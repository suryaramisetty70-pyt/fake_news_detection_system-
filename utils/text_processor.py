"""
Text Processing Module for Fake News Detection System
Handles text cleaning, language detection, and preprocessing.
"""
import re
import string
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException


# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi', 
    'te': 'Telugu',
    'ta': 'Tamil',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'pa': 'Punjabi',
    'ur': 'Urdu',
}


def clean_text(text: str) -> str:
    """Clean and normalize text for processing.
    
    Removes URLs, HTML tags, extra whitespace, email addresses,
    and special characters while preserving meaningful content.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters but keep language-specific characters
    # (Don't strip non-ASCII for multilingual support!)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text


def detect_language(text: str) -> dict:
    """Detect the language of the given text.
    
    Returns:
        dict: {'code': 'en', 'name': 'English', 'confidence': 0.99}
    """
    if not text or len(text.strip()) < 10:
        return {'code': 'unknown', 'name': 'Unknown', 'confidence': 0.0}
    
    try:
        lang_code = detect(text)
        probabilities = detect_langs(text)
        confidence = probabilities[0].prob if probabilities else 0.0
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, f'Other ({lang_code})')
        
        return {
            'code': lang_code,
            'name': lang_name,
            'confidence': round(confidence, 2)
        }
    except LangDetectException:
        return {'code': 'unknown', 'name': 'Unknown', 'confidence': 0.0}


def get_text_stats(text: str) -> dict:
    """Get basic statistics about the text."""
    if not text:
        return {'word_count': 0, 'char_count': 0, 'sentence_count': 0}
    
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    return {
        'word_count': len(words),
        'char_count': len(text),
        'sentence_count': len(sentences),
        'avg_word_length': round(sum(len(w) for w in words) / max(len(words), 1), 1),
        'exclamation_count': text.count('!'),
        'question_count': text.count('?'),
        'caps_ratio': round(sum(1 for c in text if c.isupper()) / max(len(text), 1), 3)
    }


def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to max_length tokens (approximate by words)."""
    words = text.split()
    if len(words) <= max_length:
        return text
    return ' '.join(words[:max_length]) + '...'


def clean_forwarded_text(raw_text: str) -> str:
    """Clean WhatsApp/MMS forward junk, timestamps, name prefixes, and emojis.
    
    Normalizes ALL CAPS clickbait formatting to sentence case.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""
        
    text = raw_text.strip()
    
    # 1. Remove Forwarded tags (e.g. "Forwarded", "Forwarded many times")
    text = re.sub(r'(?i)forwarded\s*(many\s*times)?\s*:?\s*', '', text)
    text = re.sub(r'(?i)forwarded\s*message\s*:?\s*', '', text)
    
    # 2. Remove timestamps with brackets (e.g. "[10/08, 3:22 pm]")
    text = re.sub(r'\[\d{1,2}/\d{1,2}(/\d{2,4})?,\s*\d{1,2}:\d{2}(:\d{2})?(\s*[aApP][mM])?\]', '', text)
    text = re.sub(r'\[\d{1,2}:\d{2}(:\d{2})?(\s*[aApP][mM])?\]', '', text)
    
    # Remove naked dates and times (e.g. "10/08/2026, 12:45 PM" or "12:45 PM")
    text = re.sub(r'\b\d{1,2}/\d{1,2}(/\d{2,4})?\b', '', text)
    text = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?(\s*[aApP][mM])?\b', '', text)
    
    # 3. Remove sender name prefixes (e.g. "John: " or "+91 99999 99999:")
    # Handles lines starting with sender names
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r'^\s*([\w\s+]+|\+?\d[\d\s-]{5,20}):\s*', '', line)
        cleaned_lines.append(cleaned_line)
    text = '\n'.join(cleaned_lines)
    
    # Remove any leftover leading colon space
    text = re.sub(r'^\s*:\s*', '', text)
    
    # 4. Strip emojis (strip characters outside Basic Multilingual Plane)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    
    # 5. Normalize ALL CAPS text
    # If the entire text is in uppercase, capitalize it to sentence case
    if text.isupper():
        text = text.capitalize()
    else:
        # Convert individual uppercase words longer than 3 characters (e.g. BREAKING) to lowercase
        words = text.split()
        for i, w in enumerate(words):
            clean_w = re.sub(r'[^\w]', '', w)
            if len(clean_w) > 3 and clean_w.isupper():
                words[i] = w.lower()
        text = ' '.join(words)
        
    # 6. Collapse multiple line breaks and whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
