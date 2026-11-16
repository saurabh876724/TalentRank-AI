"""Deterministic candidate ranking by final matching score.

Ordering uses only job-relevant scores. Ties on the final score are broken
by skills score, then semantic score, then candidate id (insertion order)
so results are stable and reproducible. Equal final scores share the same
rank (competition ranking: 1, 2, 2, 4). Names, age, gender and other
protected attributes are never used.
"""


def rank_candidates(results: list[dict]) -> list[dict]:
    ordered = sorted(
        results,
        key=lambda r: (
            -(r["final_score"] if r["final_score"] is not None else -1.0),
            -(r["skills_score"] if r["skills_score"] is not None else -1.0),
            -(r["semantic_score"] if r["semantic_score"] is not None else -1.0),
            r["candidate_id"],
        ),
    )
    ranked: list[dict] = []
    previous_score: float | None = None
    previous_rank = 0
    for position, result in enumerate(ordered, start=1):
        score = result["final_score"]
        if previous_score is not None and score == previous_score:
            rank = previous_rank
        else:
            rank = position
        ranked.append({"rank": rank, **result})
        previous_score = score
        previous_rank = rank
    return ranked