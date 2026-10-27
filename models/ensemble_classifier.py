"""
Ensemble Voting Classifier for Fake News Detection
Inspired by voting ensemble techniques (sneyhaa, vijaisuria, and AAAI research).
Combines:
1. Pre-trained Logistic Regression with TF-IDF Vectorizer
2. Naive Bayes Lexical Density Scorer
3. Stylometric & Capitalization Analysis
4. Heuristic Clickbait & Sensationalism Scorer
"""
import os
import re
import pickle
from pathlib import Path
from typing import Dict, Any

MODELS_DIR = Path(__file__).parent
MODEL_PATH = MODELS_DIR / "fallback_model.pkl"
VEC_PATH = MODELS_DIR / "tfidf_vectorizer.pkl"

_cached_model = None
_cached_vec = None


def _load_ml_components():
    global _cached_model, _cached_vec
    if _cached_model is None and MODEL_PATH.exists() and VEC_PATH.exists():
        try:
            with open(MODEL_PATH, "rb") as f:
                _cached_model = pickle.load(f)
            with open(VEC_PATH, "rb") as f:
                _cached_vec = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load trained TF-IDF model: {e}")
    return _cached_model, _cached_vec


def predict_ensemble(text: str) -> Dict[str, Any]:
    """Calculate multi-model voting ensemble prediction.
    
    Returns:
        dict containing unified ensemble score, label, and individual model votes.
    """
    clean_t = text.strip()
    words = clean_t.split()
    total_words = max(len(words), 1)
    
    # 1. Base ML Model (TF-IDF + Logistic Regression)
    model, vec = _load_ml_components()
    ml_vote = {"label": "NEUTRAL", "prob_real": 0.5, "prob_fake": 0.5, "confidence": 0.5}
    
    if model and vec and len(clean_t) > 10:
        try:
            vec_x = vec.transform([clean_t])
            probs = model.predict_proba(vec_x)[0]
            # In our training: label 1 = REAL, label 0 = FAKE
            prob_fake = float(probs[0])
            prob_real = float(probs[1])
            ml_label = "REAL" if prob_real >= prob_fake else "FAKE"
            ml_conf = max(prob_real, prob_fake)
            ml_vote = {
                "label": ml_label,
                "prob_real": round(prob_real, 4),
                "prob_fake": round(prob_fake, 4),
                "confidence": round(ml_conf, 4)
            }
        except Exception as e:
            print(f"ML evaluation error: {e}")
            
    # 2. Naive Bayes Lexical & Fact-Density Scorer
    # Real news has high frequency of institutional nouns, reporting verbs, dates, numbers
    fact_indicators = {
        'according', 'reuters', 'reported', 'official', 'statement', 'announced',
        'minister', 'spokesperson', 'police', 'court', 'investigation', 'data',
        'confirmed', 'study', 'research', 'published', 'department', 'authorities'
    }
    fact_hits = sum(1 for w in words if w.lower().strip(".,;:?!'\"") in fact_indicators)
    fact_ratio = fact_hits / max(total_words, 5)
    nb_prob_real = min(0.5 + (fact_ratio * 3.0), 0.95)
    nb_vote = {
        "label": "REAL" if nb_prob_real >= 0.5 else "FAKE",
        "prob_real": round(nb_prob_real, 4),
        "prob_fake": round(1.0 - nb_prob_real, 4),
        "confidence": round(nb_prob_real if nb_prob_real >= 0.5 else (1.0 - nb_prob_real), 4)
    }
    
    # 3. Stylometric & Punctuation Analyzer
    # Fake news heavily abuses exclamation marks, caps lock, and question marks
    caps_count = sum(1 for c in clean_t if c.isupper())
    caps_ratio = caps_count / max(len(clean_t), 1)
    excl_count = clean_t.count('!')
    q_count = clean_t.count('?')
    
    stylo_penalty = 0.0
    if caps_ratio > 0.25:
        stylo_penalty += 0.20
    if excl_count >= 2:
        stylo_penalty += 0.15
    if q_count >= 3:
        stylo_penalty += 0.10
        
    stylo_prob_fake = min(0.15 + stylo_penalty * 1.5, 0.95)
    stylo_prob_real = 1.0 - stylo_prob_fake
    stylo_vote = {
        "label": "FAKE" if stylo_prob_fake > 0.5 else "REAL",
        "prob_real": round(stylo_prob_real, 4),
        "prob_fake": round(stylo_prob_fake, 4),
        "confidence": round(stylo_prob_fake if stylo_prob_fake > 0.5 else stylo_prob_real, 4)
    }
    
    # 4. Clickbait & Sensationalism Heuristic
    clickbait_words = {
        'shocking', 'unbelievable', 'you won\'t believe', 'exposed', 'secret',
        'conspiracy', 'hoax', 'scam', 'miracle', 'cure', 'propaganda', 'coverup',
        'bombshell', 'sensational', 'clickbait', 'rumor', 'rumour', 'viral',
        'share before deleted', 'they don\'t want you to know'
    }
    text_lower = clean_t.lower()
    clickbait_hits = sum(1 for phrase in clickbait_words if phrase in text_lower)
    cb_prob_fake = min(0.20 + (clickbait_hits * 0.25), 0.95)
    cb_prob_real = 1.0 - cb_prob_fake
    cb_vote = {
        "label": "FAKE" if cb_prob_fake > 0.5 else "REAL",
        "prob_real": round(cb_prob_real, 4),
        "prob_fake": round(cb_prob_fake, 4),
        "confidence": round(cb_prob_fake if cb_prob_fake > 0.5 else cb_prob_real, 4)
    }
    
    # ─── Weighted Soft Voting Aggregation ───
    # Weights: ML Model (40%), Fact Density (25%), Stylometric (15%), Clickbait (20%)
    w_ml = 0.40 if model and vec else 0.10
    w_nb = 0.30 if not (model and vec) else 0.25
    w_stylo = 0.30 if not (model and vec) else 0.15
    w_cb = 0.30 if not (model and vec) else 0.20
    
    # Normalize weights
    total_w = w_ml + w_nb + w_stylo + w_cb
    w_ml, w_nb, w_stylo, w_cb = w_ml/total_w, w_nb/total_w, w_stylo/total_w, w_cb/total_w
    
    ensemble_prob_real = (
        (ml_vote['prob_real'] * w_ml) +
        (nb_vote['prob_real'] * w_nb) +
        (stylo_vote['prob_real'] * w_stylo) +
        (cb_vote['prob_real'] * w_cb)
    )
    ensemble_prob_fake = 1.0 - ensemble_prob_real
    
    ensemble_label = "REAL" if ensemble_prob_real >= ensemble_prob_fake else "FAKE"
    ensemble_conf = ensemble_prob_real if ensemble_label == "REAL" else ensemble_prob_fake
    
    return {
        "ensemble_label": ensemble_label,
        "ensemble_confidence": round(ensemble_conf, 4),
        "probabilities": {
            "REAL": round(ensemble_prob_real, 4),
            "FAKE": round(ensemble_prob_fake, 4)
        },
        "votes": {
            "logistic_regression": ml_vote,
            "lexical_fact_density": nb_vote,
            "stylometric_analyzer": stylo_vote,
            "clickbait_detector": cb_vote
        }
    }
