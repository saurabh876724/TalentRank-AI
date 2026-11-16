# TalentRank AI – Deployment Review

**Status: reviewed, not deployed.** Deployment is optional for this assessment. The
verified deliverable is a reliable local demonstration; nothing in this repository
claims a live hosted instance.

## What a deployment would require

### Frontend (static SPA)

- `npm run build` produces `frontend/dist` (verified: app 48.6 kB, vendor 223.3 kB,
  charts 385.5 kB). Serve it from any static host (Netlify, Vercel, GitHub Pages,
  nginx) with SPA fallback to `index.html` for client-side routes.
- Production API URL is build-time configuration: set `VITE_API_BASE_URL` in
  `frontend/.env` (or the host's env) **before** `npm run build`, e.g.
  `VITE_API_BASE_URL=https://api.example.com`. The committed `.env.example` carries
  only the placeholder `http://127.0.0.1:8000`.
- HTTPS is required in production if the backend is HTTPS (mixed-content blocking).

### Backend (FastAPI + model)

- Run `uvicorn main:app --host 0.0.0.0 --port 8000` behind a reverse proxy
  (nginx/Caddy) with TLS. Do not use `--reload` in production.
- **Model hosting/memory:** `all-MiniLM-L6-v2` loads once per process
  (~300–500 MB RAM with torch CPU). A 1 GB RAM instance is the practical minimum;
  2 GB recommended. First request after boot downloads the model (~90 MB) unless the
  Hugging Face cache is baked into the image; set `HF_HOME` to a persisted volume to
  avoid re-downloads on restart.
- CPU-only torch wheels are already pinned in `requirements.txt`
  (`--extra-index-url https://download.pytorch.org/whl/cpu`), keeping images small.
- Multiple workers multiply model memory (one copy per process); start with 1 worker.

### Database persistence

- SQLite (`backend/talentrank.db`) is a single-file, single-writer store: fine for a
  demo, unsuitable for concurrent multi-user production or ephemeral containers
  (data lost on redeploy unless the file lives on a persisted volume).
- `TALENTRANK_DATABASE_URL` accepts any SQLAlchemy URL; moving to PostgreSQL is a
  configuration change plus driver install, but the lightweight `ALTER TABLE`
  migration in `database/database.py` would need review for a real migration tool
  (Alembic) before production use.

### CORS and security

- `TALENTRANK_CORS_ORIGINS` defaults to `http://localhost:3000,http://localhost:5173`.
  For deployment set it to the exact frontend origin(s), e.g.
  `TALENTRANK_CORS_ORIGINS=https://talentrank.example.com`. Never use `*` with
  credentials.
- Uploads are validated (extension, 5 MB size, 20-file batch), processed in memory,
  never executed, never written to disk, and never served back via URLs — this
  behaviour is deployment-safe as-is.
- There is **no authentication**. A public deployment would expose candidate data
  (even synthetic) to anyone; add auth before any real-world use.
- No secrets are required at runtime (no API keys); keep it that way or inject via
  environment variables, never committed files.

## Environment variables summary

| Variable | Purpose | Production example |
|---|---|---|
| `VITE_API_BASE_URL` | Frontend → backend base URL (build-time) | `https://api.example.com` |
| `TALENTRANK_DATABASE_URL` | SQLAlchemy database URL | `postgresql+psycopg://user:pass@db:5432/talentrank` |
| `TALENTRANK_CORS_ORIGINS` | Comma-separated allowed origins | `https://talentrank.example.com` |
| `TALENTRANK_MAX_FILE_SIZE` | Per-file upload limit (bytes) | `5242880` |
| `TALENTRANK_MAX_BATCH` | Files per upload batch | `20` |
| `HF_HOME` | Hugging Face cache location (model persistence) | `/var/cache/huggingface` |

## Recommendation

For the assessment: demonstrate locally (two terminals, commands in README §8).
If a hosted demo is later wanted, the lowest-risk path is a single small VM/container
running both the static frontend (nginx) and one uvicorn worker with a persisted
volume for the SQLite file and HF cache — accepting the single-user limitation.