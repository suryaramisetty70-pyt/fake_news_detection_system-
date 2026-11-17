"""
Search Verifier Module for Fake News Detection System (All-India Edition)
Queries DuckDuckGo/Google Search to verify news claims against 50+ trusted
local, state-level, and national Indian news sources in all major languages.

Cost: ₹0 (FREE, no API keys needed)
"""
import re
from urllib.parse import urlparse

# Trusted news sources domains spanning all Indian states and languages
TRUSTED_DOMAINS = {
    # ─── Government & Official Fact Checkers (Highest Priority) ───
    'pib.gov.in', 'factcheck.pib.gov.in', 'gov.in', 'nic.in', 'altnews.in', 
    'boomlive.in', 'factcrescendo.com', 'vishvasnews.com', 'factcheck.org',
    'factly.in', 'snopes.com', 'politifact.com', 'fullfact.org', 'thip.media',
    
    # ─── National Outlets (English & Hindi) ───
    'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk', 'nytimes.com', 
    'washingtonpost.com', 'bloomberg.com', 'cnn.com', 'theguardian.com',
    'msn.com', 'ndtv.com', 'thehindu.com', 'timesofindia.indiatimes.com', 
    'indianexpress.com', 'hindustantimes.com', 'news18.com', 'indiatoday.in', 
    'livemint.com', 'moneycontrol.com', 'firstpost.com', 'oneindia.com',
    
    # ─── Andhra Pradesh & Telangana (Telugu) ───
    'eenadu.net', 'sakshi.com', 'andhrabhoomi.net', 'andhrajyothy.com',
    'namasthetelangaana.com', 'telugu.samayam.com', 'telugu.oneindia.com',
    
    # ─── Tamil Nadu (Tamil) ───
    'dailythanthi.com', 'dinamalar.com', 'dinakaran.com', 'vikatan.com', 
    'tamil.thehindu.com', 'tamil.samayam.com', 'puthiyathalaimurai.com',
    
    # ─── Karnataka (Kannada) ───
    'prajavani.net', 'kannadaprabha.com', 'vijaykarnataka.com', 'udayavani.com',
    'kannada.oneindia.com', 'suvarnanews.com',
    
    # ─── Kerala (Malayalam) ───
    'mathrubhumi.com', 'manoramaonline.com', 'deshabhimani.com', 
    'asianetnews.com', 'malayalam.samayam.com',
    
    # ─── Maharashtra (Marathi) ───
    'lokmat.com', 'esakal.com', 'maharashtratimes.com', 'loksatta.com',
    'marathi.abplive.com',
    
    # ─── Gujarat (Gujarati) ───
    'divyabhaskar.co.in', 'sandesh.com', 'gujaratsamachar.com', 'gujarati.abplive.com',
    
    # ─── West Bengal & Northeast (Bengali / Assamese) ───
    'anandabazar.com', 'bartamanpatrika.com', 'sangbadpratidin.in', 
    'assamtribune.com', 'asomiyapratidin.in', 'bengali.abplive.com',
    
    # ─── Odisha (Odia) ───
    'dharitri.com', 'sambad.in', 'samaja.epapr.in', 'otvkhabar.in',
    
    # ─── Punjab (Punjabi) ───
    'jagbani.punjabkesari.in', 'ajitjalandhar.com', 'babushahi.com',
    
    # ─── North India (Hindi - UP, Bihar, MP, Rajasthan, Haryana, etc.) ───
    'jagran.com', 'amarujala.com', 'bhaskar.com', 'jansatta.com', 
    'livehindustan.com', 'navbharattimes.indiatimes.com', 'patrika.com',
    
    # ─── Entertainment, Cinema & Sports (National & Regional) ───
    'gulte.com', '123telugu.com', 'greatandhra.com', 'mirchi9.com',
    'pinkvilla.com', 'bollywoodhungama.com', 'cinemaexpress.com',
    'filmibeat.com', 'ottplay.com', 'espncricinfo.com', 'cricbuzz.com'
}

# Global Stopwords for search queries and title overlap
GLOBAL_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
    'to', 'of', 'in', 'on', 'for', 'with', 'at', 'by', 'from', 'about',
    'as', 'into', 'like', 'through', 'after', 'over', 'between', 'out',
    'against', 'during', 'without', 'before', 'under', 'around', 'among',
    'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them', 'he',
    'him', 'she', 'her', 'we', 'us', 'you', 'your', 'my', 'our', 'what',
    'who', 'whom', 'which', 'how', 'why', 'where', 'when', 'according',
    'reports', 'report', 'breaking', 'exclusive', 'news', 'can', 'could',
    'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'do',
    'does', 'did', 'have', 'has', 'had', 'having', 'been', 'being',
    'ago', 'days', 'day', 'hours', 'hour', 'mins', 'minutes', 'yesterday',
    'today', 'tomorrow', 'headline', 'read', 'click', 'share', 'view',
    'watch', 'update', 'updates'
}


def _clean_punctuation(text: str) -> str:
    """Strip common punctuation but keep all Unicode letters, numbers, spaces, and combining marks (like Telugu/Hindi diacritics)."""
    return re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?"\'’‘“”\[\]]', '', text)


def _stem_word(word: str) -> str:
    """Perform simple, lightweight English suffix stripping to improve keyword matching.
    
    Leaves non-English characters untouched.
    """
    word = word.lower()
    if not word.isascii() or not word.isalpha():
        return word
    suffixes = ('tional', 'tion', 'ment', 'ing', 'ed', 'es', 'ly', 'al', 's', 'y')
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                word = word[:-len(suffix)]
                changed = True
                break
    return word


def _extract_search_query(text: str) -> str:
    """Extract a clean, concise search query from the text.
    
    Filters out stop words and takes the first 6 high-information words
    to optimize search matching and prevent query over-specification.
    """
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove special characters but keep Unicode letters, combining marks and spaces
    text = _clean_punctuation(text)
    
    words = text.split()
    key_words = [w for w in words if w.lower() not in GLOBAL_STOPWORDS]
    
    # Take first 6 key words
    query_words = key_words[:6] if len(key_words) >= 6 else key_words
    
    # Fallback to first 6 words of original text if no keywords remain
    if not query_words:
        query_words = words[:6]
        
    return ' '.join(query_words)


def _get_domain(url: str) -> str:
    """Extract domain name from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


FACT_CHECK_DOMAINS = {
    "pib.gov.in", "altnews.in", "boomlive.in", "factcrescendo.com",
    "vishvasnews.com", "factcheck.org", "factly.in", "snopes.com",
    "politifact.com", "fullfact.org", "thip.media",
}


def _matches_domain(domain: str, domains: set) -> bool:
    return any(domain == source or domain.endswith("." + source) for source in domains)


def _normalize_claim(text: str) -> str:
    # Keep negations, dates, decimal points and word order when comparing claims.
    import unicodedata
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split()).rstrip(".!?।")


def _source_stance(claim: str, title: str, domain: str) -> str:
    if _matches_domain(domain, FACT_CHECK_DOMAINS):
        checks = re.fullmatch(
            r'(?:fact[ -]check:\s*)?["“](.+)["”]\s*[:–—-]\s*'
            r'(false|fake|true)[.!]?',
            title.strip(),
            flags=re.IGNORECASE,
        )
        if checks and _normalize_claim(checks[1]) == claim:
            return "REAL" if checks[2].lower() == "true" else "FAKE"
        return "RELATED"
    if _normalize_claim(title) == claim and not title.rstrip().endswith(("?", "？")):
        return "REAL"
    return "RELATED"


def verify_claim_on_web(text: str, lang_code: str = "en") -> dict:
    """Retrieve related headlines and classify only directly matching evidence."""
    from datetime import datetime, timezone
    from xml.etree import ElementTree as ET

    from utils.official_records import check_current_office

    import requests

    result = {
        "verified": False, "verdict": None, "trusted_sources_count": 0,
        "total_results_count": 0, "search_failed": False, "matches": [],
        "confidence": 0.0,
    }
    if re.search(r"\b(?:my|your|his|her|our|their)\s+(?:own\s+)?(?:home|house|residence)\b", text, re.IGNORECASE):
        return {
            **result,
            "message": "A private-home claim needs a specific person, place, date and a public source. The details provided are insufficient.",
        }
    office = check_current_office(text, now=datetime.now(timezone.utc))
    if office:
        return office

    query = _extract_search_query(text)
    if len(query.strip()) < 5:
        return result

    regional = {"hi", "te", "ta", "ml", "kn", "mr", "bn", "gu", "pa", "ur"}
    language = lang_code if lang_code in regional else "en"
    params = {
        "q": query, "hl": language if language != "en" else "en-IN",
        "gl": "IN", "ceid": f"IN:{language}",
    }
    try:
        response = requests.get(
            "https://news.google.com/rss/search", params=params, timeout=(3, 6),
        )
        response.raise_for_status()
        items = ET.fromstring(response.content).findall("./channel/item")
    except (requests.RequestException, ET.ParseError):
        result["search_failed"] = True
        return result

    claim = _normalize_claim(text)
    claim_is_question = text.rstrip().endswith(("?", "？"))
    query_stems = {_stem_word(word) for word in query.split()}
    matches = {}
    result["total_results_count"] = len(items)
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source = item.find("source")
        domain = _get_domain(source.get("url", "") if source is not None else "")
        if not title or not link.startswith(("https://", "http://")):
            continue
        if not _matches_domain(domain, TRUSTED_DOMAINS):
            continue

        suffix = f" - {(source.text or '').strip()}"
        headline = title.removesuffix(suffix).strip()
        stance = "RELATED" if claim_is_question else _source_stance(claim, headline, domain)
        title_stems = {_stem_word(word) for word in _clean_punctuation(headline).split()}
        if stance == "RELATED" and len(query_stems & title_stems) / len(query_stems) < 0.35:
            continue
        matches.setdefault((domain, stance), {
            "title": title, "url": link, "domain": domain, "stance": stance,
        })

    direct = [match for match in matches.values() if match["stance"] != "RELATED"]
    stances = {match["stance"] for match in direct}
    verdict = next(iter(stances)) if len(stances) == 1 else None
    result.update(
        verified=verdict == "REAL",
        verdict=verdict,
        trusted_sources_count=len({match["domain"] for match in direct}) if verdict else 0,
        matches=(direct + [match for match in matches.values() if match["stance"] == "RELATED"])[:8],
        confidence=0.0,
    )
    return result
