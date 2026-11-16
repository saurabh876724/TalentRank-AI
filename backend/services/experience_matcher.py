"""Experience matching against explicit JD requirements.

Missing-data policy (documented, never silent zeros):
- JD specifies no experience requirement -> component unavailable (score
  None); the scoring engine redistributes its weight.
- JD requires experience but the candidate's experience is unknown ->
  neutral score of 50 with an explicit explanation. Unknown is NOT zero.
- Employment duration is never inferred from graduation years.

Scoring when both values are known:
- Meets preferred (or required when no preferred): 100.
- Meets required but not preferred: 80-100, linear toward preferred.
- Below required: partial credit 80 * (candidate / required), floor 0.
"""

NEUTRAL_UNKNOWN_SCORE = 50.0


def match_experience(
    candidate_years: float | None,
    required_years: float | None,
    preferred_years: float | None = None,
) -> dict:
    result = {
        "candidate_experience": candidate_years,
        "required_experience": required_years,
        "preferred_experience": preferred_years,
        "experience_score": None,
        "experience_gap": None,
        "explanation": "",
    }

    if required_years is None and preferred_years is None:
        result["explanation"] = "JD specifies no experience requirement; component excluded from scoring."
        return result

    if candidate_years is None:
        result["experience_score"] = NEUTRAL_UNKNOWN_SCORE
        result["explanation"] = (
            "Candidate experience could not be determined from the resume; "
            f"neutral score of {NEUTRAL_UNKNOWN_SCORE:.0f} applied (unknown is not treated as zero)."
        )
        return result

    target = required_years if required_years is not None else preferred_years
    result["experience_gap"] = round(max(0.0, target - candidate_years), 1)

    if required_years is None:
        # Only a preferred target exists: soft, proportional scoring.
        score = min(100.0, 100.0 * candidate_years / preferred_years) if preferred_years else 100.0
        result["experience_score"] = round(score, 1)
        result["explanation"] = (
            f"Candidate has {candidate_years} years; JD prefers {preferred_years} years "
            f"(no hard minimum). Score {result['experience_score']}."
        )
        return result

    if candidate_years >= required_years:
        if preferred_years is not None and candidate_years < preferred_years:
            span = preferred_years - required_years
            progress = (candidate_years - required_years) / span if span > 0 else 1.0
            score = 80.0 + 20.0 * progress
            result["explanation"] = (
                f"Meets the required {required_years} years with {candidate_years} years, "
                f"but below the preferred {preferred_years} years."
            )
        else:
            score = 100.0
            result["explanation"] = (
                f"Candidate has {candidate_years} years, meeting the required {required_years} years."
            )
    else:
        score = max(0.0, 80.0 * candidate_years / required_years) if required_years > 0 else 100.0
        result["explanation"] = (
            f"Candidate has {candidate_years} years, below the required {required_years} years "
            f"(gap of {result['experience_gap']} years); partial credit applied."
        )

    result["experience_score"] = round(score, 1)
    return result