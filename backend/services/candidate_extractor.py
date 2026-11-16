"""Rule-based candidate information extraction from resume text.

No LLM APIs are used. Extraction is kept separate from document parsing.
"""
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Indian mobile (+91 / 0 prefix, starts 6-9, optional 5+5 split) and international (+CC).
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+91[\s-]?[6-9]\d{4}[\s-]?\d{5}"
    r"|(?<!\d)[6-9]\d{4}[\s-]\d{5}(?!\d)"
    r"|(?<!\d)[6-9]\d{9}(?!\d)"
    r"|\+\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4})(?!\d)"
)

SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python"],
    "Java": ["java"],
    "C++": ["c++"],
    "C": ["c programming"],
    "SQL": ["sql", "mysql", "postgresql", "postgres"],
    "React": ["react", "react.js", "reactjs"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "AWS": ["aws", "amazon web services"],
    "Docker": ["docker"],
    "Git": ["git", "github", "gitlab"],
    "Node.js": ["node.js", "nodejs"],
    "MongoDB": ["mongodb"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "Kubernetes": ["kubernetes"],
    "REST API": ["rest api", "restful"],
}

# "JavaScript" must not match inside "Java"; aliases are matched with boundaries.
_SKILL_PATTERNS: list[tuple[str, re.Pattern]] = []
for _canonical, _aliases in SKILL_ALIASES.items():
    for _alias in sorted(_aliases, key=len, reverse=True):
        escaped = re.escape(_alias)
        # \b fails for aliases ending in non-word chars like "c++" or "node.js".
        pattern = rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9+])"
        _SKILL_PATTERNS.append((_canonical, re.compile(pattern, re.IGNORECASE)))

DEGREE_RE = re.compile(
    r"\b(?:ph\.?d|doctorate|m\.?b\.?a|m\.?tech|m\.?e\.?|m\.?sc|m\.?c\.?a|"
    r"b\.?tech|b\.?e\.?|b\.?sc|b\.?c\.?a|b\.?com|bachelor(?:'s)?(?:\s+of)?|"
    r"master(?:'s)?(?:\s+of)?|diploma|higher secondary|class\s+(?:x|xii|10|12))\b",
    re.IGNORECASE,
)

INSTITUTION_RE = re.compile(
    r"[A-Z][A-Za-z.&' ]*(?:University|Institute of Technology|Institute|College|School of [A-Za-z ]+)",
)

EXPERIENCE_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|work\s+|industry\s+)?experience", re.IGNORECASE),
    re.compile(r"experience\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE),
    re.compile(r"total\s+experience\s*[:\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
]

_NAME_REJECT_WORDS = {
    "resume", "curriculum", "vitae", "cv", "profile", "summary",
    "contact", "education", "experience", "skills", "objective",
}


def extract_name(text: str) -> str | None:
    """Look at header lines; skip labels like 'RESUME' and lines with contact info."""
    for line in text.split("\n")[:8]:
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if any(ch.isdigit() for ch in line) or "@" in line or "|" in line:
            continue
        words = line.split()
        if not 2 <= len(words) <= 4:
            continue
        if any(w.lower().strip(":.,") in _NAME_REJECT_WORDS for w in words):
            continue
        if all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words):
            return line
    return None


def extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = PHONE_RE.search(text)
    if not match:
        return None
    return re.sub(r"[\s.-]", "", match.group(0))


def extract_skills(text: str) -> list[str]:
    found: list[str] = []
    for canonical, pattern in _SKILL_PATTERNS:
        if canonical in found:
            continue
        if pattern.search(text):
            found.append(canonical)
    # "Java" pattern can match inside "JavaScript" boundary-wise; drop if only JS present.
    if "Java" in found and "JavaScript" in found:
        if not re.search(r"(?<![A-Za-z0-9])java(?![A-Za-z0-9+])(?!\s*script)", text, re.IGNORECASE):
            found.remove("Java")
    return found


def find_skill_mentions(text: str) -> list[tuple[str, int]]:
    """Return (canonical_skill, match_position) for every skill mention.

    Used by the JD analyzer to classify each mention by its surrounding context.
    """
    mentions: list[tuple[str, int]] = []
    seen: set[str] = set()
    for canonical, pattern in _SKILL_PATTERNS:
        if canonical in seen:
            continue
        match = pattern.search(text)
        if match:
            seen.add(canonical)
            mentions.append((canonical, match.start()))
    return mentions


def extract_education(text: str) -> list[dict]:
    entries: list[dict] = []
    seen_degrees: set[str] = set()
    lines = text.split("\n")
    for i, line in enumerate(lines):
        degree_match = DEGREE_RE.search(line)
        if not degree_match:
            continue
        degree = degree_match.group(0)
        # Look at the same line and the next two lines for an institution name.
        context = "\n".join(lines[i : i + 3])
        institution_match = INSTITUTION_RE.search(context)
        key = degree.lower().replace(".", "").replace(" ", "")
        if key in seen_degrees:
            continue
        seen_degrees.add(key)
        entries.append(
            {
                "degree": degree,
                "institution": institution_match.group(0).strip() if institution_match else None,
                "details": line.strip(),
            }
        )
    return entries


def extract_experience_years(text: str) -> float | None:
    for pattern in EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            years = float(match.group(1))
            return int(years) if years.is_integer() else years
    return None


def extract_candidate_info(text: str) -> dict:
    return {
        "candidate_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience_years(text),
        "resume_text": text,
    }