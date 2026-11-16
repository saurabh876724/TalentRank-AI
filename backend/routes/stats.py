"""Dashboard statistics computed from real database records (Day 3)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.database import get_db
from models import Candidate, MatchResult

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> dict:
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    analyzed_candidates = (
        db.query(func.count(func.distinct(MatchResult.candidate_id))).scalar() or 0
    )
    total_analyses = db.query(func.count(func.distinct(MatchResult.analysis_id))).scalar() or 0

    latest_analysis = None
    latest_row = db.query(MatchResult).order_by(MatchResult.id.desc()).first()
    if latest_row is not None:
        rows = (
            db.query(MatchResult)
            .filter(MatchResult.analysis_id == latest_row.analysis_id)
            .order_by(MatchResult.rank)
            .all()
        )
        scores = [r.final_score for r in rows]
        buckets = [0] * 5  # 0-20, 20-40, 40-60, 60-80, 80-100
        for score in scores:
            index = min(4, int(score // 20))
            buckets[index] += 1
        latest_analysis = {
            "analysis_id": latest_row.analysis_id,
            "job_title": latest_row.job_title,
            "created_at": latest_row.created_at.isoformat() if latest_row.created_at else None,
            "candidate_count": len(rows),
            "average_score": round(sum(scores) / len(scores), 1),
            "highest_score": max(scores),
            "score_distribution": [
                {"range": label, "count": count}
                for label, count in zip(["0-20", "20-40", "40-60", "60-80", "80-100"], buckets)
            ],
        }

    return {
        "total_candidates": total_candidates,
        "analyzed_candidates": analyzed_candidates,
        "total_analyses": total_analyses,
        "latest_analysis": latest_analysis,
    }