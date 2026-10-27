"""
Social Media Context & Viral Vector Analyzer
Inspired by Sohamcoder1 (Platform & Social Media Context Analysis).
Detects:
1. Platform Origins (WhatsApp forward, Telegram channel, Twitter/X post, Facebook chain)
2. Viral Forwarding Risk Score
3. Suspicious formatting / phone number tags
"""
import re
from typing import Dict, Any


def analyze_social_context(raw_text: str) -> Dict[str, Any]:
    """Detect platform vector and viral forwarding risk from raw text."""
    if not raw_text:
        return {
            "platform": "Unknown",
            "is_forwarded": False,
            "risk_score": 0.0,
            "viral_signals": []
        }
        
    text_lower = raw_text.lower()
    signals = []
    platform = "Web / Direct Article"
    risk = 10.0  # Base risk
    
    # 1. WhatsApp detection
    if "forwarded" in text_lower or re.search(r'\[\d{1,2}/\d{1,2}.*?\d{1,2}:\d{2}', raw_text):
        platform = "WhatsApp Forward"
        signals.append("WhatsApp forwarded header detected")
        risk += 35.0
        
    if re.search(r'^\s*(\+?\d[\d\s-]{8,15}):', raw_text, re.MULTILINE):
        platform = "WhatsApp Chat / Group"
        signals.append("Mobile sender number prefix detected")
        risk += 25.0
        
    # 2. Telegram detection
    if "t.me/" in text_lower or "@telegram" in text_lower or "join channel" in text_lower:
        platform = "Telegram Channel"
        signals.append("Telegram broadcast link or handle detected")
        risk += 25.0
        
    # 3. Twitter / X detection
    if re.search(r'@\w{2,15}\b', raw_text) or "#breaking" in text_lower or "#viral" in text_lower:
        if platform == "Web / Direct Article":
            platform = "Twitter / X Post"
        signals.append("Social media handle or viral hashtag detected")
        risk += 15.0
        
    # 4. Viral chain letter cues
    chain_cues = [
        "forward to all", "share this to 10 people", "share before it's deleted",
        "do not ignore", "pass it on", "forward to your family", "spread the word"
    ]
    for cue in chain_cues:
        if cue in text_lower:
            signals.append(f"Viral chain call-to-action: '{cue}'")
            risk += 30.0
            break
            
    is_forwarded = len(signals) > 0
    risk = min(risk, 100.0)
    
    return {
        "platform": platform,
        "is_forwarded": is_forwarded,
        "risk_score": round(risk, 1),
        "viral_signals": signals
    }
