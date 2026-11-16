"""Job description analysis.

Day 1: intake validation + storage (kept for /api/jobs/analyze).
Day 2: structured requirement extraction for the matching engine.

Extraction is rule-based and conservative: fields that are not explicitly
present in the JD are returned as null or empty lists, never invented.
"""
import re
from datetime import datetime, timezone

from config import settings
from services.candidate_extractor import (
    DEGREE_RE,
    EXPERIENCE_PATTERNS,
    find_skill_mentions,
)

# Prototype storage; matching reads the JD text directly from the request.
_stored_jobs: list[dict] = []


class JDValidationError(ValueError):
    pass


def analyze_job_description(job_description: str) -> dict:
    text = job_description.strip()
    if not text:
        raise JDValidationError("Job description must not be empty.")
    word_count = len(text.split())
    if word_count < settings.MIN_JD_WORDS:
        raise JDValidationError(
            f"Job description is too short ({word_count} words). "
            f"Please provide at least {settings.MIN_JD_WORDS} words."
        )
    _stored_jobs.append(
        {
            "text": text,
            "word_count": word_count,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {
        "status": "success",
        "message": "Job description received",
        "word_count": word_count,
    }


_PREFERRED_CONTEXT_RE = re.compile(
    r"\b(preferred|preferably|nice[- ]to[- ]have|good[- ]to[- ]have|bonus|a plus|is a plus|advantage|desirable|optional)\b",
    re.IGNORECASE,
)

_TITLE_PATTERNS = [
    re.compile(r"(?:job\s+title|position|role)\s*[:\-]\s*([^\n,.;]+)", re.IGNORECASE),
    re.compile(r"(?:hiring|seeking|looking for| recruiting)\s+(?:a|an)\s+([^\n,.;]+?)(?:\s+with\b|\s+who\b|[,.]|\n|$)", re.IGNORECASE),
]

_MIN_EXPERIENCE_RE = re.compile(
    r"(?:minimum|at least|min\.?)\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

_PREFERRED_EXPERIENCE_RE = re.compile(
    r"(?:preferred|preferably|nice[- ]to[- ]have|bonus|desirable)\s*(?:is\s*)?(?:at least\s*)?(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)"
    r"|(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+experience\s*)?(?:is\s+)?(?:preferred|preferably|a plus|bonus)",
    re.IGNORECASE,
)

_RESPONSIBILITY_HEADING_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:key\s+)?(?:responsibilities|duties|what you(?:'ll| will) do)\s*:\s*$",
    re.IGNORECASE,
)
_SECTION_HEADING_RE = re.compile(
    r"^\s*(?:requirements|qualifications|skills|education|experience|benefits|about (?:us|the role)|nice to have|preferred)\b",
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[tuple[str, int]]:
    """Split into sentences/lines, keeping each one's start offset in text."""
    parts: list[tuple[str, int]] = []
    offset = 0
    for chunk in re.split(r"(?<=[.!?;])\s+|\n", text):
        start = text.find(chunk, offset) if chunk else offset
        if chunk.strip():
            parts.append((chunk, start))
        offset = start + len(chunk)
    return parts


def _extract_job_title(text: str) -> str | None:
    # 1. Explicit labels ("Job Title:", "Position:", "Role:").
    match = _TITLE_PATTERNS[0].search(text)
    if match:
        title = match.group(1).strip()
        if 3 <= len(title) <= 80:
            return title
    # 2. A standalone heading line (short, no digits, not a sentence).
    first_line = text.strip().split("\n")[0].strip()
    if (
        3 <= len(first_line) <= 80
        and not any(ch.isdigit() for ch in first_line)
        and not first_line.endswith(".")
        and len(first_line.split()) <= 10
        and not re.match(r"^(?:we|are|looking|hiring|seeking|join|about|the)\b", first_line, re.IGNORECASE)
    ):
        return first_line
    # 3. "We are hiring a X ..." phrasing.
    match = _TITLE_PATTERNS[1].search(text)
    if match:
        title = match.group(1).strip()
        if 3 <= len(title) <= 80:
            return title
    return None


def _extract_experience_requirements(text: str) -> tuple[float | None, float | None]:
    minimum: float | None = None
    preferred: float | None = None
    for sentence, _ in _split_sentences(text):
        # A sentence may carry both a minimum and a preferred clause
        # ("minimum 3 years of experience, preferred 5 years"); classify each separately.
        for clause in re.split(r"[,;]", sentence):
            min_match = _MIN_EXPERIENCE_RE.search(clause)
            if min_match:
                years = float(min_match.group(1))
                minimum = years if minimum is None else min(minimum, years)
                continue
            pref_match = _PREFERRED_EXPERIENCE_RE.search(clause)
            if pref_match:
                years = float(pref_match.group(1) or pref_match.group(2))
                preferred = years if preferred is None else max(preferred, years)
                continue
            years = None
            for pattern in EXPERIENCE_PATTERNS:
                match = pattern.search(clause)
                if match:
                    years = float(match.group(1))
                    break
            if years is None:
                continue
            if _PREFERRED_CONTEXT_RE.search(clause):
                preferred = years if preferred is None else max(preferred, years)
            else:
                minimum = years if minimum is None else min(minimum, years)
    return minimum, preferred


def _extract_responsibilities(text: str) -> list[str]:
    lines = text.split("\n")
    responsibilities: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if _RESPONSIBILITY_HEADING_RE.search(stripped):
            collecting = True
            continue
        if collecting:
            if not stripped:
                if responsibilities:
                    break
                continue
            if _SECTION_HEADING_RE.match(stripped):
                break
            item = re.sub(r"^[\-*•\d.)\s]+", "", stripped)
            if item:
                responsibilities.append(item)
            if len(responsibilities) >= 10:
                break
    return responsibilities


def extract_jd_requirements(job_description: str) -> dict:
    """Structured JD requirements. Unmarked skill mentions default to required."""
    text = job_description.strip()

    required_skills: list[str] = []
    preferred_skills: list[str] = []
    sentences = _split_sentences(text)
    for skill, position in find_skill_mentions(text):
        containing = next(
            (s for s, start in sentences if start <= position < start + len(s)),
            "",
        )
        if _PREFERRED_CONTEXT_RE.search(containing):
            if skill not in preferred_skills:
                preferred_skills.append(skill)
        elif skill not in required_skills:
            required_skills.append(skill)
    # A skill explicitly required somewhere outranks a preferred mention.
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    minimum_experience, preferred_experience = _extract_experience_requirements(text)
    required_education = []
    for match in DEGREE_RE.finditer(text):
        degree = match.group(0)
        if degree.lower() not in {d.lower() for d in required_education}:
            required_education.append(degree)

    return {
        "job_title": _extract_job_title(text),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_experience_years": minimum_experience,
        "preferred_experience_years": preferred_experience,
        "required_education": required_education,
        "responsibilities": _extract_responsibilities(text),
    }