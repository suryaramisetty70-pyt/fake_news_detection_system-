"""
Model Utilities for Fake News Detection System
Handles loading the ML model, making predictions, and managing model state.

Supports two modes:
1. Transformer mode (DistilBERT) — high accuracy, needs model files
2. Fallback mode (TF-IDF + Logistic Regression) — lightweight, built-in
"""
import os
import re
import pickle
import numpy as np
from pathlib import Path


# ─── Global model cache ───
_model_cache = {}


def _get_model_dir() -> Path:
    """Get the models directory path."""
    return Path(__file__).parent


def load_transformer_model():
    """Load fine-tuned Multilingual DistilBERT model.
    
    Requires the model to be fine-tuned and saved in models/saved_model/
    Use the Google Colab training notebook to create this.
    """
    if 'transformer' in _model_cache:
        return _model_cache['transformer']
    
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
            pipeline
        )
        
        model_path = _get_model_dir() / 'saved_model'
        
        # Only load if the fine-tuned model directory actually exists
        if model_path.exists() and (model_path / 'config.json').exists():
            tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
            
            classifier = pipeline(
                'text-classification',
                model=model,
                tokenizer=tokenizer,
                return_all_scores=True,
                truncation=True,
                max_length=512
            )
            
            _model_cache['transformer'] = {
                'classifier': classifier,
                'tokenizer': tokenizer,
                'model': model,
                'type': 'transformer'
            }
            return _model_cache['transformer']
        else:
            # Do not load un-finetuned base model from HF Hub (will output random weights)
            return None
            
    except Exception as e:
        print(f'Could not load transformer model: {e}')
        return None


def load_fallback_model():
    """Load TF-IDF + Logistic Regression fallback model.
    
    This is a lightweight model that works without GPU.
    It's automatically trained on first use if no saved model exists.
    """
    if 'fallback' in _model_cache:
        return _model_cache['fallback']
    
    model_path = _get_model_dir() / 'fallback_model.pkl'
    vectorizer_path = _get_model_dir() / 'tfidf_vectorizer.pkl'
    
    if model_path.exists() and vectorizer_path.exists():
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        
        _model_cache['fallback'] = {
            'model': model,
            'vectorizer': vectorizer,
            'type': 'fallback'
        }
        return _model_cache['fallback']
    
    return None


def predict(text: str, use_transformer: bool = True) -> dict:
    """Make a news verification prediction based on real-time Google News RSS search.
    
    Bypasses AI model classification to avoid false positives and leverages
    trusted news domain cross-referencing.
    
    Args:
        text: The news text to verify
        use_transformer: Unused (kept for API compatibility)
    
    Returns:
        dict: {
            'label': 'REAL', 'FAKE', or 'UNABLE TO VERIFY',
            'confidence': float,
            'probabilities': {'FAKE': float, 'REAL': float},
            'model_type': 'search_verification'
        }
    """
    from utils.text_processor import clean_forwarded_text, detect_language
    
    # 1. Clean WhatsApp/MMS forward junk before running prediction
    cleaned_text = clean_forwarded_text(text)
    
    if not cleaned_text or len(cleaned_text.strip()) < 8:
        return {
            'label': 'UNKNOWN',
            'confidence': 0.0,
            'probabilities': {'FAKE': 0.0, 'REAL': 0.0},
            'model_type': 'none',
            'error': 'Text is too short for analysis. Please provide more content.'
        }
        
    # Detect language of the text to pass to verifier
    lang_info = detect_language(cleaned_text)
    lang_code = lang_info.get('code', 'en')
    
    from utils.search_verifier import verify_claim_on_web
    web_check = verify_claim_on_web(cleaned_text, lang_code=lang_code)
    
    # 2. Check if search failed or returned zero results (UNABLE TO VERIFY state)
    if web_check.get('search_failed') or web_check.get('total_results_count', 0) == 0:
        label = 'UNABLE TO VERIFY'
        confidence = 0.0
        message = "We couldn't find matching sources. This doesn't confirm the news is fake — try rephrasing or check manually."
        return {
            'label': label,
            'confidence': confidence,
            'message': message,
            'probabilities': {'FAKE': 0.0, 'REAL': 0.0},
            'model_type': 'search_verification',
            'web_check': web_check
        }
    
    # 3. Search returned results, evaluate verification
    if web_check.get('verified'):
        # Check if any matches are on fact-checking domains (debunked)
        fact_checkers = {
            'pib.gov.in', 'factcheck.pib.gov.in', 'altnews.in', 
            'boomlive.in', 'factcrescendo.com', 'vishvasnews.com'
        }
        
        has_fact_check_debunk = False
        fact_check_match = None
        
        for match in web_check.get('matches', []):
            domain = match.get('domain', '')
            if domain in fact_checkers or any(domain.endswith('.' + fc) for fc in fact_checkers):
                has_fact_check_debunk = True
                fact_check_match = match
                break
                
        if has_fact_check_debunk:
            label = 'FAKE'
            confidence = 0.85
            message = f"This claim was officially flagged as false/fake by fact-checking agency: {fact_check_match['domain']}"
            return {
                'label': label,
                'confidence': confidence,
                'message': message,
                'probabilities': {'FAKE': 0.85, 'REAL': 0.15},
                'model_type': 'search_verification',
                'web_check': web_check
            }
        else:
            label = 'REAL'
            confidence = web_check.get('confidence', 0.85)
            return {
                'label': label,
                'confidence': confidence,
                'probabilities': {
                    'FAKE': round(1.0 - confidence, 4),
                    'REAL': round(confidence, 4)
                },
                'model_type': 'search_verification',
                'web_check': web_check
            }
    else:
        # Search returned results, but no matches on trusted domains.
        # Verdict must be UNABLE TO VERIFY (never default to FAKE unless contradicted by fact-checking sites)
        label = 'UNABLE TO VERIFY'
        confidence = 0.0
        message = "We couldn't find matching sources. This doesn't confirm the news is fake — try rephrasing or check manually."
        return {
            'label': label,
            'confidence': confidence,
            'message': message,
            'probabilities': {'FAKE': 0.0, 'REAL': 0.0},
            'model_type': 'search_verification',
            'web_check': web_check
        }


def _heuristic_predict(text: str) -> dict:
    """Simple heuristic-based fake news detection.
    
    Used as ultimate fallback when no trained model is available.
    Checks for common fake news indicators:
    - Excessive capitalization
    - Excessive punctuation (!!!, ???)
    - Clickbait phrases
    - Extreme sentiment words
    """
    score = 0.30  # Start neutral/conservative
    
    # Check for excessive caps (e.g. SHOCKING)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.3:
        score += 0.15
    
    # Check for excessive exclamation marks
    exclamation_count = text.count('!')
    if exclamation_count > 3:
        score += 0.15
    
    # Check for clickbait phrases (excluding standard words like breaking / urgent)
    clickbait_phrases = [
        'you won\'t believe', 'shocking', 'share before', 'forward this', 
        'must read', 'unbelievable', 'exposed', 'secret', 
        'they don\'t want you to know', 'mainstream media won\'t tell', 
        'wake up', 'open your eyes'
    ]
    text_lower = text.lower()
    clickbait_count = sum(1 for phrase in clickbait_phrases if phrase in text_lower)
    score += clickbait_count * 0.12
    
    # Check for ALL CAPS words
    words = text.split()
    all_caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
    if all_caps_words > 3:
        score += 0.15
    
    # Cap the score
    score = min(score, 0.95)
    
    if score > 0.55:
        label = 'FAKE'
        confidence = score
    else:
        label = 'REAL'
        confidence = 1 - score
    
    return {
        'label': label,
        'confidence': round(confidence, 4),
        'probabilities': {
            'FAKE': round(score, 4),
            'REAL': round(1 - score, 4),
        },
        'model_type': 'heuristic',
        'note': 'Using heuristic analysis. For better accuracy, train the ML model using the provided Colab notebook.'
    }


def predict_batch(texts: list, use_transformer: bool = True) -> list:
    """Make predictions on multiple texts."""
    return [predict(text, use_transformer) for text in texts]
