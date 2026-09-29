"""
Test script to verify the news verification system and 3-state verdicts.
"""
import sys
import os

# Safe print helper to prevent UnicodeEncodeError on Windows CP1252 consoles
def print(*args, **kwargs):
    import builtins
    text = " ".join(str(arg) for arg in args)
    try:
        builtins.print(text, **kwargs)
    except UnicodeEncodeError:
        try:
            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='replace').decode(encoding)
            builtins.print(safe_text, **kwargs)
        except Exception:
            builtins.print(text.encode('ascii', errors='replace').decode('ascii'), **kwargs)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_utils import predict

# Test sample 1: Genuinely fake-sounding news / conspiracy claim
fake_sample = (
    "SHOCKING CONSPIRACY EXPOSED!!! The government is secretly using alien technology "
    "to control our minds through radio signals. Share this warning before they take it down! "
    "Unbelievable details inside!"
)

# Test sample 2: Real news headline copied WITH WhatsApp forward junk
real_sample_with_junk = (
    "[10/08, 3:22 pm] John: Forwarded many times. According to reports from Reuters, "
    "the Federal Reserve announced a plan to adjust interest rates by a quarter of a percentage point."
)

# Test sample 3: Obscure/very recent claim with no search matches
obscure_sample = (
    "An obscure local event happened at some random location where no news agency has written anything."
)

print("Testing prediction system...")

print("\n--- Test 1 (Fake Sample) ---")
result_fake = predict(fake_sample)
print(f"Original: {fake_sample[:100]}...")
print(f"Verdict: {result_fake['label']}")
print(f"Confidence: {result_fake['confidence']:.2%}")
print(f"Model Type: {result_fake['model_type']}")

print("\n--- Test 2 (Real Sample with WhatsApp Junk) ---")
result_real = predict(real_sample_with_junk)
print(f"Original: {real_sample_with_junk[:100]}...")
print(f"Verdict: {result_real['label']}")
print(f"Confidence: {result_real['confidence']:.2%}")
print(f"Model Type: {result_real['model_type']}")

print("\n--- Test 3 (Obscure Sample with No Matches) ---")
result_obscure = predict(obscure_sample)
print(f"Original: {obscure_sample[:100]}...")
print(f"Verdict: {result_obscure['label']}")
print(f"Confidence: {result_obscure['confidence']:.2%}")
print(f"Message: {result_obscure.get('message', '')}")
print(f"Model Type: {result_obscure['model_type']}")

print("\n--- Test 4 (Repeated Same-News Check) ---")
repeated_sample = "ISRO successfully launches second development flight of SSLV"

from database.db_handler import save_prediction, get_cached_prediction

# Clear cache entry for a clean test run
import sqlite3
from database.db_handler import DB_PATH, _generate_text_hash
try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM predictions WHERE text_hash = ?", (_generate_text_hash(repeated_sample),))
    conn.commit()
    conn.close()
except Exception:
    pass

print("[Test 4 - Run 1] Calling predict...")
run1 = predict(repeated_sample)
print(f"Verdict 1: {run1['label']} | Cached: {run1.get('cached', False)}")

# Save to cache database to simulate display_results behavior
save_prediction(repeated_sample, run1)

print("[Test 4 - Run 2] Checking cache...")
cached_run2 = get_cached_prediction(repeated_sample)

if cached_run2:
    print(f"Verdict 2: {cached_run2['label']} | Cached: {cached_run2.get('cached', False)}")
    verdict2 = cached_run2['label']
else:
    run2 = predict(repeated_sample)
    print(f"Verdict 2: {run2['label']} | Cached: {run2.get('cached', False)}")
    verdict2 = run2['label']

assert run1['label'] == verdict2 == "REAL", f"Verification inconsistent: Run 1={run1['label']}, Run 2={verdict2}"
print("Success: Both runs returned identical REAL verdict!")

print("\n--- Test 5 (Regional Language News - Telugu) ---")
telugu_sample = "చంద్రబాబు నాయుడు ప్రమాణ స్వీకారం"
result_telugu = predict(telugu_sample)
print(f"Original: {telugu_sample}")
print(f"Verdict: {result_telugu['label']}")
print(f"Confidence: {result_telugu['confidence']:.2%}")
print(f"Model Type: {result_telugu['model_type']}")

print("\nVerification Complete!")
