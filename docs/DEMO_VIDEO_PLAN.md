# TalentRank AI – Demonstration Video Plan (3–5 minutes)

Record a single continuous screen capture of the **real running application**
(backend on its configured port, frontend at http://localhost:5173) with the ten
synthetic resumes from `sample_resumes/`. No mock data, no edited-in scores.

Preparation before recording:

1. Start backend: `uvicorn main:app --reload --port 8000` (8010 on this machine).
2. Start frontend: `npm run dev`, open http://localhost:5173 in a clean browser profile.
3. Have `sample_resumes/` open in a file explorer window for drag-and-drop.
4. Keep the JD text below in a text file ready to paste.
5. Optional second tab: Swagger UI (`/docs`) and the GitHub repository page.

Job description to paste:

```
Senior Python Backend Developer
We are looking for a Senior Python Backend Developer to design and build scalable APIs and data pipelines for our recruitment analytics platform.
Required skills: Python, FastAPI, SQL, Docker, AWS, Git.
Preferred skills: React, Machine Learning, NLP.
Requirements: minimum 3 years of experience, preferred 5 years. Bachelor's degree in Computer Science or a related field.
Responsibilities: Design REST APIs, optimize database queries, deploy services to AWS, mentor junior developers.
```

## Timeline

**0:00–0:30 — Introduction and problem statement**
Show the empty dashboard. State the problem: manual resume screening is slow,
inconsistent and keyword-biased; recruiters need explainable rankings. One sentence
on what TalentRank AI does (parse → match → rank → explain).

**0:30–1:00 — Technology stack and architecture**
Show the README architecture diagram (or a slide): React + Vite + Tailwind + Recharts
frontend; FastAPI + SQLAlchemy + SQLite backend; local sentence-transformers
`all-MiniLM-L6-v2` + scikit-learn cosine similarity. Emphasize: model runs locally,
no paid APIs, all scores computed server-side.

**1:00–1:40 — Enter a Job Description**
Navigate to Job Analysis. Paste the JD, add the job title, submit. Point at the
extracted requirements panel: required vs preferred skills, minimum 3 / preferred 5
years, Bachelor's requirement, responsibilities — all computed by the backend.

**1:40–2:20 — Upload 10 synthetic resumes**
Drag all 10 files (5 PDF + 5 DOCX) from `sample_resumes/` into the upload zone.
Show the staged list, click Upload, show `Processed: 10, Failed: 0`. Optionally drop a
`.txt` file first to show client-side rejection, and mention corrupted files fail
individually without breaking the batch.

**2:20–3:00 — Run AI matching and show rankings**
Click "Analyze 10 candidates". Mention the first run loads the embedding model
(~10 s). Show the ranked table: rank, name, experience, match %, matched and missing
skills. Point out the order comes from the backend and the comparison chart below.

**3:00–3:40 — Candidate details and score breakdown**
Open the top candidate (Divya Bhatt in the reference run). Show overall score and
rank, the component-score chart (semantic / skills / experience / education),
matched vs missing skill badges, and the generated explanation including the score
breakdown. Open a mid-ranked candidate to contrast gaps (e.g. experience gap note).

**3:40–4:20 — Explain the matching algorithm**
Walk the README "Matching Algorithm" and "Scoring Methodology" sections: embeddings →
cosine similarity 0–100; skills weighted 2× required / 1× preferred; experience and
education partial credit; 40/30/20/10 weights; missing-data redistribution and the
neutral-50 policy for unknown values; deterministic tie-breaks. Stress honesty:
unknown ≠ zero, no fabricated scores.

**4:20–5:00 — Repository and documentation**
Show the GitHub repository tree, README sections, `docs/screenshots/`, the 75 passing
pytest tests (`python -m pytest backend/tests -q`) and the limitations section
(OCR not implemented, rule-based extraction). Close with future improvements.

## Recording notes

- Capture at 1440×900 or higher; keep the browser zoom at 100%.
- If the first matching run is slow, say so on camera — it is the model loading, not a freeze.
- Do not cut away errors: if an upload fails, show the per-file error message; it is a feature.
- All identities shown are synthetic; state this once during the upload segment.