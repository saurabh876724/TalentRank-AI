"""TalentRank AI API — Day 1 backend entry point.

Run from the backend directory:  uvicorn main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database.database import init_db
from routes import candidates, jobs, matching, resume, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    description="AI-Based Resume Matching & Candidate Ranking System (Day 1 backend).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(candidates.router)
app.include_router(stats.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Do not leak internal details (paths, stack traces) to clients.
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error."},
    )


@app.get("/", tags=["Health"])
def root() -> dict:
    return {"message": "TalentRank AI API is running", "status": "success"}


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "healthy"}