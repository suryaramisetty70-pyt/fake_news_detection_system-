"""Find an exact statement in the cited 2020 CLIMATE-FEVER research archive."""
from functools import lru_cache
import json
from pathlib import Path

SOURCE = "https://github.com/tdiggelm/climate-fever-dataset/blob/03de61617b10a5c1935f8e08bb0e8ac1ee775356/dataset/climate-fever.jsonl"


def key(text):
    return " ".join(text.casefold().split()).rstrip(". ")


@lru_cache(maxsize=1)
def records():
    index = {}
    path = Path(__file__).resolve().parents[1] / "data/climate_review_index.jsonl"
    with path.open(encoding="utf-8") as rows:
        for row in rows:
            claim, rating, line = json.loads(row)
            index.setdefault(key(claim), []).append((rating, line))
    return index


def archived_review(text):
    matches = records().get(key(text), [])
    if not matches:
        return None
    ratings = {rating for rating, _ in matches}
    rating = next(iter(ratings)) if len(ratings) == 1 else "DISPUTED"
    description = {"SUPPORTS": "supported", "REFUTES": "refuted",
                   "DISPUTED": "disputed", "NOT_ENOUGH_INFO": "insufficient evidence"}[rating]
    label = {"SUPPORTS": "ARCHIVE SUPPORTED", "REFUTES": "ARCHIVE REFUTED"}.get(rating)
    return {
        "verdict": label, "verified": False, "confidence": 0.0, "method": "climate_fever_2020",
        "message": f"The 2020 CLIMATE-FEVER dataset rated this exact statement: {description}. This is a historical review.",
        "total_results_count": len(matches), "trusted_sources_count": 0, "search_failed": False,
        "matches": [{"domain": "github.com", "url": f"{SOURCE}#L{line}",
                     "title": f"CLIMATE-FEVER (2020), original claim and evidence, line {line}",
                     "stance": "ARCHIVED"} for _, line in matches],
    }
