"""Job description endpoints (Day 1: validation + storage only)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.jd_analyzer import (
    JDValidationError,
    analyze_job_description,
    extract_jd_requirements,
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., min_length=1, description="Full job description text")


@router.post("/analyze")
def analyze_job(payload: JobDescriptionRequest) -> dict:
    try:
        result = analyze_job_description(payload.job_description)
    except JDValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result["requirements"] = extract_jd_requirements(payload.job_description)
    return result