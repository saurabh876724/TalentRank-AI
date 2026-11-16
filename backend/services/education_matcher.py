"""Education matching against explicit JD degree requirements.

Only degree level is compared — never college reputation or personal
attributes.

Missing-data policy:
- JD specifies no education requirement -> component unavailable (score
  None); no artificial penalty, weight is redistributed.
- JD requires a degree but candidate education is unknown -> neutral 50
  with an explicit explanation (unknown is not zero).
- Known candidate below the required level -> proportional partial credit.
"""
import re

NEUTRAL_UNKNOWN_SCORE = 50.0

_LEVEL_PATTERNS: list[tuple[int, re.Pattern]] = [
    (4, re.compile(r"\bph\.?d\b|\bdoctorate\b", re.IGNORECASE)),
    (3, re.compile(r"\bm\.?tech\b|\bm\.?e\.?\b|\bm\.?sc\b|\bm\.?c\.?a\b|\bm\.?b\.?a\b|\bmaster", re.IGNORECASE)),
    (2, re.compile(r"\bb\.?tech\b|\bb\.?e\.?\b|\bb\.?sc\b|\bb\.?c\.?a\b|\bb\.?com\b|\bbachelor", re.IGNORECASE)),
    (1, re.compile(r"\bdiploma\b|\bhigher secondary\b|\bclass\s+(?:x|xii|10|12)\b", re.IGNORECASE)),
]


def degree_level(degree: str) -> int:
    for level, pattern in _LEVEL_PATTERNS:
        if pattern.search(degree):
            return level
    return 0


def match_education(candidate_education: list[dict], required_degrees: list[str]) -> dict:
    result = {
        "candidate_education": candidate_education,
        "required_education": required_degrees,
        "education_score": None,
        "explanation": "",
    }

    if not required_degrees:
        result["explanation"] = "JD specifies no education requirement; component excluded from scoring."
        return result

    required_levels = [degree_level(d) for d in required_degrees]
    required_level = min(required_levels) if required_levels else 0
    if required_level == 0:
        result["explanation"] = "JD education requirement could not be classified; component excluded."
        return result

    candidate_degrees = [e.get("degree", "") for e in candidate_education if e.get("degree")]
    if not candidate_degrees:
        result["education_score"] = NEUTRAL_UNKNOWN_SCORE
        result["explanation"] = (
            "Candidate education could not be determined from the resume; "
            f"neutral score of {NEUTRAL_UNKNOWN_SCORE:.0f} applied (unknown is not treated as zero)."
        )
        return result

    candidate_level = max(degree_level(d) for d in candidate_degrees)
    required_name = required_degrees[required_levels.index(required_level)]

    if candidate_level >= required_level:
        result["education_score"] = 100.0
        result["explanation"] = (
            f"Candidate education ({', '.join(candidate_degrees)}) meets the required {required_name} level."
        )
    else:
        result["education_score"] = round(100.0 * candidate_level / required_level, 1)
        result["explanation"] = (
            f"Candidate education ({', '.join(candidate_degrees)}) is below the required "
            f"{required_name} level; proportional partial credit applied."
        )
    return result