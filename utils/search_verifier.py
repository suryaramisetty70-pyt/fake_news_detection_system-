"""
Search Verifier Module for Fake News Detection System (All-India Edition)
Queries DuckDuckGo/Google Search to verify news claims against 50+ trusted
local, state-level, and national Indian news sources in all major languages.

Cost: ₹0 (FREE, no API keys needed)
"""
import re
import sys
from urllib.parse import urlparse
from ddgs import DDGS

# Safe print helper to prevent UnicodeEncodeError on Windows CP1252 consoles
def print(*args, **kwargs):
    import builtins
    text = " ".join(str(arg) for arg in args)
    try:
        builtins.print(text, **kwargs)
    except UnicodeEncodeError:
        try:
            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            builtins.print(safe_text, **kwargs)
        except Exception:
            builtins.print(text.encode('ascii', errors='replace').decode('ascii'), **kwargs)

# Trusted news sources domains spanning all Indian states and languages
TRUSTED_DOMAINS = {
    # ─── Government & Official Fact Checkers (Highest Priority) ───
    'pib.gov.in', 'factcheck.pib.gov.in', 'gov.in', 'nic.in', 'altnews.in', 
    'boomlive.in', 'factcrescendo.com', 'vishvasnews.com',
    
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
    'livehindustan.com', 'navbharattimes.indiatimes.com', 'patrika.com'
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
    
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'to', 'of', 'in', 'on', 'for', 'with', 'at', 'by', 'from', 'about',
        'as', 'into', 'like', 'through', 'after', 'over', 'between', 'out',
        'against', 'during', 'without', 'before', 'under', 'around', 'among',
        'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them', 'he',
        'him', 'she', 'her', 'we', 'us', 'you', 'your', 'my', 'our', 'what',
        'who', 'whom', 'which', 'how', 'why', 'where', 'when', 'according',
        'reports', 'report', 'breaking', 'exclusive', 'news'
    }
    
    words = text.split()
    key_words = [w for w in words if w.lower() not in stopwords]
    
    # Take first 6 key words
    query_words = key_words[:6] if len(key_words) >= 6 else key_words
    
    # Fallback to first 6 words of original text if no keywords remain
    if not query_words:
        query_words = words[:6]
        
    print(f"[Verifier Log] Extracted 6 keywords for search: {query_words}")
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


# Configurable keyword overlap threshold (default 35%)
OVERLAP_THRESHOLD = 0.35


def verify_claim_on_web(text: str, lang_code: str = 'en') -> dict:
    """Search Google News RSS feed to check if trusted news domains are reporting the same story.
    
    Includes 2-retry logic on fetch timeouts and a configurable title keyword overlap check.
    
    Returns:
        dict: {
            'verified': True/False,
            'trusted_sources_count': int,
            'total_results_count': int,
            'search_failed': True/False,
            'matches': list of dicts [{'title', 'url', 'domain'}],
            'confidence': float (0.0 to 1.0)
        }
    """
    import requests
    import xml.etree.ElementTree as ET
    from urllib.parse import urlparse
    
    query = _extract_search_query(text)
    if not query or len(query.strip()) < 5:
        return {
            'verified': False,
            'trusted_sources_count': 0,
            'total_results_count': 0,
            'search_failed': False,
            'matches': [],
            'confidence': 0.0,
            'error': 'Text is too short to construct a valid search query.'
        }
    
    matches = []
    seen_domains = set()
    total_results_count = 0
    
    # Map detected language code to regional Google News RSS parameters
    lang_map = {
        'hi': ('hi', 'IN:hi'),     # Hindi
        'te': ('te', 'IN:te'),     # Telugu
        'ta': ('ta', 'IN:ta'),     # Tamil
        'ml': ('ml', 'IN:ml'),     # Malayalam
        'kn': ('kn', 'IN:kn'),     # Kannada
        'mr': ('mr', 'IN:mr'),     # Marathi
        'bn': ('bn', 'IN:bn'),     # Bengali
        'gu': ('gu', 'IN:gu'),     # Gujarati
        'pa': ('pa', 'IN:pa'),     # Punjabi
        'ur': ('ur', 'IN:ur'),     # Urdu
    }
    hl, ceid = lang_map.get(lang_code, ('en-IN', 'IN:en'))
    
    # Google News RSS search URL
    import urllib.parse
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl=IN&ceid={ceid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    import time
    
    # Base delay of 1.5s to prevent IP rate-limiting from Google News RSS
    time.sleep(1.5)
    
    # Log the query and destination URL
    print(f"\n[Verifier Log] Exact query sent to Google News RSS: '{query}'")
    print(f"[Verifier Log] Target Search URL: {search_url}")
    
    response = None
    retries = 3  # Retry up to 3 times (4 total attempts)
    backoff_delays = [1.0, 3.0, 5.0]
    
    for attempt in range(retries + 1):
        if attempt > 0:
            delay = backoff_delays[attempt - 1]
            print(f"[Verifier Log] Attempt {attempt + 1} - Sleeping {delay}s for backoff...")
            time.sleep(delay)
            
        try:
            response = requests.get(search_url, headers=headers, timeout=5)
            print(f"[Verifier Log] HTTP Status Code received: {response.status_code}")
            response.raise_for_status()
            break
        except Exception as e:
            status_code = response.status_code if response is not None else "None/Timeout"
            print(f"[Verifier Log] Fetch attempt {attempt + 1} failed (Status: {status_code}). Error: {e}")
            if attempt == retries:
                print(f"[Verifier Log] ALL retries failed. Returning UNABLE TO VERIFY state.")
                return {
                    'verified': False,
                    'trusted_sources_count': 0,
                    'total_results_count': 0,
                    'search_failed': True,
                    'matches': [],
                    'confidence': 0.0,
                    'error': f'Failed to query Google News RSS after {retries+1} attempts: {str(e)}'
                }
                
    try:
        # Check for empty response content
        if not response or not response.content:
            print("[Verifier Log] Empty XML response returned by Google News RSS.")
            return {
                'verified': False,
                'trusted_sources_count': 0,
                'total_results_count': 0,
                'search_failed': True,
                'matches': [],
                'confidence': 0.0,
                'error': 'Empty XML response received.'
            }
            
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        total_results_count = len(items)
        print(f"[Verifier Log] Number of Google News RSS results parsed: {total_results_count}")
        
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            
            source_elem = item.find('source')
            source_url = ""
            if source_elem is not None:
                source_url = source_elem.attrib.get('url', '')
                
            if not source_url:
                source_url = link
                
            domain = _get_domain(source_url)
            
            # Check if domain is trusted
            is_trusted = False
            for trusted in TRUSTED_DOMAINS:
                if domain == trusted or domain.endswith('.' + trusted):
                    is_trusted = True
                    break
            
            # Calculate title keyword overlap
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                'to', 'of', 'in', 'on', 'for', 'with', 'at', 'by', 'from', 'about',
                'as', 'into', 'like', 'through', 'after', 'over', 'between', 'out',
                'against', 'during', 'without', 'before', 'under', 'around', 'among',
                'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them', 'he',
                'him', 'she', 'her', 'we', 'us', 'you', 'your', 'my', 'our', 'what',
                'who', 'whom', 'which', 'how', 'why', 'where', 'when', 'according',
                'reports', 'report', 'breaking', 'exclusive', 'news'
            }
            
            query_clean = _clean_punctuation(query)
            query_words = {w.lower() for w in query_clean.split() if w.lower() not in stopwords}
            query_stems = {_stem_word(w) for w in query_words}
            
            # Google News titles usually append the source name at the end (e.g., "- Reuters")
            # Strip this to calculate overlap purely on the headline text
            title_clean = title
            if " - " in title:
                title_clean = title.rsplit(" - ", 1)[0]
                
            title_clean = _clean_punctuation(title_clean)
            title_words = {w.lower() for w in title_clean.split() if w.lower() not in stopwords}
            title_stems = {_stem_word(w) for w in title_words}
            
            overlap = query_stems.intersection(title_stems)
            overlap_ratio = len(overlap) / max(len(query_stems), 1)
            
            # Log matching details for tuning (side-by-side comparison)
            print(f"[Verifier Log] Title: '{title}' | Domain: {domain}")
            print(f"               Query Keywords (Stemmed): {list(query_stems)}")
            print(f"               Article Keywords (Stemmed): {list(title_stems)}")
            print(f"               Matched Stems: {list(overlap)} | Overlap Ratio: {overlap_ratio:.1%} | Trusted: {is_trusted}")
            
            # Only accept match if domain is trusted AND keyword overlap is at least OVERLAP_THRESHOLD
            if is_trusted and overlap_ratio >= OVERLAP_THRESHOLD and domain not in seen_domains:
                seen_domains.add(domain)
                matches.append({
                    'title': title,
                    'url': source_url,
                    'domain': domain,
                    'snippet': f"Reported by {domain}. Article title: '{title}'"
                })
                
    except Exception as e:
        print(f"Error parsing Google News RSS XML: {e}")
        return {
            'verified': False,
            'trusted_sources_count': 0,
            'total_results_count': 0,
            'search_failed': True,
            'matches': [],
            'confidence': 0.0,
            'error': f'XML parsing failure: {str(e)}'
        }
        
    sources_count = len(matches)
    if sources_count >= 2:
        verified = True
        confidence = 0.99
    elif sources_count == 1:
        verified = True
        confidence = 0.85
    else:
        verified = False
        confidence = 0.0
        
    return {
        'verified': verified,
        'trusted_sources_count': sources_count,
        'total_results_count': total_results_count,
        'search_failed': False,
        'matches': matches,
        'confidence': confidence
    }
