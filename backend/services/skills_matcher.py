"""Weighted skills matching between JD requirements and candidate skills.

Required skills carry weight 2, preferred skills weight 1:
    Skills Score = (matched weighted skills / total weighted JD skills) * 100

Missing-data policy: if the JD lists no skills at all, the component is
unavailable (score None) and the scoring engine redistributes its weight.
A candidate with zero skills against a JD that requires skills scores 0 —
that is a known empty set, not missing information.
"""
from services.candidate_extractor import SKILL_ALIASES

REQUIRED_WEIGHT = 2.0
PREFERRED_WEIGHT = 1.0

# Controlled normalization dictionary: alias -> canonical name.
# Only genuinely equivalent names are mapped; unrelated skills never alias.
NORMALIZATION_MAP: dict[str, str] = {}
for _canonical, _aliases in SKILL_ALIASES.items():
    NORMALIZATION_MAP[_canonical.lower()] = _canonical
    for _alias in _aliases:
        NORMALIZATION_MAP[_alias.lower()] = _canonical
NORMALIZATION_MAP.update(
    {
        "machine-learning": "Machine Learning",
        "deep-learning": "Deep Learning",
        "natural language processing": "NLP",
        "rest apis": "REST API",
        "restful api": "REST API",
        "node": "Node.js",
        "js": "JavaScript",
        "ml": "Machine Learning",
        "scikit learn": "Scikit-learn",
        "amazon web services": "AWS",
    }
)


def normalize_skill(name: str) -> str | None:
    return NORMALIZATION_MAP.get(name.strip().lower())


def _normalize_set(skills: list[str]) -> set[str]:
    normalized = set()
    for skill in skills:
        canonical = normalize_skill(skill)
        if canonical:
            normalized.add(canonical)
    return normalized


def match_skills(
    required_skills: list[str],
    preferred_skills: list[str],
    candidate_skills: list[str],
) -> dict:
    required = _normalize_set(required_skills)
    preferred = _normalize_set(preferred_skills) - required
    candidate = _normalize_set(candidate_skills)

    matched_required = sorted(required & candidate)
    missing_required = sorted(required - candidate)
    matched_preferred = sorted(preferred & candidate)

    total_weight = REQUIRED_WEIGHT * len(required) + PREFERRED_WEIGHT * len(preferred)
    if total_weight == 0:
        score = None
    else:
        matched_weight = REQUIRED_WEIGHT * len(matched_required) + PREFERRED_WEIGHT * len(matched_preferred)
        score = round(matched_weight / total_weight * 100, 1)

    return {
        "matched_skills": matched_required + matched_preferred,
        "matched_required_skills": matched_required,
        "missing_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "skills_score": score,
    }