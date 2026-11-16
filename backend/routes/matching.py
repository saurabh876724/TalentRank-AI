"""Candidate-to-JD matching endpoint (Day 2 AI/NLP engine)."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from models import Candidate, MatchResult
from services.education_matcher import match_education
from services.embedding_service import ModelLoadError
from services.experience_matcher import match_experience
from services.jd_analyzer import extract_jd_requirements
from services.ranking_engine import rank_candidates
from services.scoring_engine import build_explanation, compute_final_score
from services.semantic_matcher import semantic_scores_batch
from services.skills_matcher import match_skills

router = APIRouter(prefix="/api/matching", tags=["Matching"])


class MatchingRequest(BaseModel):
    job_description: str = Field(..., min_length=1)
    candidate_ids: list[int] = Field(..., min_length=1)


@router.post("/analyze")
def analyze_matching(payload: MatchingRequest, db: Session = Depends(get_db)) -> dict:
    jd_text = payload.job_description.strip()
    if not jd_text:
        raise HTTPException(status_code=422, detail="Job description must not be empty.")

    unique_ids = list(dict.fromkeys(payload.candidate_ids))
    # Single query for all requested candidates.
    candidates = db.query(Candidate).filter(Candidate.id.in_(unique_ids)).all()
    found_ids = {c.id for c in candidates}
    not_found_ids = [i for i in unique_ids if i not in found_ids]
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=f"No candidates found for ids {not_found_ids}. Upload resumes first.",
        )

    jd_requirements = extract_jd_requirements(jd_text)

    # Semantic scores: one batched embedding call; resumes without stored
    # text get None (component unavailable, weight redistributed).
    with_text = [c for c in candidates if c.resume_text]
    try:
        batch_scores = semantic_scores_batch(jd_text, [c.resume_text for c in with_text])
    except ModelLoadError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    semantic_by_id = {c.id: score for c, score in zip(with_text, batch_scores)}

    results: list[dict] = []
    for candidate in candidates:
        skills_result = match_skills(
            jd_requirements["required_skills"],
            jd_requirements["preferred_skills"],
            candidate.skills or [],
        )
        experience_result = match_experience(
            candidate.experience_years,
            jd_requirements["min_experience_years"],
            jd_requirements["preferred_experience_years"],
        )
        education_result = match_education(
            candidate.education or [],
            jd_requirements["required_education"],
        )
        semantic = semantic_by_id.get(candidate.id)

        scoring = compute_final_score(
            {
                "semantic": semantic,
                "skills": skills_result["skills_score"],
                "experience": experience_result["experience_score"],
                "education": education_result["education_score"],
            }
        )
        explanation = build_explanation(
            candidate.candidate_name, scoring, skills_result, experience_result, education_result
        )

        results.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.candidate_name,
                "final_score": scoring["final_score"],
                "semantic_score": semantic,
                "skills_score": skills_result["skills_score"],
                "experience_score": experience_result["experience_score"],
                "education_score": education_result["education_score"],
                "matched_skills": skills_result["matched_skills"],
                "missing_skills": skills_result["missing_skills"],
                "experience_gap": experience_result["experience_gap"],
                "score_breakdown": scoring["breakdown"],
                "explanation": explanation,
            }
        )

    ranked = rank_candidates(results)

    # Persist the analysis so the dashboard can show real history (Day 3).
    analysis_id = uuid4().hex
    for result in ranked:
        db.add(
            MatchResult(
                analysis_id=analysis_id,
                candidate_id=result["candidate_id"],
                job_title=jd_requirements["job_title"],
                rank=result["rank"],
                final_score=result["final_score"],
                semantic_score=result["semantic_score"],
                skills_score=result["skills_score"],
                experience_score=result["experience_score"],
                education_score=result["education_score"],
                matched_skills=result["matched_skills"],
                missing_skills=result["missing_skills"],
                explanation=result["explanation"],
            )
        )
    db.commit()

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "total_candidates": len(results),
        "not_found_ids": not_found_ids,
        "job_requirements": jd_requirements,
        "ranked_candidates": ranked,
    }


@router.get("/latest")
def latest_analysis(db: Session = Depends(get_db)) -> dict:
    latest_row = db.query(MatchResult).order_by(MatchResult.id.desc()).first()
    if latest_row is None:
        return {"status": "success", "analysis": None}
    rows = (
        db.query(MatchResult)
        .filter(MatchResult.analysis_id == latest_row.analysis_id)
        .order_by(MatchResult.rank)
        .all()
    )
    return {
        "status": "success",
        "analysis": {
            "analysis_id": latest_row.analysis_id,
            "job_title": latest_row.job_title,
            "created_at": latest_row.created_at.isoformat() if latest_row.created_at else None,
            "ranked_candidates": [
                {
                    "rank": r.rank,
                    "candidate_id": r.candidate_id,
                    "final_score": r.final_score,
                    "semantic_score": r.semantic_score,
                    "skills_score": r.skills_score,
                    "experience_score": r.experience_score,
                    "education_score": r.education_score,
                    "matched_skills": r.matched_skills or [],
                    "missing_skills": r.missing_skills or [],
                    "explanation": r.explanation or [],
                }
                for r in rows
            ],
        },
    }