# SmartCode

> Adaptive Python programming tutor with deterministic code grading and step-by-step AI teaching.

**Live deployment:** <https://smartcodelau.com/> &nbsp;·&nbsp; mirror: <https://lau-ai-tutor.duckdns.org/>

SmartCode is a web-based programming-practice platform that combines a real Python execution sandbox with the Google Gemini language model to deliver personalized, conversational tutoring. Students take a five-question diagnostic, receive a per-skill profile across five competencies, and are guided through a 55-problem curriculum where every submission is graded both deterministically (by a subprocess sandbox) and qualitatively (by an LLM that explains *why* a solution failed and suggests how to fix it).

The project is the **final submission** for LAU **COE 416 — Software Engineering**, Spring 2026 (Group 11, Section 12).

---

## Try It

| URL | Status |
| --- | --- |
| <https://smartcodelau.com/> | Live |
| <https://lau-ai-tutor.duckdns.org/> | Live (mirror — may be blocked on some institutional firewalls) |

**Demo accounts** *(password for all: `Test1234`)*:

| Email | Role | Notes |
| --- | --- | --- |
| `admin@example.com` | Admin | Full content + user management |
| `alice@example.com` | Student | Rich data — solved problems, skill history, feedback |
| `bob@example.com` | Student | Mid-progress |
| `carla@example.com` | Student | Mid-progress |
| `daniel@example.com` | Student | Fresh — useful to walk through the diagnostic |

---

## Features

| Area | Capability |
| --- | --- |
| **Diagnostic** | 5 open-ended Python coding questions, LLM-graded with plain-English partial credit; produces a per-skill 0–100 profile across Algorithms, Data Structures, Edge Cases, Code Quality, Time Complexity |
| **Editor** | LeetCode-style three-pane Monaco editor (problem · code · test cases) with three action buttons: **Run** (sandbox-only, free), **Run with AI** (sandbox + LLM commentary), **Submit** (final evaluation against hidden tests) |
| **Sandbox** | Per-case Python subprocess, 3 s timeout, deterministic pass/fail authority. Supports per-problem input/output adapters (linked-list construction, sorted-list-of-lists canonicalization, float-5dp formatting) |
| **AI grading** | LLM overlays the sandbox verdict with severity per case (`minor` / `moderate` / `severe`), per-axis scores (correctness / edge cases / code quality / time complexity), inferred Big-O, and actionable bullets |
| **AST cheater backstop** | Detects `return <literal>` and parameter-ignoring solutions deterministically; rejects them even when they happen to match a sample case |
| **Dynamic hints** | Three escalation levels; the LLM reads the student's in-progress code and produces a hint specific to *where this student is stuck*. Escalating cost: 3 → 5 → 8 → 8 → 8 points (cap 25). |
| **Interactive AI tutor** | Six-step conversational walkthrough that explains the problem, asks comprehension questions after each step, and advances only when the student demonstrates understanding |
| **Per-problem cheatsheet drawer** | Slide-in left panel with a w3schools-style Python syntax reference tailored to each specific problem (Gemini-generated, cached on `problems.cheatsheet_md`) |
| **3-pick recommender** | Returns 3 next-problem suggestions ordered best → good-fallback (LLM + heuristic fallback); 14-day spaced-repetition cooldown on solved problems |
| **Catalogue** | **55 LeetCode-style problems** across easy / medium / hard, each with 5–7 test cases (sample / public / hidden) and full sandbox configuration |
| **Skill updates** | Difficulty-weighted, efficiency-scaled, capped per submission, floored at zero — bad attempts never reduce skill scores |
| **Hint + failed-attempt penalty** | Severity-weighted point deduction with kind weights (`run = 0.5x`, `submit = 1.0x`); final score clamped to `[50, 100]` so a correct submission never drops below 50 |
| **Admin** | Manage users, problems, skills, test cases (with sample/public/hidden visibility), and audit logs |
| **Auth** | bcrypt (cost 12) + JWT; strong-password validator (8+ chars, mixed case, digit, 28-entry blacklist) |
| **Deployment** | Single FastAPI process serving JSON API + built React SPA; Caddy reverse-proxy with auto-renewing Let's Encrypt certificate; dual-domain SAN cert (`smartcodelau.com` + `lau-ai-tutor.duckdns.org`) |

---

## Architecture

```
                       ┌────────────────────────────┐
                       │   Student's Browser        │
                       │   React 19 SPA + Monaco    │
                       └─────────────┬──────────────┘
                                     │ HTTPS / TLS 1.3
                                     ▼
   ═══════════════════════════════════════════════════ AWS EC2 ═══════════
                                     │
                       ┌─────────────▼──────────────┐
                       │  Caddy (:80 + :443)        │
                       │  Let's Encrypt ACME        │
                       └─────────────┬──────────────┘
                                     │ loopback 127.0.0.1:8001
                                     ▼
            ┌───────────────────────────────────────────────────┐
            │  uvicorn → FastAPI 0.115                          │
            │  JSON API + serves dist/ (React build)            │
            └───────┬──────────────────┬─────────────────┬──────┘
                    │                  │                 │
                    ▼                  ▼                 ▼
            ┌───────────┐      ┌──────────────┐   ┌─────────────┐
            │ MariaDB   │      │ google-genai │   │ Python      │
            │ 17 tables │      │ (Gemini API) │   │ subprocess  │
            └───────────┘      └──────────────┘   │ sandbox     │
                                                  └─────────────┘
```

The same diagram (and the full database ERD, all use-case models, the activity diagram, and screenshots of every screen) appears in the final report — see [`SmartCode_Final_Report.pdf`](SmartCode_Final_Report.pdf).

---

## Tech Stack

| Layer | Choice |
| --- | --- |
| **Frontend** | React 19 · Vite 8 · Tailwind CSS v4 · `react-router-dom` v7 · `@monaco-editor/react` · `react-resizable-panels@^2.1.0` · `recharts` · `lucide-react` |
| **Backend** | Python 3.11 · FastAPI 0.115 · SQLAlchemy 2 · PyMySQL · python-jose (JWT) · bcrypt · `google-genai` |
| **Database** | MariaDB 12 (17 tables; see [`database/schema.sql`](database/schema.sql)) |
| **LLM** | Google Gemini 2.5 Flash (with deterministic heuristic fallback for every LLM-backed feature) |
| **Sandbox** | Python `subprocess` with per-case timeout; `tracemalloc` for peak-memory metric |
| **Reverse proxy** | Caddy with automatic Let's Encrypt HTTP-01 cert renewal |
| **Deployment target** | AWS EC2 t3.small (Windows Server 2025); NSSM-managed Windows services |

---

## Repository Layout

```
SmartCode/
├── README.md                       ← you are here
├── SmartCode_Final_Report.pdf      ← 29-page IEEE-format final report
├── SmartCode_Presentation.pdf      ← 12-slide demo deck
│
├── src/                            ← React frontend
│   ├── api/                       fetch wrappers (auto-attach JWT)
│   ├── components/                Nav, Layout, CheatsheetDrawer, ProtectedRoute
│   ├── context/AuthContext.jsx    real auth state, /me validation
│   ├── screens/
│   │   ├── auth/                  Login, Register
│   │   ├── student/               Diagnostic, Dashboard, ProblemList,
│   │   │                          Editor (Monaco + split panes), Feedback
│   │   └── admin/                 Dashboard, Problems CRUD, Skills CRUD,
│   │                              Assessments, Users (with drilldown)
│   └── App.jsx                    router only
│
├── backend/                   ← FastAPI application
│   ├── app/
│   │   ├── main.py                FastAPI app, CORS, /api/health, mount routers
│   │   ├── config.py              Pydantic Settings (reads .env)
│   │   ├── database.py            SQLAlchemy engine + SessionLocal + get_db
│   │   ├── models.py              ORM models for all 17 tables
│   │   ├── schemas.py             Pydantic request/response models
│   │   ├── security.py            bcrypt + JWT encode/decode
│   │   ├── deps.py                get_current_user, require_diagnostic_complete
│   │   ├── audit.py               audit_log writer
│   │   ├── routers/
│   │   │   ├── auth.py              /register · /login · /me
│   │   │   ├── skills.py            /me/skills · /me/skills/history · /skills
│   │   │   ├── problems.py          /problems · /:id · /run · /run-ai · /hint
│   │   │   │                        /ai-tutor/turn · /ai-solve/stream · /ai-solution
│   │   │   │                        /my-attempt · /my-submissions
│   │   │   ├── submissions.py       POST /submissions · GET /submissions/:id
│   │   │   ├── recommendations.py   /me/recommendations/next  (3 picks)
│   │   │   ├── diagnostic.py        POST /diagnostic · GET /diagnostic/last
│   │   │   └── admin.py             /admin/stats · /users · /problems CRUD
│   │   │                            /skills CRUD · /test-cases CRUD
│   │   ├── llm/
│   │   │   ├── client.py            google-genai wrapper (JSON mode + streaming)
│   │   │   ├── diagnostic_grader.py
│   │   │   ├── submission_evaluator.py   sandbox-first + LLM overlay + AST backstop
│   │   │   ├── hint_generator.py
│   │   │   ├── solution_generator.py
│   │   │   ├── recommender.py       3-pick LLM + heuristic fallback
│   │   │   └── interactive_tutor.py 6-step chat tutor
│   │   └── sandbox/
│   │       └── python_runner.py     PROBLEM_CONFIGS for all 55 slugs
│   ├── scripts/
│   │   └── generate_cheatsheets.py  one-shot Gemini generator for cheatsheets
│   ├── requirements.txt
│   └── .env.example
│
├── database/
│   ├── schema.sql                 17-table DDL
│   ├── seed_problems.sql          original 15 problems + content
│   ├── seed_problems_extra.sql    40 additional problems (IDs 16-55)
│   ├── seed_cheatsheets.sql       55 per-problem Python cheatsheets
│   ├── seed_users.sql             5 demo accounts (admin + 4 students)
│   ├── seed.sql                   destructive full reset (sources all of the above)
│   └── test_queries.sql           handy SELECTs for development
│
├── deploy/
│   ├── bootstrap-ec2.ps1          first-time EC2 setup (Chocolatey, Python,
│   │                              Node, MariaDB, NSSM, schema, frontend build,
│   │                              service registration)
│   ├── enable-https.ps1           Caddy + Let's Encrypt; accepts multiple domains
│   ├── redeploy-patch.ps1         surgical re-deploy preserving DB + .env
│   ├── patch-cheatsheets.ps1      apply the cheatsheet migration + seed
│   ├── patch-tutor.ps1            apply the interactive tutor backend + UI
│   ├── patch-40problems-3picks.ps1
│   └── perf_test.py               NFR-3.2.6 load test (stdlib-only)
│
└── docs/
    └── system-architecture.mmd    Mermaid source (paste into mermaid.live)
```

---

## Run It Locally

### 1. Prerequisites

- **Python 3.11+** (3.11 was used for development)
- **Node.js 18+** (24 was used for development) and `npm`
- **MariaDB 11+** or compatible MySQL 8 (port 3307 was used; adjust as needed)
- A **Google Gemini API key** — free tier from <https://aistudio.google.com/app/apikey> works. Without one the project still runs in degraded mode (sandbox-only grading, deterministic heuristic fallbacks).

### 2. Database

```sql
-- In your MariaDB client:
SOURCE database/schema.sql;
SOURCE database/seed_problems.sql;
SOURCE database/seed_problems_extra.sql;
SOURCE database/seed_cheatsheets.sql;
SOURCE database/seed_users.sql;
```

The first script `DROP`s and recreates the `ai_tutor_system` database. The four seeds populate skills, 55 problems with test cases + hints + cheatsheets, and 5 demo users.

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                # Windows;  source .venv/bin/activate on POSIX
pip install -r requirements.txt

# Copy the env template and fill in your DB password + Gemini key
cp .env.example .env
# Edit .env:
#   DATABASE_URL=mysql+pymysql://root:<your-pw>@127.0.0.1:3307/ai_tutor_system
#   JWT_SECRET=<random 48 bytes base64>
#   GOOGLE_API_KEY=<your-gemini-key>     (optional)

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs auto-served at <http://127.0.0.1:8000/docs>.

### 4. Frontend

```bash
# from the project root (not backend/)
npm install --legacy-peer-deps        # --legacy-peer-deps for React 19 peer deps
npm run dev
```

Vite's dev server hosts the SPA at <http://localhost:5173> and proxies `/api/*` to `http://127.0.0.1:8000` (see [`vite.config.js`](vite.config.js)), so no CORS dance is needed in development.

---

## Deploy to AWS EC2

The `deploy/` folder contains idempotent PowerShell scripts that drive a Windows-Server-2025 EC2 instance from zero to a live HTTPS-enabled installation. Recommended sequence:

1. Launch a t3.small Windows-Server-2025 EC2 with an Elastic IP.
2. RDP in, copy this repo into `C:\AI-Tutor-system\`, drop your real `.env` into `backend\.env`.
3. Run `.\deploy\bootstrap-ec2.ps1` — installs Chocolatey + Python + Node + MariaDB + NSSM, restores the schema + seeds, builds the frontend, registers uvicorn as a Windows service on port 80.
4. Point one or more DNS A records at the Elastic IP (DNS-only / gray cloud on Cloudflare).
5. Run `.\deploy\enable-https.ps1 -Domain 'your-domain.com,alt-domain.com' -Email you@example.com` — installs Caddy, moves uvicorn to loopback, opens 443, fetches the Let's Encrypt cert. The same Caddyfile can serve multiple SAN names from one site block.

See [`SmartCode_Final_Report.pdf`](SmartCode_Final_Report.pdf) (Deployment section) for the full deployment topology and AWS security-group settings.

---

## Testing

Both layers of testing are documented in detail in [`SmartCode_Final_Report.pdf`](SmartCode_Final_Report.pdf) §4:

- **§4.1 Automated unit tests** for the scoring math, AST cheater backstop, sandbox canonicalization, and diagnostic post-processing.
- **§4.2 End-to-end manual scenarios** against the live deployment (registration, diagnostic, problem attempt with hints, coincidence-solution rejection, interactive AI tutor, admin content management, LLM-offline degradation).
- **§4.3 Performance measurement** with `wrk` + interactive workflow timing (Table 5: per-endpoint median latency).
- **§4.4 LLM-offline robustness matrix** (Table 6: primary vs fallback behavior for every LLM-backed feature).
- **§4.5 Alpha + Beta Testing** with concrete findings (A1–A6 internal, B1–B6 external) and the fix shipped for each.

---

## Authors

Group 11, Section 12 — LAU COE 416 (Spring 2026), Dr. Helen Saad

- Mohamed Darwish
- Karim Koaik
- Yehya Mazloum
- Mohammad Ismail Hashem

---

## License

This is academic coursework. The code is provided as-is for review by the course staff and for portfolio purposes; please do not redistribute or use in commercial work without contacting the authors.
