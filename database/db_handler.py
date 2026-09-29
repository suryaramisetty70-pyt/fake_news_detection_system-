"""
SQLite Database Handler for Fake News Detection System
Uses SQLite (built into Python) — NO external setup needed.

Stores:
- Analyzed articles and their predictions
- Scraped newspaper headlines  
- User analysis history
- Statistics

Cost: ₹0 (SQLite is built into Python, no installation needed)
"""
import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


# Database file location (same directory as the project)
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "fake_news_detector.db"


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection.
    
    Creates the database file and tables if they don't exist.
    """
    # Ensure data directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA journal_mode=WAL")  # Better performance
    conn.execute("PRAGMA foreign_keys=ON")
    
    # Create tables if they don't exist
    _create_tables(conn)
    
    return conn


def _create_tables(conn: sqlite3.Connection):
    """Create all required tables."""
    conn.executescript("""
        -- Predictions table: stores all analyzed texts and results
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_hash TEXT UNIQUE NOT NULL,
            text_preview TEXT NOT NULL,
            full_text TEXT NOT NULL,
            prediction_label TEXT NOT NULL,
            confidence REAL NOT NULL,
            fake_probability REAL DEFAULT 0.0,
            real_probability REAL DEFAULT 0.0,
            model_type TEXT DEFAULT 'unknown',
            source TEXT DEFAULT 'text_input',
            language TEXT DEFAULT 'English',
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Scraped headlines table: stores newspaper scraping results
        CREATE TABLE IF NOT EXISTS scraped_headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            newspaper TEXT NOT NULL,
            language TEXT DEFAULT 'English',
            headline_title TEXT NOT NULL,
            headline_url TEXT,
            prediction_label TEXT,
            confidence REAL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for faster queries
        CREATE INDEX IF NOT EXISTS idx_predictions_hash ON predictions(text_hash);
        CREATE INDEX IF NOT EXISTS idx_predictions_label ON predictions(prediction_label);
        CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(analyzed_at);
        CREATE INDEX IF NOT EXISTS idx_headlines_newspaper ON scraped_headlines(newspaper);
    """)
    conn.commit()


def _generate_text_hash(text: str) -> str:
    """Generate a unique hash for a text to avoid duplicates."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


# ─── PREDICTION OPERATIONS ───


def save_prediction(text: str, prediction: dict, source: str = 'text_input',
                    language: str = 'English') -> bool:
    """Save a prediction result to the database.
    
    Args:
        text: The analyzed text
        prediction: Dict with 'label', 'confidence', 'probabilities'
        source: Input source ('text_input', 'voice', 'camera', 'newspaper')
        language: Detected language
    
    Returns:
        bool: True if saved successfully
    """
    try:
        conn = _get_connection()
        probabilities = prediction.get('probabilities', {})
        
        conn.execute("""
            INSERT INTO predictions 
                (text_hash, text_preview, full_text, prediction_label, confidence,
                 fake_probability, real_probability, model_type, source, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(text_hash) DO UPDATE SET
                prediction_label = excluded.prediction_label,
                confidence = excluded.confidence,
                fake_probability = excluded.fake_probability,
                real_probability = excluded.real_probability,
                model_type = excluded.model_type,
                analyzed_at = CURRENT_TIMESTAMP
        """, (
            _generate_text_hash(text),
            text[:500],  # Preview: first 500 chars
            text,
            prediction.get('label', 'UNKNOWN'),
            prediction.get('confidence', 0.0),
            probabilities.get('FAKE', 0.0),
            probabilities.get('REAL', 0.0),
            prediction.get('model_type', 'unknown'),
            source,
            language,
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving prediction: {e}")
        return False


def get_cached_prediction(text: str) -> Optional[dict]:
    """Check if we already analyzed this text before.
    
    Only reuses previously verified "REAL" predictions to avoid
    caching failed search results or stale errors.
    """
    try:
        conn = _get_connection()
        text_hash = _generate_text_hash(text)
        
        cursor = conn.execute(
            "SELECT * FROM predictions WHERE text_hash = ?", (text_hash,)
        )
        row = cursor.fetchone()
        conn.close()
        
        # Only return cached result if it was previously verified as REAL
        if row and row['prediction_label'] == 'REAL':
            return {
                'label': row['prediction_label'],
                'confidence': row['confidence'],
                'probabilities': {
                    'FAKE': row['fake_probability'],
                    'REAL': row['real_probability'],
                },
                'model_type': row['model_type'],
                'cached': True,
                'analyzed_at': row['analyzed_at'],
                'web_check': {
                    'verified': True,
                    'trusted_sources_count': 1,
                    'matches': [
                        {
                            'title': f"Previously verified story: {row['text_preview']}",
                            'url': "#",
                            'domain': "Cached Verification",
                            'snippet': "This story was previously verified and loaded from the local database cache."
                        }
                    ],
                    'confidence': row['confidence']
                }
            }
        return None
    except Exception:
        return None


# ─── HEADLINE OPERATIONS ───


def save_scraped_headlines(newspaper: str, language: str, headlines: list,
                           predictions: list = None) -> bool:
    """Save scraped headlines with optional predictions."""
    try:
        conn = _get_connection()
        
        for i, headline in enumerate(headlines):
            pred_label = None
            confidence = None
            
            if predictions and i < len(predictions):
                pred_label = predictions[i].get('label')
                confidence = predictions[i].get('confidence')
            
            conn.execute("""
                INSERT INTO scraped_headlines 
                    (newspaper, language, headline_title, headline_url,
                     prediction_label, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                newspaper,
                language,
                headline.get('title', ''),
                headline.get('url', ''),
                pred_label,
                confidence,
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving headlines: {e}")
        return False


# ─── HISTORY & STATISTICS ───


def get_analysis_history(limit: int = 50) -> list:
    """Get recent analysis history."""
    try:
        conn = _get_connection()
        cursor = conn.execute("""
            SELECT text_preview, prediction_label, confidence, 
                   source, language, model_type, analyzed_at
            FROM predictions 
            ORDER BY analyzed_at DESC 
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception:
        return []


def get_statistics() -> dict:
    """Get overall statistics from the database."""
    try:
        conn = _get_connection()
        
        total = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        fake = conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE prediction_label = 'FAKE'"
        ).fetchone()[0]
        real = conn.execute(
            "SELECT COUNT(*) FROM predictions WHERE prediction_label = 'REAL'"
        ).fetchone()[0]
        
        # Get source breakdown
        source_stats = {}
        cursor = conn.execute("""
            SELECT source, COUNT(*) as count 
            FROM predictions 
            GROUP BY source
        """)
        for row in cursor.fetchall():
            source_stats[row['source']] = row['count']
        
        # Get language breakdown
        lang_stats = {}
        cursor = conn.execute("""
            SELECT language, COUNT(*) as count 
            FROM predictions 
            GROUP BY language
        """)
        for row in cursor.fetchall():
            lang_stats[row['language']] = row['count']
        
        # Get today's count
        today_count = conn.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE DATE(analyzed_at) = DATE('now')
        """).fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'fake': fake,
            'real': real,
            'today': today_count,
            'by_source': source_stats,
            'by_language': lang_stats,
            'db_connected': True,
            'db_path': str(DB_PATH),
        }
    except Exception:
        return {
            'total': 0, 'fake': 0, 'real': 0, 'today': 0,
            'by_source': {}, 'by_language': {},
            'db_connected': False, 'db_path': str(DB_PATH),
        }


def clear_history() -> bool:
    """Clear all analysis history (for user privacy)."""
    try:
        conn = _get_connection()
        conn.execute("DELETE FROM predictions")
        conn.execute("DELETE FROM scraped_headlines")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_db_info() -> dict:
    """Get database file info."""
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0
    
    if db_size < 1024:
        size_str = f"{db_size} B"
    elif db_size < 1024 * 1024:
        size_str = f"{db_size / 1024:.1f} KB"
    else:
        size_str = f"{db_size / (1024 * 1024):.1f} MB"
    
    return {
        'exists': db_exists,
        'path': str(DB_PATH),
        'size': size_str,
        'engine': 'SQLite (built into Python)',
        'cost': '₹0 (FREE)',
    }
