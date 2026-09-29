"""
Newspaper Scraper Module for Fake News Detection System
Scrapes headlines and articles from Indian newspapers (FREE).
Uses BeautifulSoup + requests (both open-source).
"""
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scrapers.scraper_config import NEWSPAPER_SOURCES, get_newspapers_by_language


# Realistic browser headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5,hi;q=0.3,te;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}


def scrape_headlines(newspaper_key: str, max_headlines: int = 15) -> dict:
    """Scrape latest headlines from a newspaper.
    
    Args:
        newspaper_key: Key from NEWSPAPER_SOURCES (e.g., 'eenadu', 'ndtv')
        max_headlines: Maximum number of headlines to fetch
    
    Returns:
        dict: {'success': True/False, 'headlines': [...], 'error': '...'}
    """
    if newspaper_key not in NEWSPAPER_SOURCES:
        return {
            'success': False,
            'newspaper': newspaper_key,
            'headlines': [],
            'error': f'Unknown newspaper: {newspaper_key}'
        }
    
    config = NEWSPAPER_SOURCES[newspaper_key]
    
    try:
        # Add a small random delay to be respectful
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(
            config['headlines_url'],
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        response.encoding = config.get('encoding', 'utf-8')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find headlines using configured selectors
        headlines = []
        seen_titles = set()
        
        for selector in config['headline_selector'].split(', '):
            elements = soup.select(selector)
            for elem in elements:
                title = elem.get_text(strip=True)
                href = elem.get('href', '')
                
                # Skip empty, too short, or duplicate titles
                if not title or len(title) < 10 or title in seen_titles:
                    continue
                
                # Build full URL if relative
                if href and not href.startswith('http'):
                    href = urljoin(config['base_url'], href)
                
                seen_titles.add(title)
                headlines.append({
                    'title': title,
                    'url': href,
                    'newspaper': config['name'],
                    'language': config['language'],
                })
                
                if len(headlines) >= max_headlines:
                    break
            
            if len(headlines) >= max_headlines:
                break
        
        return {
            'success': True,
            'newspaper': config['name'],
            'language': config['language'],
            'headlines': headlines,
            'count': len(headlines),
            'error': None
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'newspaper': config['name'],
            'headlines': [],
            'error': f'Timeout: {config["name"]} took too long to respond.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'newspaper': config['name'],
            'headlines': [],
            'error': f'Error fetching {config["name"]}: {str(e)}'
        }


def scrape_article(url: str) -> dict:
    """Scrape full article text from a URL.
    
    Args:
        url: Full URL of the news article
    
    Returns:
        dict: {'success': True/False, 'text': '...', 'title': '...', 'error': '...'}
    """
    try:
        time.sleep(random.uniform(0.5, 1.0))
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get the title
        title = ''
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract article body paragraphs
        paragraphs = []
        
        # Try common article body selectors
        body_selectors = [
            '.article-body p', '.story-content p', '.article-content p',
            '.field-item p', '.content_text p', '.full-details p',
            'article p', '.post-content p', '.entry-content p',
        ]
        
        for selector in body_selectors:
            elements = soup.select(selector)
            if elements:
                paragraphs = [p.get_text(strip=True) for p in elements if p.get_text(strip=True)]
                break
        
        # Fallback: get all paragraphs from the page
        if not paragraphs:
            all_p = soup.find_all('p')
            paragraphs = [p.get_text(strip=True) for p in all_p 
                         if p.get_text(strip=True) and len(p.get_text(strip=True)) > 30]
        
        article_text = '\n\n'.join(paragraphs)
        
        if not article_text:
            return {
                'success': False,
                'title': title,
                'text': '',
                'error': 'Could not extract article text from this URL.'
            }
        
        return {
            'success': True,
            'title': title,
            'text': article_text,
            'url': url,
            'error': None
        }
    
    except Exception as e:
        return {
            'success': False,
            'title': '',
            'text': '',
            'error': f'Error scraping article: {str(e)}'
        }


def scrape_multiple_newspapers(language: str = None, max_per_paper: int = 10) -> list:
    """Scrape headlines from multiple newspapers.
    
    Args:
        language: Filter by language (None = all)
        max_per_paper: Max headlines per newspaper
    
    Returns:
        list: Combined list of all headlines
    """
    newspapers = get_newspapers_by_language(language)
    all_headlines = []
    
    for key in newspapers:
        result = scrape_headlines(key, max_headlines=max_per_paper)
        if result['success']:
            all_headlines.extend(result['headlines'])
    
    return all_headlines
