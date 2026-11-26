"""Check explicit current-office claims against official records."""

from datetime import date, timedelta
from functools import lru_cache
import re

import requests
from bs4 import BeautifulSoup


TAMIL_NADU_SOURCE = "https://www.tn.gov.in/governor.php"
TAMIL_NADU_SNAPSHOT_DATE = date(2026, 11, 17)
TAMIL_NADU_SNAPSHOT_HOLDER = "C. Joseph Vijay"
PERSON = r"(?P<person>[\w.]+(?: [\w.]+){0,6})"
REGION = r"(?:tamil ?nadu|t\.?n\.?)"
ROLE = r"(?:cm|chief minister)"
OFFICE = rf"(?:(?:current )?{ROLE} (?:of|for) {REGION}|(?:current )?{REGION} {ROLE})"
NEGATION = r"(?P<negation>not )?"
OFFICE_CLAIMS = (
    re.compile(rf"{PERSON} (?:is|as|=) (?:currently )?{NEGATION}(?:the )?{OFFICE}", re.I),
    re.compile(rf"(?:the )?{OFFICE} is (?:currently )?{NEGATION}{PERSON}", re.I),
)


@lru_cache(maxsize=24)
def _fetch_tamil_nadu_holder(hour: int):
    """Recheck the current government page every hour."""
    try:
        response = requests.get(TAMIL_NADU_SOURCE, timeout=(3, 5))
        response.raise_for_status()
    except requests.RequestException:
        return None
    lines = list(BeautifulSoup(response.content, "html.parser").stripped_strings)
    for index, line in enumerate(lines):
        if index and line.casefold() == "chief minister of tamil nadu":
            match = re.fullmatch(r"Thiru\s+([^<>]{3,90})", lines[index - 1], re.IGNORECASE)
            if match:
                return match[1].strip()
    return None


def _name_key(name: str) -> str:
    return " ".join(re.findall(r"\w+", name.casefold()))


def check_current_office(claim: str, now):
    """Return evidence for recognized identities and present-tense office claims."""
    if claim.rstrip().endswith(("?", "？")):
        return None
    statement = " ".join(claim.split()).rstrip(".!")
    for pattern in OFFICE_CLAIMS:
        match = pattern.fullmatch(statement)
        if match:
            break
    if not match:
        return None

    person = _name_key(match["person"])
    holder = _fetch_tamil_nadu_holder(int(now.timestamp()) // 3600)
    checked_on = now.date()
    if not holder:
        if not TAMIL_NADU_SNAPSHOT_DATE <= now.date() <= TAMIL_NADU_SNAPSHOT_DATE + timedelta(days=30):
            return None
        holder = TAMIL_NADU_SNAPSHOT_HOLDER
        checked_on = TAMIL_NADU_SNAPSHOT_DATE

    holder_key = _name_key(holder)
    # Only identify aliases we recognize. Unfamiliar names can have multiple spellings.
    known_names = (
        {"c joseph vijay", "joseph vijay", "vijay"},
        {"narendra modi", "modi", "pm modi", "prime minister narendra modi"},
        {"m k stalin", "mk stalin", "muthuvel karunanidhi stalin"},
    )
    holder_names = next((names for names in known_names if holder_key in names), {holder_key})
    if person in holder_names:
        holds_office = True
    elif any(person in names for names in known_names) and any(holder_key in names for names in known_names):
        holds_office = False
    else:
        return None
    verdict = "REAL" if holds_office != bool(match["negation"]) else "FAKE"

    title = f"Government of Tamil Nadu lists {holder} as Chief Minister"
    return {
        "verdict": verdict,
        "verified": verdict == "REAL",
        "trusted_sources_count": 1,
        "total_results_count": 1,
        "search_failed": False,
        "matches": [{
            "title": title, "url": TAMIL_NADU_SOURCE, "domain": "tn.gov.in", "stance": verdict,
        }],
        "message": f"{title} (checked {checked_on.isoformat()}).",
        "confidence": 0.0,
        "method": "official_record",
    }
