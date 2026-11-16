"""Bulk resume upload endpoint."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import settings
from database.database import get_db
from models import Candidate
from services.candidate_extractor import extract_candidate_info
from services.resume_parser import ResumeParseError, parse_resume

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


def safe_display_name(filename: str | None) -> str:
    # Strip any directory components to prevent path traversal in reports.
    return Path(filename or "unnamed").name


@router.post("/upload")
async def upload_resumes(
    files: list[UploadFile],
    db: Session = Depends(get_db),
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    if len(files) > settings.MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {settings.MAX_FILES_PER_BATCH} per batch.",
        )

    candidates: list[dict] = []
    errors: list[dict] = []

    for upload in files:
        filename = safe_display_name(upload.filename)
        try:
            extension = Path(filename.lower()).suffix
            if extension not in settings.ALLOWED_EXTENSIONS:
                raise ResumeParseError(
                    "Unsupported file format. Only PDF and DOCX resumes are accepted."
                )

            # Files are processed fully in memory; nothing is written to disk.
            content = await upload.read()
            if not content:
                raise ResumeParseError("Uploaded file is empty (0 bytes).")
            if len(content) > settings.MAX_FILE_SIZE_BYTES:
                raise ResumeParseError(
                    f"File exceeds the {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB size limit."
                )

            text = parse_resume(filename, content)
            info = extract_candidate_info(text)

            candidate = Candidate(
                candidate_name=info["candidate_name"],
                email=info["email"],
                phone=info["phone"],
                skills=info["skills"],
                education=info["education"],
                experience_years=info["experience_years"],
                resume_text=text,
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

            candidates.append(
                {
                    "id": candidate.id,
                    "filename": filename,
                    "candidate_name": info["candidate_name"],
                    "email": info["email"],
                    "phone": info["phone"],
                    "skills": info["skills"],
                    "education": info["education"],
                    "experience_years": info["experience_years"],
                }
            )
        except ResumeParseError as exc:
            errors.append({"filename": filename, "error": str(exc)})
        except Exception:
            db.rollback()
            errors.append({"filename": filename, "error": "Unable to process this file."})
        finally:
            await upload.close()

    return {
        "total_uploaded": len(files),
        "successfully_processed": len(candidates),
        "failed": len(errors),
        "candidates": candidates,
        "errors": errors,
    }