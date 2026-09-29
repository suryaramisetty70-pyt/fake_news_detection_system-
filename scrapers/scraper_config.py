"""
Newspaper Scraper Configuration
Contains URLs, CSS selectors, and metadata for supported newspapers.
"""

# Newspaper configuration
# Each entry contains: name, language, base_url, headlines_url, and CSS selectors
NEWSPAPER_SOURCES = {
    # ─── Telugu ───
    'eenadu': {
        'name': 'Eenadu',
        'language': 'Telugu',
        'base_url': 'https://www.eenadu.net',
        'headlines_url': 'https://www.eenadu.net/telugu-news',
        'headline_selector': 'h3 a, h2 a, .field-content a',
        'article_selector': '.field-item p, .article-body p, .story-content p',
        'encoding': 'utf-8',
    },
    'sakshi': {
        'name': 'Sakshi',
        'language': 'Telugu',
        'base_url': 'https://www.sakshi.com',
        'headlines_url': 'https://www.sakshi.com/telugu',
        'headline_selector': 'h2 a, h3 a, .story-title a',
        'article_selector': '.article-body p, .story-body p, .field-item p',
        'encoding': 'utf-8',
    },
    
    # ─── Tamil ───
    'dinamalar': {
        'name': 'Dinamalar',
        'language': 'Tamil',
        'base_url': 'https://www.dinamalar.com',
        'headlines_url': 'https://www.dinamalar.com/news',
        'headline_selector': 'h2 a, h3 a, .news-title a',
        'article_selector': '.article-content p, .news-content p',
        'encoding': 'utf-8',
    },
    'dinathanthi': {
        'name': 'Dinathanthi',
        'language': 'Tamil',
        'base_url': 'https://www.dailythanthi.com',
        'headlines_url': 'https://www.dailythanthi.com/news',
        'headline_selector': 'h2 a, h3 a, .article-title a',
        'article_selector': '.article-body p, .story-element p',
        'encoding': 'utf-8',
    },
    
    # ─── Hindi ───
    'dainik_jagran': {
        'name': 'Dainik Jagran',
        'language': 'Hindi',
        'base_url': 'https://www.jagran.com',
        'headlines_url': 'https://www.jagran.com/news/national-news-hindi.html',
        'headline_selector': 'h3 a, h2 a, .ListingSide a',
        'article_selector': '.articleBody p, .story-content p',
        'encoding': 'utf-8',
    },
    'amar_ujala': {
        'name': 'Amar Ujala',
        'language': 'Hindi',
        'base_url': 'https://www.amarujala.com',
        'headlines_url': 'https://www.amarujala.com/india-news',
        'headline_selector': 'h2 a, h3 a, .article-title a',
        'article_selector': '.article-content p, .story-content p',
        'encoding': 'utf-8',
    },
    
    # ─── English ───
    'the_hindu': {
        'name': 'The Hindu',
        'language': 'English',
        'base_url': 'https://www.thehindu.com',
        'headlines_url': 'https://www.thehindu.com/news/',
        'headline_selector': 'h3 a, h2 a, .story-card-heading a',
        'article_selector': '.article-body p, .articlebodycontent p',
        'encoding': 'utf-8',
    },
    'ndtv': {
        'name': 'NDTV',
        'language': 'English',
        'base_url': 'https://www.ndtv.com',
        'headlines_url': 'https://www.ndtv.com/latest',
        'headline_selector': 'h2 a, h3 a, .newsHdng a',
        'article_selector': '.article-body p, .story__content p, .content_text p',
        'encoding': 'utf-8',
    },
    'times_of_india': {
        'name': 'Times of India',
        'language': 'English',
        'base_url': 'https://timesofindia.indiatimes.com',
        'headlines_url': 'https://timesofindia.indiatimes.com/india',
        'headline_selector': 'h2 a, h3 a, .w_tle a, span a',
        'article_selector': '.article-body p, ._s30J p, .ga-headlines p',
        'encoding': 'utf-8',
    },
    'indian_express': {
        'name': 'Indian Express',
        'language': 'English',
        'base_url': 'https://indianexpress.com',
        'headlines_url': 'https://indianexpress.com/section/india/',
        'headline_selector': 'h2 a, h3 a, .title a',
        'article_selector': '.article-body p, .full-details p',
        'encoding': 'utf-8',
    },
}

# Group newspapers by language for easy filtering
LANGUAGE_GROUPS = {}
for key, config in NEWSPAPER_SOURCES.items():
    lang = config['language']
    if lang not in LANGUAGE_GROUPS:
        LANGUAGE_GROUPS[lang] = []
    LANGUAGE_GROUPS[lang].append(key)


def get_newspapers_by_language(language: str = None) -> dict:
    """Get newspaper configurations filtered by language."""
    if language:
        keys = LANGUAGE_GROUPS.get(language, [])
        return {k: NEWSPAPER_SOURCES[k] for k in keys}
    return NEWSPAPER_SOURCES


def get_available_languages() -> list:
    """Get list of available newspaper languages."""
    return list(LANGUAGE_GROUPS.keys())


def get_newspaper_names() -> dict:
    """Get mapping of newspaper keys to display names."""
    return {k: v['name'] for k, v in NEWSPAPER_SOURCES.items()}
