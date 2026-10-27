"""
Linguistic, Sentiment & Dual-Emotion Analyzer
Inspired by aryashah2k (spaCy & Sentiment) and WWW/AAAI Dual-Emotion Research.
Extracts:
1. Subjectivity vs Objectivity Index
2. Sensationalism & Clickbait Index
3. Dual-Emotion Breakdown (Alarmism / Outrage vs Neutral Factuality)
4. Highlighted token-level credibility badges
"""
import re
from typing import Dict, Any, List


def analyze_linguistics(text: str) -> Dict[str, Any]:
    """Perform in-depth linguistic, emotional, and stylometric analysis on text."""
    if not text:
        return {
            "subjectivity": 0.0,
            "sensationalism": 0.0,
            "credibility_index": 50.0,
            "emotions": {"alarmism": 0.0, "objectivity": 50.0, "urgency": 0.0},
            "highlighted_tokens": []
        }
        
    words = text.split()
    total_words = max(len(words), 1)
    
    # ─── Lexicon Definitions ───
    alarm_words = {
        'shocking', 'panic', 'disaster', 'danger', 'alert', 'urgent', 'horrifying',
        'terrifying', 'collapse', 'death', 'killed', 'crisis', 'conspiracy', 'scam',
        'exposed', 'threat', 'warning', 'destroy', 'banned', 'secret', 'miracle'
    }
    
    subjective_words = {
        'terrible', 'worst', 'best', 'incredible', 'disgusting', 'heroic', 'pathetic',
        'insane', 'ridiculous', 'obviously', 'undeniably', 'unbelievable', 'stupid',
        'genius', 'evil', 'shameful', 'mastermind', 'traitor', 'corrupt'
    }
    
    objective_words = {
        'according', 'reported', 'announced', 'spokesperson', 'official', 'statement',
        'department', 'ministry', 'data', 'percent', 'study', 'confirmed', 'evidence',
        'police', 'investigation', 'published', 'reuters', 'court', 'judge'
    }
    
    clean_words = [re.sub(r'[^\w]', '', w.lower()) for w in words]
    
    alarm_hits = sum(1 for w in clean_words if w in alarm_words)
    subj_hits = sum(1 for w in clean_words if w in subjective_words)
    obj_hits = sum(1 for w in clean_words if w in objective_words)
    
    # Punctuation signals
    excl_count = text.count('!')
    q_count = text.count('?')
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
    
    # Calculations (0.0 to 100.0)
    sensationalism = min((alarm_hits * 15.0) + (excl_count * 10.0) + (caps_words * 8.0), 100.0)
    subjectivity = min((subj_hits * 20.0) + (q_count * 6.0) + (10.0 if sensationalism > 40 else 0.0), 100.0)
    objectivity = min((obj_hits * 18.0) + (40.0 if sensationalism < 20 else 10.0), 100.0)
    urgency = min((text.count('urgent') * 35.0) + (text.count('share') * 25.0) + (excl_count * 12.0), 100.0)
    
    # Credibility Index: High objectivity + low sensationalism = High Credibility
    credibility_index = max(min(objectivity * 0.7 + (100.0 - sensationalism) * 0.3, 100.0), 5.0)
    
    # Generate highlighted token-level representation
    tokens: List[Dict[str, str]] = []
    for w in words:
        clean_w = re.sub(r'[^\w]', '', w.lower())
        tag = "normal"
        if clean_w in alarm_words:
            tag = "alarm"
        elif clean_w in subjective_words:
            tag = "subjective"
        elif clean_w in objective_words:
            tag = "credible"
        elif w.isupper() and len(w) > 2:
            tag = "caps"
            
        tokens.append({"word": w, "tag": tag})
        
    return {
        "subjectivity": round(subjectivity, 1),
        "sensationalism": round(sensationalism, 1),
        "credibility_index": round(credibility_index, 1),
        "emotions": {
            "alarmism": round(sensationalism, 1),
            "objectivity": round(objectivity, 1),
            "urgency": round(urgency, 1)
        },
        "highlighted_tokens": tokens[:120]  # First 120 words for visualization
    }
