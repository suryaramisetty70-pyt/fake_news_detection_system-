"""
Text Processing Module for Fake News Detection System
Handles text cleaning, language detection, and preprocessing.
"""
import re
import string
from langdetect import DetectorFactory, detect_langs

DetectorFactory.seed = 0
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
        probabilities = detect_langs(text)
        lang_code = probabilities[0].lang
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
    """Remove only explicit, leading message metadata and preserve the claim."""
    if not isinstance(raw_text, str):
        return ""
    text = re.sub(
        r"^\s*\[\d{1,2}/\d{1,2}(?:/\d{2,4})?,\s*\d{1,2}:\d{2}(?:\s*[ap]m)?\]\s*",
        "", raw_text, count=1, flags=re.I,
    )
    text = re.sub(r"^\s*forwarded(?: many times| message)?(?:\s*:\s*|\s+)", "", text, count=1, flags=re.I)
    return " ".join(text.split())
