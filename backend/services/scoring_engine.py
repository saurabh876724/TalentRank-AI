"""Weighted final scoring with transparent missing-data handling.

Base weights: semantic 40%, skills 30%, experience 20%, education 10%.

Missing-data policy: a component whose score is None is genuinely
unavailable (e.g. the JD states no education requirement, or the resume
text was not stored). Its weight is redistributed proportionally across
the available components, and the breakdown reports both base and
effective weights. Unknown values are never silently treated as zero.
"""

BASE_WEIGHTS: dict[str, float] = {
    "semantic": 0.40,
    "skills": 0.30,
    "experience": 0.20,
    "education": 0.10,
}

_COMPONENT_LABELS = {
    "semantic": "Semantic Similarity",
    "skills": "Skills Matching",
    "experience": "Experience Matching",
    "education": "Education Matching",
}


def compute_final_score(components: dict[str, float | None]) -> dict:
    available = {k: v for k, v in components.items() if v is not None and k in BASE_WEIGHTS}
    total_available_weight = sum(BASE_WEIGHTS[k] for k in available)

    breakdown: dict[str, dict] = {}
    for name, base_weight in BASE_WEIGHTS.items():
        score = components.get(name)
        is_available = name in available and total_available_weight > 0
        breakdown[name] = {
            "score": score,
            "base_weight": base_weight,
            "effective_weight": round(base_weight / total_available_weight, 4) if is_available else 0.0,
            "available": is_available,
        }

    if not available or total_available_weight == 0:
        return {
            "final_score": 0.0,
            "breakdown": breakdown,
            "note": "No scorable information available; final score is 0.",
        }

    final = sum(available[k] * breakdown[k]["effective_weight"] for k in available)
    return {"final_score": round(final, 1), "breakdown": breakdown, "note": None}


def build_explanation(
    candidate_name: str | None,
    scoring: dict,
    skills_result: dict,
    experience_result: dict,
    education_result: dict,
) -> list[str]:
    lines: list[str] = []
    name = candidate_name or "Unknown candidate"
    lines.append(f"{name}: Final Score {scoring['final_score']}%")

    breakdown = scoring["breakdown"]
    positives: list[str] = []
    semantic = breakdown["semantic"]["score"]
    if semantic is not None:
        if semantic >= 70:
            positives.append(f"Strong semantic similarity with the JD ({semantic}).")
        elif semantic >= 45:
            positives.append(f"Moderate semantic similarity with the JD ({semantic}).")
    if skills_result["matched_skills"]:
        positives.append("Matches " + ", ".join(skills_result["matched_skills"]) + ".")
    if experience_result["experience_score"] == 100.0:
        positives.append("Meets the required experience.")
    if education_result["education_score"] == 100.0:
        positives.append("Meets the education requirement.")

    if positives:
        lines.append("Positive factors:")
        lines.extend(f"- {p}" for p in positives)

    missing: list[str] = []
    if skills_result["missing_skills"]:
        missing.append("Missing required skills: " + ", ".join(skills_result["missing_skills"]) + ".")
    gap = experience_result["experience_gap"]
    if gap:
        missing.append(f"Experience gap of {gap} years against the JD minimum.")
    if education_result["education_score"] not in (None, 100.0):
        missing.append(education_result["explanation"])
    if missing:
        lines.append("Missing requirements:")
        lines.extend(f"- {m}" for m in missing)

    for key in ("experience", "education"):
        score = breakdown[key]["score"]
        if score == 50.0:
            lines.append(f"Note: {_COMPONENT_LABELS[key]} information unavailable; neutral 50 applied.")
    redistributed = [
        _COMPONENT_LABELS[k] for k, v in breakdown.items() if not v["available"]
    ]
    if redistributed:
        lines.append("Note: " + ", ".join(redistributed) + " not applicable; weights redistributed.")

    lines.append("Score breakdown:")
    for key, label in _COMPONENT_LABELS.items():
        entry = breakdown[key]
        score_text = str(entry["score"]) if entry["score"] is not None else "n/a (weight redistributed)"
        lines.append(f"- {label}: {score_text}")
    return lines