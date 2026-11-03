import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models.model_utils import predict

human_test_cases = [
    {
        "category": "😂 Funny & Absurd Rumors",
        "claim": "Aliens landed in Bangalore and got stuck in Silk Board traffic for 5 hours",
    },
    {
        "category": "😂 Funny & Absurd Rumors",
        "claim": "NASA confirms the moon is made entirely of green cheese",
    },
    {
        "category": "📱 WhatsApp Miracle Medical Scam",
        "claim": "Drinking hot lemon water with baking soda cures all stages of cancer in 24 hours forward to everyone",
    },
    {
        "category": "📱 Viral Free Recharge Scam",
        "claim": "Government announced 5000 rupees free recharge scheme for all Jio and Airtel mobile users click here to claim",
    },
    {
        "category": "🇮🇳 Classic Indian WhatsApp Hoax",
        "claim": "UNESCO declares Indian National Anthem Jana Gana Mana as the best national anthem in the world",
    },
    {
        "category": "💸 Classic Currency Hoax",
        "claim": "RBI confirms 2000 rupee notes have radioactive nano GPS chips to track black money from satellites",
    },
    {
        "category": "🏛️ Political Identity Claim (False)",
        "claim": "pm modi is the cm of tn",
    },
    {
        "category": "🏛️ Political Identity Claim (False - Reverse)",
        "claim": "ap cm is rahul gandhi",
    },
    {
        "category": "🏛️ Political Fact (True)",
        "claim": "MK Stalin is the Chief Minister of Tamil Nadu",
    },
    {
        "category": "🚀 Real Space Science News",
        "claim": "ISRO successfully launched Chandrayaan 3 lunar mission to the moon",
    },
    {
        "category": "🏏 Real Sports Breaking News",
        "claim": "India won the ICC Men's T20 World Cup 2024",
    },
    {
        "category": "❓ Random Personal Gossip",
        "claim": "My neighbor Ramesh bought an invisible flying motorcycle yesterday",
    }
]

print("=" * 80)
print("🧑‍🔬 HUMAN-STYLE REAL WORLD VERIFICATION TEST SUITE")
print("=" * 80)

for idx, tc in enumerate(human_test_cases, 1):
    claim = tc["claim"]
    cat = tc["category"]
    print(f"\n[{idx}/12] Category: {cat}")
    print(f"👉 Input News: \"{claim}\"")
    
    res = predict(claim)
    label = res.get('label')
    conf = round(res.get('confidence', 0.0) * 100)
    model_type = res.get('model_type')
    message = res.get('message', '')
    sources_cnt = res.get('web_check', {}).get('trusted_sources_count', 0)
    ensemble_lbl = res.get('ensemble', {}).get('ensemble_label', 'N/A')
    alarmism = res.get('linguistics', {}).get('emotions', {}).get('alarmism', 0)
    
    status_icon = "✅" if label == "REAL" else ("❌" if label == "FAKE" else "⚠️")
    print(f"   Verdict: {status_icon} {label} ({conf}% Confidence) [Engine: {model_type}]")
    if message:
        print(f"   Reason / Message: {message}")
    if sources_cnt > 0:
        print(f"   Trusted Sources Found: {sources_cnt}")
    print(f"   Ensemble Vote: {ensemble_lbl} | Alarmism Meter: {alarmism}%")
