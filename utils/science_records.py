"""Compare complete, present-tense solar-system claims with NASA's reference."""
import re

SOURCE = "https://science.nasa.gov/solar-system/planets/"
PLANETS = ("mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune")
DWARFS = {"ceres", "pluto", "haumea", "makemake", "eris"}
ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth")


def check_planet_fact(text):
    claim = " ".join(text.casefold().split()).rstrip(".!")
    classification = re.fullmatch(r"(\w+) is (not )?a (dwarf planet|planet)(?: in (?:our|the) solar system)?", claim)
    position = re.fullmatch(r"(\w+) is (not )?the (\w+) planet from the sun", claim)
    if classification:
        body, negation, category = classification.groups()
        if body not in PLANETS and body not in DWARFS:
            return None
        actual = "planet" if body in PLANETS else "dwarf planet"
        supported = category == actual
        explanation = f"NASA classifies {body.title()} as a {actual}."
    elif position:
        body, negation, ordinal = position.groups()
        if body not in PLANETS or ordinal not in ORDINALS:
            return None
        actual = ORDINALS[PLANETS.index(body)]
        supported = ordinal == actual
        explanation = f"NASA lists {body.title()} as the {actual} planet from the Sun."
    else:
        return None
    verdict = "REAL" if supported != bool(negation) else "FAKE"
    return {
        "verified": verdict == "REAL", "verdict": verdict, "method": "official_record",
        "total_results_count": 1, "trusted_sources_count": 1, "search_failed": False,
        "confidence": 0.0, "message": explanation,
        "matches": [{"url": SOURCE, "domain": "science.nasa.gov", "title": explanation, "stance": verdict}],
    }
