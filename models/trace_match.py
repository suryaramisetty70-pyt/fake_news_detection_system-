import sys
import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_verifier import TRUSTED_DOMAINS, _get_domain, _extract_search_query

text = "According to reports from Reuters, the Federal Reserve announced a plan to adjust interest rates by a quarter of a percentage point."
query = _extract_search_query(text)
print("Extracted Query:", query)

search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(search_url, headers=headers, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')
results = soup.find_all('div', class_='result')
print("Total Results found:", len(results))

for r in results:
    title_a = r.find('a', class_='result__a')
    if title_a:
        title = title_a.get_text(strip=True)
        href = title_a.get('href', '')
        parsed_href = urlparse(href)
        query_params = parse_qs(parsed_href.query)
        url = query_params.get('uddg', [''])[0]
        if not url:
            url = href
        domain = _get_domain(url)
        
        is_trusted = any(domain == t or domain.endswith('.' + t) for t in TRUSTED_DOMAINS)
        
        # Calculate overlap
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
        query_clean = re.sub(r'[^\w\s]', '', query)
        query_words = {w.lower() for w in query_clean.split() if w.lower() not in stopwords}
        
        title_clean = re.sub(r'[^\w\s]', '', title)
        title_words = {w.lower() for w in title_clean.split() if w.lower() not in stopwords}
        
        overlap = query_words.intersection(title_words)
        ratio = len(overlap) / max(len(query_words), 1)
        
        print(f"Title: {title}")
        print(f"URL: {url} | Domain: {domain}")
        print(f"Trusted: {is_trusted} | Overlap Ratio: {ratio:.2f}")
        print("---")
