# Development Guide

This guide covers everything you need to run SmartCode locally, run the test suite, and work on the codebase.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | 3.12 also works |
| Node.js | 18+ | 20 LTS recommended |
| MariaDB | 11+ | Must be running on port 3307 (or adjust `DATABASE_URL`) |
| Git | any | |
| Google Gemini API key | optional | AI features degrade gracefully without it |

---

## 1. Clone

```bash
git clone https://github.com/<your-org>/SmartCode.git
cd SmartCode
```

---

## 2. Database Setup

SmartCode uses MariaDB. The schema and seed data live in `database/`.

```sql
-- Connect to MariaDB as root, then:
CREATE DATABASE ai_tutor_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Apply schema and seed files in order:

```bash
mysql -u root -p ai_tutor_system < database/schema.sql
mysql -u root -p ai_tutor_system < database/seed.sql
mysql -u root -p ai_tutor_system < database/seed_problems.sql
mysql -u root -p ai_tutor_system < database/seed_problems_extra.sql
mysql -u root -p ai_tutor_system < database/seed_cheatsheets.sql
mysql -u root -p ai_tutor_system < database/seed_users.sql
```

To reset the database to a clean state, drop and re-create it, then reapply the files above.

---

## 3. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt   # includes httpx + pytest for tests
# or for production only: pip install -r requirements.txt
```

Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

Edit `backend/.env` — the only required values for a fully working local instance are:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy connection string (default targets `127.0.0.1:3307`) |
| `JWT_SECRET` | Any long random string (generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`) |
| `GOOGLE_API_KEY` | Optional — leave blank to disable LLM; deterministic fallbacks keep the UI functional |

Start the API server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

---

## 4. Frontend

```bash
# from the repo root
npm ci --legacy-peer-deps
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies `/api` to the backend automatically (configured in `vite.config.js`).

---

## 5. Running the Tests

```bash
cd backend
pytest backend/tests/ -v
```

Tests use the same `DATABASE_URL` from `backend/.env`. A running MariaDB with the seeded schema is required — there is no in-memory mock.

---

## 6. Generating Cheatsheets

Problem-topic cheatsheets are pre-generated Markdown files served statically. To regenerate them (requires a valid `GOOGLE_API_KEY`):

```bash
cd backend
python scripts/generate_cheatsheets.py
```

The output is written to `backend/cheatsheets/` and must be committed if you want changes to be reflected in production.

---

## Environment Variables Reference

All variables are read from `backend/.env` via Pydantic Settings. See `backend/app/config.py` for the authoritative list.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | SQLAlchemy URL, e.g. `mysql+pymysql://root:pass@127.0.0.1:3307/ai_tutor_system` |
| `JWT_SECRET` | Yes | — | HMAC signing key for access tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRES_MINUTES` | No | `1440` | Token lifetime in minutes (24 h) |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated list of allowed CORS origins |
| `GOOGLE_API_KEY` | No | _(blank)_ | Google Gemini API key; leave blank to disable LLM |
| `LLM_MODEL` | No | `gemini-2.5-flash` | Gemini model name |
| `LLM_MAX_TOKENS` | No | `4096` | Maximum tokens per LLM response |

---

## Project Layout (quick reference)

```
SmartCode/
├── backend/
│   ├── app/
│   │   ├── llm/          # Gemini integration (grader, hint, evaluator, …)
│   │   ├── routers/      # FastAPI route handlers
│   │   ├── sandbox/      # Isolated Python code runner
│   │   ├── main.py       # App factory and startup
│   │   ├── models.py     # SQLAlchemy ORM models
│   │   └── schemas.py    # Pydantic request/response schemas
│   ├── scripts/          # Offline tooling (cheatsheet generator)
│   ├── tests/            # pytest suite
│   ├── requirements.txt
│   └── .env.example
├── src/                  # React 19 frontend (Vite)
├── database/             # SQL schema + seed files
├── docker-compose.yml
└── package.json
```
