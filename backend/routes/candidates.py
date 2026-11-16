"""Read-only candidate endpoints for the frontend (Day 3)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from models import Candidate, MatchResult

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


def _candidate_dict(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "candidate_name": candidate.candidate_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "skills": candidate.skills or [],
        "education": candidate.education or [],
        "experience_years": candidate.experience_years,
        "has_resume_text": bool(candidate.resume_text),
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
    }


def _match_dict(result: MatchResult) -> dict:
    return {
        "analysis_id": result.analysis_id,
        "job_title": result.job_title,
        "rank": result.rank,
        "final_score": result.final_score,
        "semantic_score": result.semantic_score,
        "skills_score": result.skills_score,
        "experience_score": result.experience_score,
        "education_score": result.education_score,
        "matched_skills": result.matched_skills or [],
        "missing_skills": result.missing_skills or [],
        "explanation": result.explanation or [],
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.get("")
def list_candidates(db: Session = Depends(get_db)) -> dict:
    candidates = db.query(Candidate).order_by(Candidate.id.desc()).all()
    return {"total": len(candidates), "candidates": [_candidate_dict(c) for c in candidates]}


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> dict:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")
    latest_match = (
        db.query(MatchResult)
        .filter(MatchResult.candidate_id == candidate_id)
        .order_by(MatchResult.id.desc())
        .first()
    )
    return {
        "candidate": _candidate_dict(candidate),
        "latest_match": _match_dict(latest_match) if latest_match else None,
    }