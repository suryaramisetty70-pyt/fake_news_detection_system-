import sys
import os
import re
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.search_verifier import verify_claim_on_web, _extract_search_query

text = "According to reports from Reuters, the Federal Reserve announced a plan to adjust interest rates by a quarter of a percentage point."

print("Original Text:", text)
query = _extract_search_query(text)
print("Extracted Query:", query)

res = verify_claim_on_web(text)
print("\nVerification Results:")
print("Verified:", res.get('verified'))
print("Trusted Sources Count:", res.get('trusted_sources_count'))
print("Matches:")
for m in res.get('matches', []):
    print(f"- Title: {m['title']}")
    print(f"  URL: {m['url']}")
    print(f"  Domain: {m['domain']}")
