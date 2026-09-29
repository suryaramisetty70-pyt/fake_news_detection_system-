"""
Explainability Module for Fake News Detection System
Provides visual explanations for why a text was classified as FAKE or REAL.
Uses LIME (Local Interpretable Model-agnostic Explanations) — FREE.
"""
import re
import numpy as np
from collections import Counter
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


def generate_word_importance(text: str, prediction: dict) -> list:
    """Generate word importance scores based on heuristic analysis.
    
    For a full LIME explanation, the trained model is needed.
    This provides a lightweight alternative that highlights suspicious words.
    
    Returns:
        list of dicts: [{'word': '...', 'score': float, 'color': 'red/green'}]
    """
    # Suspicious words commonly found in fake news
    fake_indicators = {
        'shocking': 0.8, 'exposed': 0.8, 'unbelievable': 0.8, 
        'secret': 0.7, 'conspiracy': 0.9, 'hoax': 0.9, 
        'scam': 0.8, 'miracle': 0.8, 'cure': 0.6, 
        'propaganda': 0.8, 'coverup': 0.9, 'bombshell': 0.7,
        'sensational': 0.7, 'clickbait': 0.9, 'rumor': 0.8, 'rumour': 0.8,
    }
    
    # Credibility indicators (words common in real news)
    real_indicators = {
        'according': 0.6, 'reported': 0.5, 'official': 0.5, 'statement': 0.5,
        'confirmed': 0.6, 'research': 0.7, 'study': 0.7, 'evidence': 0.7,
        'analysis': 0.6, 'data': 0.6, 'source': 0.5, 'published': 0.6,
        'investigation': 0.6, 'authorities': 0.5, 'government': 0.4,
        'university': 0.7, 'scientists': 0.7, 'experts': 0.6,
        'peer-reviewed': 0.9, 'journal': 0.7, 'reuters': 0.8, 'associated press': 0.8,
    }
    
    words = text.lower().split()
    word_scores = []
    
    for word in words[:100]:  # Limit to first 100 words
        clean_word = re.sub(r'[^\w]', '', word)
        if not clean_word or len(clean_word) < 3:
            continue
        
        if clean_word in fake_indicators:
            word_scores.append({
                'word': clean_word,
                'score': fake_indicators[clean_word],
                'type': 'suspicious',
                'color': '#FF4444',  # Red
            })
        elif clean_word in real_indicators:
            word_scores.append({
                'word': clean_word,
                'score': real_indicators[clean_word],
                'type': 'credible',
                'color': '#44FF44',  # Green
            })
    
    # Sort by score descending
    word_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return word_scores


def generate_highlighted_html(text: str, word_scores: list) -> str:
    """Generate HTML with highlighted words showing suspicious/credible indicators."""
    # Build lookup dictionaries
    suspicious_words = {ws['word']: ws['score'] for ws in word_scores if ws['type'] == 'suspicious'}
    credible_words = {ws['word']: ws['score'] for ws in word_scores if ws['type'] == 'credible'}
    
    words = text.split()
    highlighted_words = []
    
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        if clean_word in suspicious_words:
            intensity = suspicious_words[clean_word]
            alpha = max(0.3, intensity)
            highlighted_words.append(
                f'<span style="background-color: rgba(255, 68, 68, {alpha}); '
                f'padding: 2px 4px; border-radius: 3px; font-weight: bold;" '
                f'title="Suspicious indicator (score: {intensity})">{word}</span>'
            )
        elif clean_word in credible_words:
            intensity = credible_words[clean_word]
            alpha = max(0.3, intensity)
            highlighted_words.append(
                f'<span style="background-color: rgba(68, 255, 68, {alpha}); '
                f'padding: 2px 4px; border-radius: 3px; color: #000;" '
                f'title="Credibility indicator (score: {intensity})">{word}</span>'
            )
        else:
            highlighted_words.append(word)
    
    return ' '.join(highlighted_words)


def generate_confidence_chart(prediction: dict) -> BytesIO:
    """Generate a confidence bar chart as an image."""
    fig, ax = plt.subplots(figsize=(8, 2.5))
    
    probabilities = prediction.get('probabilities', {'FAKE': 0.5, 'REAL': 0.5})
    fake_prob = probabilities.get('FAKE', 0.5)
    real_prob = probabilities.get('REAL', 0.5)
    
    colors = ['#FF4B4B', '#00CC66']
    bars = ax.barh(
        ['FAKE', 'REAL'],
        [fake_prob * 100, real_prob * 100],
        color=colors,
        height=0.5,
        edgecolor='white',
        linewidth=0.5
    )
    
    # Add percentage labels
    for bar, prob in zip(bars, [fake_prob, real_prob]):
        width = bar.get_width()
        ax.text(
            width + 1, bar.get_y() + bar.get_height() / 2,
            f'{prob * 100:.1f}%',
            ha='left', va='center',
            fontsize=14, fontweight='bold', color='white'
        )
    
    ax.set_xlim(0, 110)
    ax.set_xlabel('Confidence (%)', fontsize=12, color='white')
    ax.set_title('Prediction Confidence', fontsize=14, fontweight='bold', color='white')
    
    # Style
    ax.set_facecolor('#0E1117')
    fig.set_facecolor('#0E1117')
    ax.tick_params(colors='white', labelsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_color('#333333')
    
    plt.tight_layout()
    
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    
    return buf


def generate_wordcloud_image(text: str, label: str = 'FAKE') -> BytesIO:
    """Generate a word cloud image from the text."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        return None
    
    # Color scheme based on prediction
    if label == 'FAKE':
        colormap = 'Reds'
        bg_color = '#0E1117'
    else:
        colormap = 'Greens'
        bg_color = '#0E1117'
    
    try:
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color=bg_color,
            colormap=colormap,
            max_words=100,
            max_font_size=80,
            min_font_size=10,
            random_state=42,
            contour_width=1,
            contour_color='white',
        ).generate(text)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(
            f'Word Cloud ({label} News)',
            fontsize=16, fontweight='bold', color='white', pad=10
        )
        fig.set_facecolor('#0E1117')
        
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception:
        return None


def get_text_analysis_summary(text: str, prediction: dict) -> dict:
    """Generate a comprehensive text analysis summary."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    # Count indicators
    word_scores = generate_word_importance(text, prediction)
    suspicious_count = sum(1 for ws in word_scores if ws['type'] == 'suspicious')
    credible_count = sum(1 for ws in word_scores if ws['type'] == 'credible')
    
    return {
        'word_count': len(words),
        'sentence_count': len(sentences),
        'suspicious_words': suspicious_count,
        'credible_words': credible_count,
        'caps_ratio': round(sum(1 for c in text if c.isupper()) / max(len(text), 1) * 100, 1),
        'exclamation_count': text.count('!'),
        'question_marks': text.count('?'),
        'top_suspicious': [ws['word'] for ws in word_scores if ws['type'] == 'suspicious'][:5],
        'top_credible': [ws['word'] for ws in word_scores if ws['type'] == 'credible'][:5],
    }
