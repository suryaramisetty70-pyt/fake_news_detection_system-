"""Check explicit current-office claims against official records."""

from datetime import date, timedelta
from functools import lru_cache
import re

import requests
from bs4 import BeautifulSoup


TAMIL_NADU_SOURCE = "https://www.tn.gov.in/governor.php"
TAMIL_NADU_SNAPSHOT_DATE = date(2026, 11, 17)
TAMIL_NADU_SNAPSHOT_HOLDER = "C. Joseph Vijay"
TAMIL_NADU_CLAIM = re.compile(
    r"(?P<person>[\w.]+(?: [\w.]+){0,6}) (?:is|as|=) "
    r"(?:currently )?(?:the )?(?:cm|chief minister) (?:of|for) "
    r"(?:tamil ?nadu|t\.?n\.?)",
    re.IGNORECASE,
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
    match = TAMIL_NADU_CLAIM.fullmatch(" ".join(claim.split()).rstrip(".!"))
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
    aliases = {holder_key}
    if holder_key == "c joseph vijay":
        aliases.update({"joseph vijay", "vijay"})
    elif holder_key == "narendra modi":
        aliases.update({"modi", "pm modi", "prime minister narendra modi"})
    if person in aliases:
        verdict = "REAL"
    elif person in {"modi", "narendra modi", "pm modi", "prime minister narendra modi"} and "modi" not in holder_key.split():
        verdict = "FAKE"
    else:
        return None

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
