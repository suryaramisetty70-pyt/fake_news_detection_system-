"""Look up claims across topics using FactCheck.org's public article index."""
from concurrent.futures import ThreadPoolExecutor
import re
import unicodedata
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import requests


def claim_key(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.translate(str.maketrans({"“": '"', "”": '"', "’": "'"}))
    # Typographic emphasis varies between an article and a pasted claim.
    text = text.replace('"', '')
    for short, full in (("isn't", "is not"), ("aren't", "are not"), ("won't", "will not"),
                        ("doesn't", "does not"), ("can't", "cannot")):
        text = re.sub(r"\b" + short + r"\b", full, text)
    return " ".join(text.split()).rstrip(".!")


def article_reviews(url, target):
    if not re.match(r"^https://(?:www\.)?factcheck\.org/[0-9]{4}/", url):
        return []
    response = requests.get(url, timeout=(4, 10), allow_redirects=False)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.content, "html.parser")
    matches = []
    for review in soup.select('[itemtype$="/ClaimReview"]'):
        statement = review.select_one('[itemprop="claimReviewed"]')
        rating = review.select_one('[itemprop="reviewRating"] [itemprop="alternateName"]')
        if statement is None or rating is None or claim_key(statement.get_text(" ", strip=True)) != target:
            continue
        label = {"true": "REAL", "false": "FAKE"}.get(rating.get_text(strip=True).casefold())
        date = review.select_one('[itemprop="datePublished"]')
        if label:
            matches.append({
                "url": url, "domain": urlsplit(url).hostname.removeprefix("www."),
                "title": f"FactCheck.org ({date.get_text(strip=True)[:10] if date else 'archived review'}): "
                         f"{rating.get_text(strip=True)} — {statement.get_text(' ', strip=True)}",
                "stance": label,
            })
    return matches


def find_publisher_reviews(text, query):
    """Search by keywords, then compare the full statement before using its rating."""
    try:
        response = requests.get("https://www.factcheck.org/wp-json/wp/v2/search",
                                params={"search": query, "per_page": 3, "_fields": "url"},
                                timeout=(4, 10))
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError):
        return []
    if not isinstance(rows, list):
        return []
    urls = [row["url"] for row in rows[:3] if isinstance(row, dict) and isinstance(row.get("url"), str)]
    matches = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(article_reviews, url, claim_key(text)) for url in urls]
        for future in futures:
            try:
                matches.extend(future.result())
            except requests.RequestException:
                continue
    return matches
