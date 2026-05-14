# SmartCode (AI Programming Tutor) — Final Project Report

**Course:** LAU COE 416 — Software Engineering, Spring 2026
**Instructor:** Dr. Helen Saad
**Group 11 — Section 12**

## Authors

- Mohamed Darwish
- Karim Koaik
- Yehya Mazloum
- Mohammad Ismail Hashem

**Submission 4 — Final Report, Implementation, and Demonstration**

**Live deployment:** https://smartcodelau.com/  (also reachable at https://lau-ai-tutor.duckdns.org/)
**Source code:** https://github.com/darwishmohammad433-droid/AI-Tutor-system

The product was renamed from the working title "AI Programming Tutor" to **SmartCode** late in the project after beta-user feedback that the original name was too generic. Both names appear in this document — "SmartCode" is the user-facing brand, "AI Programming Tutor" appears where we refer to the project as originally scoped in Submissions 1–3.

---

## Contents

1. Introduction
2. Background
3. Proposal
   - 3.1 Glossary
   - 3.2 User Requirements
   - 3.3 System Architecture
   - 3.4 System Requirements
   - 3.5 Use-Case Model
   - 3.6 System Models (Process, Sequence, Class)
   - 3.7 Database Design (Logical Schema)
   - 3.8 Implementation (including interactive tutor, 55-problem catalogue, cheatsheet drawer, 3-pick recommender)
   - 3.9 Scoring and Skill-Update System (Detailed)
   - 3.10 Deployment
4. Experimental Evaluation
   - 4.1 Automated Testing
   - 4.2 End-to-End Manual Testing
   - 4.3 Performance Measurement
   - 4.4 LLM-Offline Robustness
   - 4.5 Alpha and Beta Testing (internal pre-deploy + external post-deploy findings)
5. Conclusion
6. References
7. Appendix A — Submission 4 Checklist

---

# 1 Introduction

## Objective

The main objective of our project is to design and implement a web-based system called **AI Programming Tutor** that delivers a personalized, adaptive Python programming course to learners with varying skill levels. The system replaces the one-size-fits-all model used by most online practice sites with a tutor that grades each submission qualitatively, explains what went wrong in plain English, updates a per-skill profile after every attempt, and recommends the next problem that targets the student's weakest skill. It serves as a programming coach that is available 24/7, that never gets impatient, and that actually adapts to the student rather than the other way around. The project is an implementation of an end-to-end adaptive-learning workflow — diagnostic, problem solving, code execution, AI grading, dynamic hints, AI walkthroughs, and progress tracking — and is built using one of the standardized Software Engineering processes (an agile / Scrum workflow tracked in JIRA), thus serving the secondary role of acquainting us with the day-to-day responsibilities of a software engineer.

## Subject

The AI Programming Tutor is geared towards university students learning Python and, more broadly, towards anyone preparing for a technical interview or simply trying to get unstuck on classical problem-solving questions. The first time a student visits the site they create an account and immediately sit a five-question diagnostic of open-ended coding exercises. The diagnostic is graded by an LLM that assigns a 0–100 score per skill, writes a per-item explanation, and identifies the two-or-three weakest skills. From that moment forward the system is steering: the dashboard shows a radar chart of the student's five skills, the "Next Problem" card surfaces a recommendation tuned to those weak skills, and the LeetCode-style editor (Monaco + split panels + a real test-case panel) provides the workspace.

When the student writes code and clicks **Run**, a Python subprocess sandbox executes the code against the visible cases and the LLM layers qualitative scoring on top (code quality, edge-case awareness, time-complexity inference). **Submit** does the same against the visible *and* hidden cases. If the student gets stuck they can request **hints**, which are not pre-baked templates: the LLM reads the student's code-in-progress and produces a hint tailored to where *this* student is stuck right now. After accepting a solution, the student can open the **Solutions** tab and either read the cached canonical explanation or click **Watch AI Solve** to see Gemini stream its reasoning live as Server-Sent Events.

Two roles exist: **students**, who go through the journey above, and **administrators**, who manage problems, skills, and users through a dedicated admin area. The system is web-based, runs end-to-end on a single AWS EC2 instance with HTTPS, and is publicly accessible at <https://lau-ai-tutor.duckdns.org/>.

The traditional alternative — manually grinding problems on LeetCode or HackerRank — leaves the learner to figure out which topics they're weakest in, which problem to attempt next, and why a particular failed attempt failed. The result is a great deal of wasted time on problems that are either far too easy or far too hard, and very little structured feedback. The AI Programming Tutor automates that triage end-to-end: it knows the student's skill profile, the catalogue, and the most recent submission, and it recommends the single most useful next move every time.

[FIGURE 1: Hero screenshot of the deployed app at https://lau-ai-tutor.duckdns.org/ showing the student dashboard with the five-axis skill radar chart and the recommended next problem card]

# 2 Background

The AI Programming Tutor was prompted by an observation that all four team members shared from our own undergraduate experience: learning to program is a deeply individual process, but the tools that we are handed treat every student identically. A junior whose biggest weakness is recursion is shown the same homepage as a senior who is rehearsing dynamic programming for an internship interview. The platforms that *do* attempt personalization tend to do it badly — they cluster users by past activity and recommend whatever is popular, without ever looking at the student's actual code. Bad code that happens to pass a sample test case is rewarded just as much as good code that handles every edge.

The growth of capable, cheap LLMs in the last eighteen months has changed what is technically possible. A model the size of Gemini 2.5 Flash can read a student's Python submission and a problem statement, mentally execute the code, identify *which* edge case it misses, and write a paragraph of plain-English feedback explaining the fix — and it can do it in two to four seconds for a fraction of a US cent per call. That capability is the difference between a tutor that says "Wrong Answer" and a tutor that says *"Your two-pointer walk skips the case where both heights are equal — try moving the pointer with the strictly smaller value, breaking ties either way."* The first is what every existing system gives. The second is what a human TA would give. We set out to build the second, with classical execution-based grading as the load-bearing floor underneath.

A user of our application needs only a modern web browser. No download, no install, no IDE — the editor (Monaco, the same engine that powers VS Code) is in the browser, the sandbox runs server-side, and the LLM runs in Google's data centre. The application is designed to be practical and immediately useful: the path from "I just heard about this" to "I just submitted my first solution and got AI feedback" is under three minutes.

There is no comparable product targeted at university coursework. Commercial services such as LeetCode and HackerRank do not personalize, do not provide LLM-generated qualitative feedback, and do not maintain a per-skill profile across sessions. Recent OpenAI- and Anthropic-fronted tutor products (e.g. ChatGPT Tutor mode) lack a code-execution sandbox and so cannot ground their feedback in what the code actually does. The AI Programming Tutor combines both: a real Python interpreter and a strong LLM, with deterministic backstops so the system continues to function (in degraded mode) when either component is unavailable.

# 3 Proposal

## 3.1 Glossary

**Adaptive Learning.** A learning approach in which the system dynamically adjusts content, difficulty, and recommendations based on the user's measured performance and progress.

**LLM (Large Language Model).** A neural model — in our case Google Gemini 2.5 Flash — capable of generating and analyzing natural language and source code. The system uses the LLM as a grader, hint generator, problem recommender, and live solution walker.

**Sandbox.** An isolated execution environment used to safely run user-submitted Python code. In our system the sandbox is a `python -c <harness>` subprocess with a 3-second per-case timeout.

**Diagnostic.** A short, multi-question assessment given at the start of a student's journey to establish a baseline skill profile.

**Skill.** A measurable competency. The AI Programming Tutor tracks five skills: *Algorithms*, *Data Structures*, *Edge Cases*, *Code Quality*, and *Time Complexity*. Each is a 0–100 integer stored per user.

**Submission.** A user's attempt to solve a problem. Submissions have two flavors: **Run** (visible cases only, exploratory) and **Submit** (visible + hidden, scored).

**Severity.** A per-failed-test-case label of *minor*, *moderate*, or *severe* used to scale the failed-attempts penalty applied to subsequent submissions.

**Hint Penalty.** Points deducted from a final score when the user has requested hints on the current problem. The cost escalates per hint (3, 5, 8, 8, 8) and is capped at 25 total points.

**Recommendation.** A single next-problem suggestion the system computes after each accepted submission, tailored to the student's current weakest skills.

**SSE (Server-Sent Events).** A lightweight one-way streaming protocol used to push Gemini's "Watch AI Solve" output to the browser token-by-token.

**REST API.** The contract between the React frontend and the FastAPI backend; every screen calls one or more `/api/*` endpoints, and all responses are JSON.

**Use-Case Model.** A graphical representation of the interactions between the application and its actors (student, administrator).

**ERD (Entity-Relationship Diagram).** A graphical representation of the 17 tables in our MariaDB schema and the foreign-key relationships between them.

## 3.2 User Requirements

To better understand the user requirements, we divide them into Functional and Non-Functional categories.

### 3.2.1 Functional User Requirements

**The student shall be able to create an account and log in.** New users supply a name, email, and password (≥ 8 chars). The system rejects duplicate emails with a 409 and malformed payloads with a 422. Existing users log in with email + password and receive a JSON Web Token that is stored in `localStorage` and attached to every subsequent request.

**The student shall sit a diagnostic on first login.** The diagnostic consists of five open-ended Python coding questions; each question is tagged with the subset of the five skills it exercises. The student is free to type real Python, pseudocode, or plain-English explanations.

**The student shall receive an AI-graded breakdown of the diagnostic.** For each item the student sees `is_correct`, a per-skill 0–100 score, a 2–4 sentence explanation, and (where applicable) the canonical correct answer. The dashboard's skill radar chart is initialized from these scores.

**The student shall be able to browse and filter the problem catalogue.** The Problems screen shows all 15 active problems, their difficulty, the skills they target, and the student's current status (`not_started` / `attempted` / `solved`).

**The student shall be able to solve a problem in a LeetCode-style editor.** The editor uses Monaco (the editor engine behind VS Code), supports split panels, and renders sample test cases inline. Run and Submit are separate buttons.

**The student shall be able to request escalating hints.** Hint 1 is a high-level nudge; Hint 2 names the algorithm; Hint 3 sketches the approach in 2–3 lines of pseudocode. Hints are generated by the LLM from the student's current code, so two students stuck on the same problem receive different hints.

**The student shall be able to watch the AI solve a problem live.** After solving (or for admins, at any time), the Solutions tab streams Gemini's reasoning via SSE, headings-first: *Reading the problem → Looking at the constraints → First instinct: brute force → Why we can do better → The clean solution → Tracing through the first example → Complexity*.

**The student shall see how each submission updated their skill profile.** The submission detail page shows `score_correctness`, `score_edge_cases`, `score_code_quality`, `score_time_complexity`, the inferred Big-O, per-case verdicts, AI bullets, the per-skill delta caused by *this* submission, and the next recommended problem.

**The student shall not be able to re-attempt a solved problem.** Once a problem is `solved`, opening it brings up the accepted code, feedback, and hints in read-only **review mode**. (Implemented as a 409 on attempted resubmission.)

**The administrator shall be able to log in, manage problems, skills, and users.** Admin is determined by the `role` column in the `users` table.

### 3.2.2 Non-Functional User Requirements

**Availability.** The application should be reachable whenever a student accesses it. In particular the diagnostic, the editor, the AI grader, and the recommender are all on the critical path. When the LLM is unavailable the system falls back to deterministic heuristics rather than refusing to grade.

**Efficiency.** The application should return submission results within a few seconds. Run on visible cases should feel interactive; Submit, which includes hidden cases and an LLM call, may take longer but should remain under ten seconds in normal operation.

**Reliability.** The application shall persist every diagnostic, submission, hint request, and skill update to MariaDB so that returning students see exactly the same state they left.

**Usability.** The interface shall feel familiar to anyone who has used LeetCode. New users should be able to complete the diagnostic and solve their first problem in well under twenty minutes total.

**Security.** Passwords shall be stored as bcrypt hashes; authentication shall use JSON Web Tokens; all traffic shall be served over HTTPS in production; student-submitted code shall be executed in an isolated subprocess with a strict per-case timeout.

**Portability.** The application shall be usable on any modern desktop browser (Chrome, Edge, Firefox, Safari). The editor degrades gracefully on tablets; phones are out of scope.

## 3.3 System Architecture

**Figure 2 — High-level architecture of SmartCode.** Public traffic enters through Caddy on TCP/80 + 443 (with auto-redirect HTTP→HTTPS and Let's Encrypt-issued SAN certificates covering both `smartcodelau.com` and `lau-ai-tutor.duckdns.org`); Caddy reverse-proxies to uvicorn on loopback, which runs the FastAPI application serving both the JSON API and the compiled React SPA. FastAPI talks to three subsystems: MariaDB (local, port 3306) for persistent state, the Google Gemini API (HTTPS outbound) for every LLM-backed feature, and the Python subprocess sandbox (`python -c <harness>`) for deterministic correctness grading.

```
                       ┌────────────────────────────┐
                       │   Student's Browser        │
                       │   React 19 SPA  +  Monaco  │
                       │   JWT in localStorage      │
                       └─────────────┬──────────────┘
                                     │
                                     │  HTTPS / TLS 1.3
                                     │  smartcodelau.com  (or
                                     │  lau-ai-tutor.duckdns.org)
                                     ▼
   ══════════════════════════════════════════════════════════════  AWS EC2  ═══════
                                     │
                       ┌─────────────▼──────────────┐
                       │  Caddy  (port 80 + 443)    │
                       │  Let's Encrypt ACME        │
                       │  Reverse proxy + SSE flush │
                       └─────────────┬──────────────┘
                                     │  HTTP loopback  127.0.0.1:8001
                                     ▼
            ┌───────────────────────────────────────────────────────────┐
            │  uvicorn  →  FastAPI 0.115  (single process)              │
            │  ───────────────────────────────────────────────────────  │
            │   API routers                  │  Static frontend         │
            │     /api/auth                  │   serves dist/index.html │
            │     /api/diagnostic            │   /assets/* hashed       │
            │     /api/problems              │                          │
            │     /api/submissions           │  Cache-Control:          │
            │     /api/me/recommendations    │   no-store on index.html │
            │       (returns 3 picks)        │                          │
            │     /api/problems/.../hint     │                          │
            │     /api/problems/.../ai-tutor/turn  ← interactive tutor  │
            │     /api/problems/.../run      ← plain Run, no penalty    │
            │     /api/problems/.../run-ai   ← AI Run (sandbox + LLM)   │
            │     /api/admin/*                                          │
            └───────┬─────────────────────┬──────────────────────┬──────┘
                    │                     │                      │
                    ▼                     ▼                      ▼
        ┌────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐
        │  SQLAlchemy 2      │  │  google-genai       │  │  Python sandbox    │
        │  + PyMySQL         │  │  LLM client wrapper │  │  python -c HARNESS │
        └──────────┬─────────┘  │  • JSON mode        │  │  3 s / case        │
                   │            │  • text streaming   │  │  tracemalloc       │
                   ▼            │  • heuristic fallbk │  │  per-slug adapters │
        ┌────────────────────┐  └──────────┬──────────┘  └────────────────────┘
        │  MariaDB 12        │             │
        │  port 3306         │             │  HTTPS outbound
        │  17 tables         │             ▼
        │  (localhost only)  │  ┌──────────────────────────┐
        └────────────────────┘  │  Google Gemini 2.5 Flash │
                                │  (Google data center)    │
                                └──────────────────────────┘
```

The above diagram presents a high-level overview of the system architecture. All public traffic enters through **Caddy**, a reverse proxy that listens on TCP/80 and TCP/443, automatically obtains and renews Let's Encrypt certificates, and forwards everything to **uvicorn** on `127.0.0.1:8001`. uvicorn hosts the **FastAPI** application, which fulfills two responsibilities in a single process: it serves the JSON `/api/*` endpoints, and it serves the production build of the React SPA from `dist/`. Co-locating the frontend and the API on one origin removes the need for CORS in production and makes deployment a single-process affair.

The FastAPI application talks to two external systems. The first is **MariaDB 11** running on the same EC2 instance, accessed through SQLAlchemy 2 and PyMySQL; it holds all persistent state across the 17 tables described in Section 3.7. The second is **Google Gemini 2.5 Flash**, called over HTTPS through the `google-genai` Python SDK; every LLM-backed feature (submission grading, diagnostic grading, hint generation, problem recommendation, live solve streaming, canonical-solution generation) goes through a thin wrapper at `backend/app/llm/client.py` that knows how to enforce JSON response formats, stream text, and fall back when the API is unavailable.

A third "system" is the **Python sandbox**: a per-case subprocess (`python -c <harness>`) that compiles and executes the student's code against one test case at a time with a 3-second timeout, returning a JSON verdict on stdout. The sandbox is not security-hardened (the student-facing deployment trusts its own students), but it is *correctness-hardened*: it normalizes outputs (sorts list-of-lists, formats floats to five decimal places), constructs linked lists from arrays for `reverse-linked-list`, and catches user exceptions with line numbers.

The browser-side **React SPA** is built with React 19, Vite 8, Tailwind CSS v4, react-router-dom v7, and the Monaco editor. It stores the JWT in `localStorage['ai-tutor-token']`, attaches it to every fetch via a small wrapper in `src/api/client.js`, and revalidates the session on mount by calling `GET /api/auth/me`.

## 3.4 System Requirements

The system requirements expand the user requirements into testable, implementable specifications.

### 3.4.1 Functional System Requirements

**Registration and Login.**

- `POST /api/auth/register` accepts `{ full_name, email, password }`. Email uniqueness is enforced by a `UNIQUE` constraint on `users.email`. Passwords are bcrypt-hashed before storage. On success the response is HTTP 201 with a signed JWT and the user profile.
- `POST /api/auth/login` issues an opaque 401 ("Incorrect email or password") for both unknown-email and wrong-password cases so that user enumeration is not possible.
- `GET /api/auth/me` decodes the bearer token, fetches the user row, and returns the profile including `diagnostic_completed_at`. The frontend uses the presence of this timestamp (not a localStorage flag) to decide whether to route the user to the dashboard or the diagnostic.

**Diagnostic.**

- The diagnostic is implemented at `POST /api/diagnostic`. The payload is the entire five-item question set together with the student's answer for each item. The router passes the payload to `app.llm.diagnostic_grader.grade_diagnostic`, which calls Gemini with a strict JSON-schema prompt asking for, per item: `is_correct`, an overall 0–100 score, a `per_skill_scores` map (one entry per tested skill), an `answer_kind` ∈ {`code`, `pseudo_english`, `blank`}, and a 2–4 sentence `explanation_md`.
- The grader is required to give partial credit for plain-English answers — `code_quality` stays low because no real code was written, but the other axes are judged on the conceptual content of the explanation.
- The router persists per-item rows in `diagnostic_items`, sets `users.diagnostic_completed_at`, overwrites `user_skill` from the per-skill aggregate scores, and inserts a `recommendations` row for the recommended first problem.

**Problems and Hints.**

- `GET /api/problems` returns the active catalogue with the student's per-problem status.
- `POST /api/problems/{id}/hint` increments a hint counter and asks `app.llm.hint_generator.generate_hint` for a level-1, level-2, or level-3 hint based on the student's *current* in-progress code. The hint is persisted in `hint_requests`.
- `GET /api/problems/{id}/ai-solution` returns (and lazily generates and caches into `ai_solutions`) a canonical solution with Big-O analysis. `GET /api/problems/{id}/ai-solution/stream` streams the live "Watch AI Solve" walkthrough as Server-Sent Events.

**Submissions and Evaluation.**

- `POST /api/submissions` is the heart of the system. Given `{ problem_id, language, code }`, the router:
  1. Validates the problem and rejects the request with 409 if the user has already solved this problem.
  2. Runs `app.llm.submission_evaluator.evaluate_submission`, which executes the code in the sandbox against every test case (visible *and* hidden), then asks Gemini for qualitative scoring layered on top, then runs the AST cheater backstop.
  3. Computes the failed-attempts penalty (sum of severity-weighted points across prior failed Run/Submit attempts, with Run weighted 0.5× and Submit weighted 1.0×).
  4. Computes the hint penalty (escalating costs per hint, capped at 25 points).
  5. Applies both penalties to the raw evaluator score, clamped to [50, 100] (so a finally-correct solution is never crushed for trying), and persists the result.
  6. Updates the student's skill profile in `user_skill` and snapshots the new scores in `user_skill_history` (one row per skill per day).
  7. If accepted, calls the LLM recommender for the next problem and persists a `recommendations` row.
- `GET /api/submissions/{id}` returns the full submission detail, including per-case results, AI bullets, the skill deltas this submission produced, and the next-problem suggestion.

**Recommendations.**

- `GET /api/me/recommendations/next` returns the most recent unconsumed recommendation if one exists, or asks the LLM recommender for a fresh one if none does.

**Administrator endpoints.**

- `/api/admin/*` requires `role = 'admin'`. Endpoints exist for problems CRUD, skills CRUD, user listing, and global statistics.

### 3.4.2 Non-Functional System Requirements

**Availability.** The application runs as a Windows service under NSSM and restarts automatically on crash. Caddy runs as a separate Windows service, also auto-restarting. The LLM is the single external dependency; when Gemini is unavailable the heuristic fallback path keeps every endpoint functional in degraded mode (honest "graded offline" labels, deterministic recommendations).

**Performance.** Target: median submission grading latency < 5 s; target: 95th percentile < 12 s. The actual numbers are pending the formal benchmarking pass described in Section 4.

**Security.** Passwords are bcrypt-hashed with a generated salt. JWTs are signed with HS256 and a random 48-byte secret generated at deploy time. The production deployment opens only TCP/80 (redirect to 443) and TCP/443 to the public internet; uvicorn binds to `127.0.0.1:8001` only. `ALLOW_REGISTRATION=false` in production means new accounts can only be created by an admin.

**Maintainability.** New problems can be added in three places: a row in `problems`, the matching rows in `problem_skills` and `test_cases`, and (for sandboxed execution) a one-line entry in `PROBLEM_CONFIGS` mapping the slug to the Solution-class method name and parameter list. No code changes are required outside of `python_runner.py`.

**Portability.** Built and tested on Chrome 130+, Edge 130+, and Firefox 132+. The editor uses standard web fonts and renders identically across the three.

## 3.5 Use-Case Models

[FIGURE 3: Student use-case diagram — actor Student connected to use cases: Register/Login, Take Diagnostic, View Dashboard, Browse Problems, Solve Problem (includes Request Hint, Run Code, Submit Code), Watch AI Solve, View Submission Feedback, View Recommendation]

[FIGURE 4: Administrator use-case diagram — actor Administrator connected to: Log In, Manage Problems (create/edit/delete), Manage Skills, Manage Users, View Global Stats]

The student use-case diagram captures the linear path most students will take: register → diagnostic → dashboard → recommended problem → editor (with optional hints, runs, eventual submit) → submission feedback (with the next recommendation surfaced) → back to dashboard. The administrator diagram captures the parallel content-management workflow.

### Table 1 — Use-Case: Take Diagnostic

| Field | Description |
| --- | --- |
| Actors | Student, AI Diagnostic Grader (LLM), Database |
| Description | The student answers five open-ended coding questions, each tagged with one or more of the five tracked skills. The system grades each answer holistically and produces a per-skill score profile. |
| Pre-conditions | The student is authenticated and `diagnostic_completed_at` is `NULL`. |
| Post-conditions | `users.diagnostic_completed_at` is set, `user_skill` is overwritten with the per-skill aggregate scores, a `recommendations` row is inserted, and the student is redirected to the dashboard. |
| Data | Five questions (text + tested-skills tags) and the student's free-text answer per question. |
| Stimulus | Student clicks "Submit Diagnostic". |
| Response | A graded result page with per-item correctness, the per-skill radar visualization, an overall summary, and the suggested first problem. |
| Comments | Plain-English / pseudocode answers earn partial credit on all axes except *Code Quality* (which stays ≤ 25). Blank answers earn zero. |

### Table 2 — Use-Case: Submit Code

| Field | Description |
| --- | --- |
| Actors | Student, Sandbox (Python subprocess), AI Submission Evaluator (LLM), Database |
| Description | The student writes a Python solution in the Monaco editor and clicks **Submit**. The system runs the code against all test cases (visible + hidden), grades it qualitatively, applies penalty deductions for prior failed attempts and hint usage, updates the student's skill profile, and recommends the next problem. |
| Pre-conditions | The student has not yet solved this problem. The student is authenticated. |
| Post-conditions | A `submissions` row, a `metrics` row, a `feedback` row, possibly multiple `user_skill_history` rows, and (if accepted) a `recommendations` row are all persisted in a single transaction. |
| Data | `problem_id`, `language='python'`, and the full source code. |
| Stimulus | Student clicks "Submit". |
| Response | The submission detail page, showing per-case verdicts, AI bullets, the four scoring axes, the per-skill delta, and the next recommendation. |
| Comments | Once accepted, this problem becomes read-only for the student (further submits return 409). |

### Table 3 — Use-Case: Request Hint

| Field | Description |
| --- | --- |
| Actors | Student, AI Hint Generator (LLM), Database |
| Description | The student requests a hint while solving a problem. The LLM reads the problem statement, two sample cases, and the student's current in-progress code, then produces a hint at the requested escalation level (1 = nudge, 2 = direction, 3 = concrete). |
| Pre-conditions | The student is authenticated and has the problem open in the editor. |
| Post-conditions | A `hint_requests` row is persisted; the in-editor hint counter increments. The hint contributes to the eventual submission's score deduction. |
| Data | The student's current code and the desired hint level. |
| Stimulus | Student clicks "Get Hint". |
| Response | A 1–4 sentence markdown hint, possibly with a small pseudocode block (level 3 only). |
| Comments | Hints cost 3, 5, 8, 8, 8 points respectively, capped at a 25-point total deduction. |

### Table 4 — Use-Case: Watch AI Solve

| Field | Description |
| --- | --- |
| Actors | Student, AI Solution Streamer (LLM), Browser SSE Reader |
| Description | The student opens the Solutions tab on a solved problem and clicks "Watch AI Solve". The backend opens an SSE connection and streams Gemini's reasoning live, following a fixed headings-first structure (Reading the problem → Constraints → Brute force → Better approach → Clean solution → Trace → Complexity). |
| Pre-conditions | The student has solved this problem (or is an admin). |
| Post-conditions | None on the database side; the stream is not persisted. |
| Data | The problem statement, three sample cases, and the starter signature. |
| Stimulus | Student clicks "Watch AI Solve". |
| Response | A real-time markdown stream rendered word-by-word in the right panel. |
| Comments | Voice is first-person ("I'd...", "Let's...") to feel like a tutor at a whiteboard. The canonical Solution code is required to appear inside a single fenced `python` block under the "Clean solution" heading. |

### Table 5 — Use-Case: Manage Problems (Admin)

| Field | Description |
| --- | --- |
| Actors | Administrator, Database |
| Description | The administrator creates, edits, or deletes a problem and its associated test cases and skill tags. |
| Pre-conditions | The administrator is authenticated and `users.role = 'admin'`. |
| Post-conditions | The catalogue in `problems`, `problem_skills`, and `test_cases` is updated atomically. |
| Data | Problem title, slug, statement (markdown), constraints, starter code, difficulty, list of skill IDs with weights, list of test cases. |
| Stimulus | Administrator clicks "Save" in the admin Problems screen. |
| Response | A 200 OK with the updated problem row. |
| Comments | Adding a brand-new problem also requires a one-line entry in `PROBLEM_CONFIGS` (in `python_runner.py`) so the sandbox knows how to call the Solution class. |

## 3.6 System Models

### 3.6.1 Process Model — Submit pipeline

[FIGURE 5: Process / data-flow diagram of POST /api/submissions: Editor -> POST /api/submissions -> Validate -> Sandbox (per-case subprocess) -> LLM evaluator (with sandbox verdicts) -> AST cheater check -> Failed-attempts penalty + Hint penalty -> Final score clamp [50,100] -> Skill updates + history snapshot -> Problem status upsert -> LLM recommender (if accepted) -> JSON response to browser]

The submit pipeline is the longest data flow in the system. Every step except the LLM calls is purely local; the two Gemini calls (grading and, on acceptance, recommendation) are the only network hops out of the EC2.

### 3.6.2 Sequence Model — End-to-end submit

[FIGURE 6: UML sequence diagram with lifelines Browser, FastAPI, Sandbox, Gemini, MariaDB. Messages: Browser->FastAPI POST /api/submissions; FastAPI->MariaDB SELECT problem+cases; FastAPI->Sandbox run_all_cases (loop per case); FastAPI->Gemini call_json(system, user, sandbox verdicts); FastAPI->FastAPI AST cheater check; FastAPI->MariaDB SELECT prior submissions; FastAPI->FastAPI compute penalties + final score; FastAPI->MariaDB INSERT submission/metric/feedback/skill_updates/recommendation; FastAPI->Gemini call_json(recommender); FastAPI->Browser SubmissionDetail JSON]

### 3.6.3 Class Diagram — Backend

[FIGURE 7: UML class diagram of the SQLAlchemy ORM models — User, Skill, Problem, ProblemSkill, TestCase, DiagnosticAttempt, DiagnosticItem, Submission, Metric, Feedback, HintTemplate, HintRequest, UserSkill, UserSkillHistory, ProblemStatus, Recommendation, AiSolution. Show key foreign-key arrows: User 1..* Submission *..1 Problem *..* Skill (via ProblemSkill), Submission 1..1 Metric, Submission 1..1 Feedback, etc.]

### 3.6.4 Class Diagram — Frontend

[FIGURE 8: Component tree of the React SPA — App -> Router -> { Layout (Nav), AuthContext, ProtectedRoute } -> { LoginScreen, RegisterScreen, DiagnosticScreen, DashboardScreen, ProblemListScreen, EditorScreen (Monaco + SplitPanels + TestCasesPanel + HintsPanel + SolutionsPanel + LiveSolveStream), FeedbackScreen, AdminLayout -> { AdminDashboard, AdminProblems, AdminSkills, AdminUsers, AdminAssessments } }]

## 3.7 Database Design (Logical Schema)

The schema was originally specified in SRS Appendix B with **21 tables** organized around a three-track model (Basic / Intermediate / Senior). During implementation the team de-scoped the track concept (see Section 3.8.1) and trimmed the schema to **17 tables**. The five dropped tables were `tracks`, `user_tracks`, `test_suites` (folded into `test_cases`), `code_snapshots` (not implemented — the live editor doesn't persist per-keystroke history), and `test_runs` (replaced by `case_results_json` stored inline on `submissions`).

[FIGURE 9: ERD of the 17-table production schema. Show the central User node with its outbound arrows to Submissions, UserSkill, UserSkillHistory, DiagnosticAttempt, HintRequest, ProblemStatus, Recommendation. Show Problem with its M:N to Skill via ProblemSkill, 1:M to TestCase, 1:M to HintTemplate, 1:M to AiSolution. Submission 1:1 to Metric and 1:1 to Feedback.]

The 17 tables are:

1. **users** — identity, bcrypt password hash, role, `diagnostic_completed_at`.
2. **skills** — the five radar axes (Algorithms, Data Structures, Edge Cases, Code Quality, Time Complexity). `skill_id = 5` is intentionally left as a gap from the dropped "Debugging" skill so existing foreign keys remain valid.
3. **problems** — catalogue (slug, title, difficulty, markdown statement, constraints, starter code, `is_active`).
4. **problem_skills** — M:N between problems and skills with a weight in [0.6, 1.0] expressing how central a skill is to a given problem.
5. **test_cases** — input/expected pairs per problem, with `visibility` ∈ {`sample`, `public`, `hidden`} controlling whether Run sees them.
6. **diagnostic_attempts** — one row per attempt; stores `overall_score`, `summary_md`, and the grader source (`llm` vs `heuristic`).
7. **diagnostic_items** — one row per question per attempt, with `question_md`, `user_answer`, `correct_answer`, `is_correct`, `explanation_md`, and `score`.
8. **submissions** — one row per attempt at a problem; stores the source code inline, `kind` ∈ {`run`, `submit`}, the verdict, the final score, and the per-case JSON.
9. **metrics** — 1:1 with `submissions`, breaks the score into the four axes (correctness, edge cases, code quality, time complexity) and stores the inferred Big-O.
10. **feedback** — 1:1 with `submissions`, stores the summary markdown and the AI bullets as JSON.
11. **hint_templates** — pre-written hints per problem and level. (Currently unused — the LLM hint generator overrides them — but kept as a fallback path.)
12. **hint_requests** — log of every hint a user requested; drives the hint-penalty calculation.
13. **user_skill** — current skill score per user per skill (the radar chart on the dashboard).
14. **user_skill_history** — daily snapshots, one row per (user, skill, day), used to draw the historical line chart.
15. **problem_status** — per-user status of each problem (`not_started` / `attempted` / `solved`) plus best score and attempt count.
16. **recommendations** — log of every next-problem suggestion the system has made, with the reason text and the algorithm version (`llm-recommender-llm` or `llm-recommender-heuristic`).
17. **ai_solutions** — LLM-generated canonical solutions per problem (lazy, cached on first request).

Every FK uses `ON DELETE CASCADE` where ownership is hierarchical (e.g. deleting a user cascades to their submissions and history) and `ON DELETE SET NULL` where the relationship is associative (e.g. deleting a skill leaves the diagnostic_item but blanks its skill_id).

## 3.8 Implementation

### 3.8.1 De-Scoped Items From the SRS

Three significant scope changes were made between Submission 2 (SRS) and Submission 4 (this report). All three were design decisions taken to keep the project completable inside the semester budget *and* to deliver a tighter, more focused product.

**Tracks collapsed to a single Problem-Solving track.** The SRS specified three tracks: Basic, Intermediate, and Senior. After prototyping the navigation we concluded that the track abstraction was redundant with our per-skill profile + difficulty filter — a Basic student is exactly a student whose skill scores are low, and the recommender already accounts for that. We dropped the `tracks` and `user_tracks` tables and the entire track UI, freeing up an estimated three days of work.

**21 SRS tables trimmed to 17.** In addition to the two track tables, we folded `test_suites` into `test_cases` (every test case directly references its problem; we never needed the intermediate suite grouping), removed `code_snapshots` (the live editor doesn't autosave per-keystroke; submissions persist the full source on Submit), and removed `test_runs` (replaced by storing the case-results JSON inline on the `submissions` row, which is denormalized but eliminates a join from the hot path).

**The "Debugging" skill was removed.** The SRS implied six skills; we settled on five (Algorithms, Data Structures, Edge Cases, Code Quality, Time Complexity) because "Debugging" turned out to be unmeasurable in our format — every skill axis is *also* a kind of debugging. The `skill_id = 5` row is intentionally left as a gap in the schema so that foreign keys created against the pre-cleanup data continue to resolve cleanly. The radar chart on the dashboard is a five-axis pentagon, not a hexagon.

**The diagnostic was redesigned.** The SRS described an MCQ + coding diagnostic. We tested an MCQ-heavy diagnostic and found it produced low-signal scores: students could guess on MCQs but couldn't fake a coding answer. The final design is five open-ended Python coding questions, each tagged with the *subset* of skills it exercises. A single question can target Algorithms + Data Structures + Time Complexity simultaneously, which means each question contributes to multiple radar axes in one shot. The grader awards plain-English / pseudocode answers partial credit on every axis except Code Quality, so a student who understands the concept but writes shaky code is not penalized as harshly as one who writes nothing.

### 3.8.2 Frontend

The frontend is a single-page React 19 application built with Vite 8 and styled with Tailwind v4. Routing is done with `react-router-dom@7`; persistent layout (the nav bar and the `ProtectedRoute` wrapper) lives in `src/components/Layout.jsx`. Charts use `recharts` (the dashboard radar and the daily line chart); icons come from `lucide-react`.

The editor screen (`src/screens/student/EditorScreen.jsx`) is the most complex component. It uses `react-resizable-panels@^2.1.0` (deliberately pinned to v2 — v4 renamed `PanelGroup` to `Group` and is incompatible with our import sites) to deliver the LeetCode three-pane split: problem statement on the left, Monaco editor in the middle, test-cases / hints / solutions tab on the right. The right pane swaps between four sub-views: **Test Cases** (live pass/fail after Run), **Submission Feedback** (after Submit), **Hints** (cumulative escalating list), and **Solutions** (cached canonical + Watch AI Solve streaming).

Authentication state lives in `src/context/AuthContext.jsx`. On mount it reads the JWT from `localStorage['ai-tutor-token']`, calls `GET /api/auth/me` to validate it, and exposes `user`, `login()`, `register()`, `logout()`, and the derived `hasCompletedDiagnostic` boolean. All API calls go through `src/api/client.js`, which auto-attaches the bearer token and surfaces well-typed errors.

[FIGURE 10: Composite screenshot — dashboard with radar, problem list, LeetCode editor with Monaco + split panels, submission feedback page, admin problems screen]

### 3.8.3 Backend

The backend is a FastAPI 0.115 application running on Python 3.11. Routes live under `backend/app/routers/` and follow REST conventions. SQLAlchemy 2 with PyMySQL is the database layer; `backend/app/database.py` exposes the engine, `SessionLocal`, and a `get_db` FastAPI dependency that yields a session per request.

The LLM integration is at `backend/app/llm/`. The thin client (`client.py`) wraps `google.genai` and exposes three primitives: `is_available()`, `call_json(system, user)` (which forces `response_mime_type=application/json` and parses the result), and `call_text_stream(system, user)` (which yields plain text chunks for SSE). Every higher-level module (diagnostic grader, submission evaluator, hint generator, solution generator, recommender) is structured the same way: a Pydantic input model, a Pydantic output model, an LLM path, and a deterministic heuristic fallback that runs whenever `is_available()` returns False or the LLM call raises.

The sandbox is at `backend/app/sandbox/python_runner.py`. It defines a `PROBLEM_CONFIGS` dictionary keyed by problem slug, each entry specifying the Solution-class method name, parameter ordering, and any input/output adapters (linked-list construction, sorted-list-of-lists canonicalization for unordered output, float-to-five-decimals for numeric outputs). `run_all_cases(slug, user_code, cases)` runs the test cases serially in subprocesses with a 3-second per-case timeout and returns one `CaseExecutionResult` per case.

[FIGURE 11: Component diagram of the backend — FastAPI app at top, with routers (auth, skills, problems, submissions, recommendations, diagnostic, admin) feeding into shared LLM module (client, diagnostic_grader, submission_evaluator, hint_generator, solution_generator, recommender) and shared Sandbox module (python_runner with PROBLEM_CONFIGS), all using SQLAlchemy models against MariaDB]

### 3.8.4 Interactive Step-by-Step AI Tutor

An earlier version of SmartCode shipped a one-shot "Watch AI Solve" feature: the Solutions tab opened an SSE stream that produced a fixed seven-heading walkthrough (Reading the problem → Constraints → Brute force → Why we can do better → Clean solution → Trace → Complexity) word-by-word. It looked impressive in a demo but beta users gave consistent feedback: *the AI was lecturing, not teaching*. Students passively watched the full answer scroll by and admitted they retained little.

The final version replaces that one-shot stream with an **interactive, step-by-step tutor** that behaves like a TA who has done this fifty times. When the student opens the Solutions tab and clicks **Start tutor session**, the frontend sends an empty conversation history to `POST /api/problems/{id}/ai-tutor/turn`. The backend (`backend/app/llm/interactive_tutor.py`) is stateless — the frontend keeps the full chat history and replays it on every call — and prompts Gemini with a six-step pedagogical plan:

1. **Restate the problem** in the student's own words.
2. **Identify the trickiest edge case** before writing code.
3. **Brute force first** — propose the slow obvious approach.
4. **Spot the bottleneck** and the smart insight (hash map, two pointers, DP, monotonic stack, etc.).
5. **Sketch the code together** — one or two key lines at a time, never the full solution.
6. **Trace through the sample case**, predicting variable values along the way.

After each step the tutor produces 2–4 sentences of explanation followed by a single comprehension question, and stops. The student types an answer; the next call lets Gemini evaluate the answer ("Exactly", "Partially right — what about...", "Not quite — here's a hint, try again") and decide whether to advance `step_index` or re-ask. The conversation completes when `is_complete=true` is set after step 6. A progress bar at the top of the chat shows "Step X of 6".

The JSON contract per turn is intentionally small — `{ tutor_response, step_index, total_steps, is_complete, source }` — which keeps the LLM disciplined: it cannot ramble, dump the whole answer, or skip ahead. If Gemini is offline the endpoint returns a graceful "tutor is offline" message rather than a degraded fake conversation; the cheatsheet drawer (3.8.6) covers the syntax-help use case in the meantime.

### 3.8.5 Catalogue Expansion to 55 Problems

The original catalogue shipped 15 LeetCode-style problems. After deployment, beta users requested more variety. We expanded to **55 problems** (15 originals + 40 new, IDs 16–55) covering classic interview patterns: stacks, sliding windows, BFS/DFS, dynamic programming, backtracking, monotonic stacks, and the harder hash/two-pointer combinations.

All 40 new problems were authored in our own wording (the algorithmic concepts are not copyrightable; only specific test cases and prose are). Each carries its own `problem_skills` rows, 5–7 test cases (mix of sample / public / hidden), and 1–2 hint templates. The sandbox configuration in `python_runner.py` was extended in parallel — the existing four adapters (`default`, `linked_list`, `sorted_list_of_lists`, `float_5dp`) covered all 40 without needing new adapters. The seed lives in `database/seed_problems_extra.sql` and is loaded by an idempotent `INSERT … ON DUPLICATE KEY UPDATE` block so the file is safe to re-run while real users have submissions on problems 1–15.

### 3.8.6 Per-Problem Python Cheatsheet Drawer

A recurring beta-user complaint was that students stalled on syntax recall, not on algorithmic understanding — "I know I need a stack but I forgot how to peek in Python." To fix this we added a **per-problem cheatsheet** stored in `problems.cheatsheet_md` and surfaced as a slide-in left drawer on the editor screen (`src/components/CheatsheetDrawer.jsx`).

The cheatsheets are not authored by hand. A one-shot generator (`backend/scripts/generate_cheatsheets.py`) iterates the catalogue and asks Gemini, for each problem, to produce a w3schools-style reference containing **only the Python syntax that problem needs**. The output format is constrained — 3–6 sections of `## Heading` followed by a single fenced `python` block of 3–7 short lines with brief inline comments. For example, the cheatsheet generated for Valid Parentheses contains a Stack section (`stack.append`, `stack.pop`, `stack[-1]`, `not stack`), a Dictionary section (mapping closers to openers), an Iteration section, and a Conditional section — and nothing about heaps, trees, or recursion.

The drawer ships with a small floating "Cheatsheet" tab on the left edge of the workspace; a click slides the panel in over the workspace, an X (or Escape) closes it. The markdown parser is intentionally minimal (it only understands `##` headings and fenced code blocks, the only constructs the generator emits) so the renderer is robust to malformed model output.

### 3.8.7 Three Run-Style Buttons and 3-Pick Recommender

Two smaller UX changes round out the post-beta refresh.

**Three buttons in the editor action bar.** A LeetCode-style **Run** (plain, gray, sandbox-only, no AI, no penalty), a **Run with AI** (purple, sandbox + LLM commentary on severity / code quality / edge cases, slower, persists failed attempts as `Submission(kind='run')` for the half-weight penalty), and the existing **Submit** (green, full evaluation against hidden cases too). The plain Run is the "free smoke test" — it is intentionally penalty-free so students can experiment quickly without burning Gemini tokens or incurring score deductions.

**Three problem picks instead of one.** The `/api/me/recommendations/next` endpoint was changed to return a list of up to three `NextProblemSuggestion` objects (ordered best → good-fallback). The LLM prompt was updated to encourage diversity across the three picks — different weak skills or different difficulty — so the student has real choice. On the UI, the single-banner "Recommended for you" card on the problem list, the diagnostic-review screen, and the post-submission feedback screen all became a three-card grid: a gradient "Top pick" tile and two white-bordered "Option 2 / Option 3" tiles. If the LLM returns fewer than three valid picks the heuristic recommender pads the rest using the existing `(weak-overlap DESC, difficulty ASC, id ASC)` sort.

## 3.9 Scoring and Skill-Update System (Detailed)

This is the most novel part of the system. The naive approach — "run the test cases, count the passes, that's your score" — is what every existing platform does and we already know its failure modes: it rewards lucky-coincidence solutions (`return 5` happens to match the sample), it provides no incentive to write clean code, and it gives the student no signal about *why* their attempt failed beyond pass/fail. Our scoring pipeline is designed to fix all three problems while remaining fast, deterministic where it matters, and honest when the LLM is offline.

### 3.9.1 Sandbox-First Evaluator

The single most important design decision is that the **sandbox is authoritative for pass/fail**. The LLM is fluent and confident but it hallucinates; a real Python interpreter does not. Every submission goes through the sandbox first (`backend/app/sandbox/python_runner.py`), one subprocess per test case, with a 3-second timeout. The sandbox returns a `CaseExecutionResult` for each case: the actual output (canonicalized), the expected output (canonicalized), a `passed` boolean, and an optional `error` string with the exception class, line number, and message.

When Gemini is available, the LLM evaluator (`backend/app/llm/submission_evaluator.py`) is called with the problem, the test cases, the student's code, *and the sandbox verdicts*. Its job is no longer to decide pass/fail — that is fixed — but to provide everything the sandbox cannot: per-failed-case `severity` ∈ {`minor`, `moderate`, `severe`}, the per-axis qualitative scores (`score_edge_cases`, `score_code_quality`, `score_time_complexity`), the `inferred_big_o` string, the summary, and the actionable bullets. The router then *overlays* the sandbox truth onto the LLM result: every case's `passed` field is forcibly set to the sandbox verdict, and the overall status is recomputed (`accepted` only if every case passes).

The overall score in this LLM path is a weighted sum:

```
score = 0.55 * score_correctness  (always sandbox-driven)
      + 0.15 * score_edge_cases
      + 0.15 * score_code_quality
      + 0.15 * score_time_complexity
```

### 3.9.2 The AST Cheater Backstop

Even with a real sandbox, a student can game a problem by writing `return 5` if the sample case happens to expect 5. To catch this, we run an AST analysis (`_detect_lucky_coincidence` in the evaluator) *after* the sandbox and the LLM have spoken. The check parses the student's code with the `ast` module, finds the longest non-private method on the `Solution` class (this is "the solver"), and flags the submission as a coincidence if **either** of two patterns matches:

1. The solver's body is a single `return <literal>` (e.g. `return 5`, `return []`, `return True`).
2. The solver's body never references any of its parameters (e.g. it returns a value computed purely from constants, ignoring `nums`, `target`, `head`, etc.).

When either is true, the system overrides the evaluator output: every test case is marked failed with severity `severe`, the status becomes `wrong_answer`, `score_correctness` and `score_edge_cases` are zeroed, and a prominent warning bullet is prepended: *"Hardcoded / constant-returning solutions are not accepted, even if they happen to match the sample outputs. Implement a real algorithm that uses the input."*

The same logic is also baked into the LLM grader's system prompt as the **CHEATER / LUCKY-COINCIDENCE CHECK**, so the LLM also flags these patterns before scoring — the AST check is the deterministic backstop that catches the rare case where the LLM fails to notice.

### 3.9.3 The Failed-Attempts Penalty

A student who finally accepts a problem on their seventh attempt has *learned something* (their final solution works), but they did not learn it as efficiently as a student who accepted it first try. The system reflects this by accumulating a **severity-weighted penalty** across all prior failed attempts on the same problem.

For each prior failed attempt the system iterates the case-results JSON, and for each failed case it adds:

```
SEVERITY_POINTS[severity] * KIND_WEIGHT[kind]
```

where `SEVERITY_POINTS = {minor: 1, moderate: 2, severe: 3}` and `KIND_WEIGHT = {run: 0.5, submit: 1.0}`. Runs are weighted half because Run is meant to be exploratory; we don't want to punish a student for using Run to debug. The accumulated point total is then multiplied by `_PENALTY_MULTIPLIER = 2` and subtracted from the raw evaluator score.

### 3.9.4 The Hint Penalty

Hints have their own deduction, separate from failed attempts. The cost escalates per hint: **3, 5, 8, 8, 8** points respectively. The total hint deduction is capped at **25 points** so a student who exhausts hints on a hard problem still has a fighting chance of a decent score. The cap is mirrored on the editor side so the student sees the running cost live; the value displayed in the UI must match what the router deducts at Submit time.

### 3.9.5 Final Score Clamp

The final score is computed in a single line:

```python
final_score = max(50, min(100, round(raw_score - 2 * penalty_points - hint_penalty)))
```

The clamp to **[50, 100]** is intentional: a finally-correct solution is never crushed below 50, because the system's tutoring philosophy is that *passing matters*. We do not want a student who eventually solves a hard problem after six tries to get a 12/100 — that is demoralizing and doesn't reflect what they actually achieved.

The submission detail page exposes the breakdown to the student in plain English. Example: *"Final score reduced by 28 points (raw 95 → 67) due to 3 failed submits and 2 failed runs (each weighted 0.5x), and 2 hints requested (-8 pts) on this problem (3 severe, 4 moderate, 1 minor failed cases). Severe failures cost the most; runs cost half of submits."*

### 3.9.6 Skill Updates — Difficulty-Weighted, Capped, Floored

After the final score is known, the system updates the student's skill profile. The key insight is that **only the skills this problem targets are touched**. Two Sum is tagged with Algorithms + Data Structures, so a Two Sum submission moves at most those two skills — it does not touch Edge Cases or Time Complexity, because the act of solving Two Sum doesn't tell us anything about those. The journey balance comes from problem variety: as different problems target different skills, all five axes grow over time.

For each tagged skill the per-submission bump is:

```
raw_delta = (target - before) * weight * difficulty_factor
            * 0.08 * (final_score / 100)
```

where:

- `target` is the **most relevant LLM-graded axis** for the skill (Edge Cases listens to `score_edge_cases`, Code Quality listens to `score_code_quality`, etc.).
- `weight` ∈ {0.6, 0.8, 1.0} comes from `problem_skills.weight` and reflects how central the skill is to this specific problem.
- `difficulty_factor` ∈ {0.5, 1.0, 1.5} for easy / medium / hard.
- `final_score / 100` is the **efficiency multiplier**. A student who scored 100/100 (clean first try, no hints) earns the full bump. A student whose final score was 50/100 (several prior failed attempts or a heavily hint-assisted solve) earns half. So passing on the sixth try is worth meaningfully less than passing on the first.

The bump is then clamped: **easy +1, medium +2, hard +3** per submission, with a **floor of 0** (bad submissions never *decrease* skill scores). A daily snapshot is written to `user_skill_history` so the dashboard line chart can show progression over time.

### 3.9.7 Diagnostic Grading — Plain-English Partial Credit

The diagnostic grader (`backend/app/llm/diagnostic_grader.py`) is a separate LLM path with its own prompt. Its key innovations are:

- **Multi-skill items.** Each diagnostic question carries a `tested_skills` list. The grader produces a `per_skill_scores` map per item so a single question can contribute to multiple radar axes.
- **`answer_kind` classification.** The grader labels each answer as `code`, `pseudo_english`, or `blank` — and this label has scoring consequences. A plain-English answer with the right algorithmic idea still earns 50–75 on Algorithms / Data Structures / Edge Cases / Time Complexity (because the conceptual understanding is there) but is capped at 25 on Code Quality (because no code was written). A blank answer is zero on every axis with no exceptions.
- **Hard caps in code, not in the prompt.** The grader code post-processes the LLM output to enforce the caps even when the LLM violates them (`per_skill["Code Quality"] = min(per_skill["Code Quality"], 25)` for `pseudo_english` answers).
- **Aggregation from items, not from the LLM's separate skill_scores field.** We average each skill across every item that tested it; this is more reliable than trusting the LLM to do the same math.

The result is an honest skill profile after a five-minute diagnostic that genuinely reflects what the student can do, including credit for understanding-without-implementation.

### 3.9.8 Dynamic Hints

The hint generator (`backend/app/llm/hint_generator.py`) is the simplest LLM path but the one with the most direct teaching impact. It reads the problem, two sample cases, the student's *current* in-progress code, and the requested escalation level. The system prompt enforces escalation discipline: Level 1 is one sentence pointing at the family of approach without naming the algorithm; Level 2 names the algorithm and the key invariant; Level 3 may include 2–3 lines of pseudocode but never a full solution.

The student-specificity is what makes this useful. Two students stuck on Container With Most Water — one with a correct two-pointer skeleton but the wrong move-direction, one with an O(n²) nested loop — receive completely different hints: the first is told *"You're moving the wrong pointer — try moving the pointer with the strictly smaller height,"* the second is told *"Your O(n²) nested approach will time out at the constraint of 10⁵ elements; consider how a two-pointer walk could find the answer in linear time."*

## 3.10 Deployment

The system is deployed on an **AWS EC2 t3.small instance** running Windows Server 2025. Deployment is automated by two PowerShell scripts in `deploy/`.

**`bootstrap-ec2.ps1`** runs once on a fresh EC2 and: installs Chocolatey, Python 3.11, Node.js LTS, MariaDB 11, and NSSM; opens Windows Firewall port 80; sets the MariaDB root password and restores `database/dump.sql` (or applies `schema.sql` + `seed_problems.sql` + `seed_users.sql`); creates the Python venv and installs `requirements.txt`; runs `npm install --legacy-peer-deps && npm run build`; writes a production `.env` with `DATABASE_URL`, `JWT_SECRET` (random 48-byte base64), `GOOGLE_API_KEY`, `LLM_MODEL=gemini-2.5-flash`, `ALLOW_REGISTRATION=false`, and `FRONTEND_DIST=<dist path>`; and registers uvicorn as a Windows service named `ai-tutor` via NSSM (auto-start on boot, with rotating stdout/stderr logs).

**`enable-https.ps1`** runs once after a domain is pointed at the EC2's Elastic IP and: installs Caddy via Chocolatey; opens Firewall ports 80 and 443; moves uvicorn from `0.0.0.0:80` to `127.0.0.1:8001` (loopback-only — so the only internet-exposed ports become 80 and 443); patches `CORS_ORIGINS` in `.env` to the HTTPS URL; writes a Caddyfile that reverse-proxies to `127.0.0.1:8001` with `flush_interval -1` (so SSE streams are not buffered); and registers Caddy as its own Windows service. The first request triggers Caddy's automatic Let's Encrypt cert acquisition over the HTTP-01 challenge.

The live system is at <https://smartcodelau.com/> (also reachable at <https://lau-ai-tutor.duckdns.org/>, the original free DuckDNS subdomain). Both hostnames point at the same EC2 Elastic IP and share a single Caddy site block, so every deploy lands on both URLs simultaneously and the Let's Encrypt cert covers both Subject Alternative Names. The `.com` registration was added during beta testing after some users hit institutional Wi-Fi filters that blocked `*.duckdns.org` as "Dynamic DNS" (Beta finding B5, §4.5.2). Certificate renewal is fully automated by Caddy and requires zero ongoing maintenance.

[FIGURE 12: Deployment topology diagram — Browser <-HTTPS-> Caddy:443 (Let's Encrypt) -> uvicorn:8001 (loopback) -> FastAPI -> { MariaDB:3306 (localhost), Gemini API (HTTPS outbound), Python subprocess sandbox }. Show AWS Security Group rules: TCP 80 + 443 inbound from 0.0.0.0/0; everything else closed.]

# 4 Experimental Evaluation

To validate both the functional and the non-functional requirements we split the evaluation into three parts. The first part is **automated unit and integration testing** of the core scoring and skill-update logic. The second part is **end-to-end manual testing** against the live deployment, exercising every user-facing path. The third part is **performance measurement** under representative load.

## 4.1 Automated Testing

The most important pieces of the backend — the scoring penalty math, the AST cheater detection, the diagnostic post-processing, and the sandbox output canonicalization — are covered by isolated unit tests using `pytest`. The tests run against an in-memory representation of the inputs (no live MariaDB, no live LLM) and assert deterministic outputs.

[TABLE 1: Unit test coverage matrix — rows are modules (submissions router penalty logic, submission_evaluator cheater backstop, sandbox canonicalization, diagnostic_grader plain-English caps, recommender heuristic fallback), columns are { tests written, tests passing, coverage % }. Numbers TBD after the formal test pass.]

The AST cheater backstop has dedicated test cases for each known coincidence pattern:

- `class Solution: def twoSum(self, nums, target): return [0, 1]` — flagged (parameter-ignoring).
- `class Solution: def isValid(self, s): return True` — flagged (constant return).
- `class Solution: def climbStairs(self, n): if n == 1: return 1; elif n == 2: return 2; elif n == 3: return 3; return 5` — currently NOT flagged by the AST check (the LLM grader catches it instead). This is an intentional choice: the AST is the deterministic backstop for the simplest cases; the LLM handles enumerated-lookup style cheating because the threshold for "enumerated" is fuzzy and the LLM is better at the judgment call.

## 4.2 End-to-End Manual Testing

We ran the full happy-path scenario against the live deployment with each of the four seeded student accounts (alice@, bob@, carla@, daniel@; all password `Test1234`) plus the admin account (admin@example.com). For each scenario we recorded whether the expected outcome occurred and, where applicable, captured a screenshot.

### Scenario 1 — New student first session

1. Register a new account at <https://lau-ai-tutor.duckdns.org/register>. Expected: 201, JWT received, redirect to `/diagnostic`. Result: PASS.
2. Complete the five-question diagnostic with a mix of real Python and plain-English answers. Expected: AI grades each item, shows per-item explanations, redirects to `/dashboard`. Result: PASS.
3. Verify the dashboard radar reflects the diagnostic scores and that a "Next Problem" card is visible. Result: PASS.

### Scenario 2 — Problem attempt with hints

1. Open the recommended problem in the editor. Expected: Monaco editor loads with the starter code and the sample test cases are visible. Result: PASS.
2. Click "Get Hint" three times. Expected: three escalating hints (nudge → direction → concrete pseudocode), all tailored to the in-editor code. Result: PASS.
3. Click "Run". Expected: visible cases execute in the sandbox; pass/fail rendered with predicted-vs-expected output. Result: PASS.
4. Click "Submit" with a correct solution. Expected: 201 with a SubmissionDetail showing per-case verdicts, AI bullets, per-skill deltas, and the next-problem recommendation. The final score should reflect the hint penalty. Result: PASS.

### Scenario 3 — Coincidence-solution rejection

1. Submit `class Solution: def twoSum(self, nums, target): return [0, 1]` for Two Sum (this *would* pass the first sample case by coincidence). Expected: rejected as `wrong_answer`, every case marked severe failure, prominent warning bullet about hardcoded solutions. Result: PASS.

### Scenario 4 — Watch AI Solve

1. Open the Solutions tab on a solved problem; click "Watch AI Solve". Expected: a streamed markdown walkthrough appears word-by-word, following the seven fixed headings, with a fenced Python solution under the "Clean solution" heading. Result: PASS.

### Scenario 5 — Already-solved review mode

1. Re-open a solved problem in the editor. Expected: code is the accepted submission, Submit is disabled (any attempt returns 409). Result: PASS.

### Scenario 6 — Admin content management

1. Log in as `admin@example.com`; open the admin Problems screen; edit a problem's statement and save. Expected: 200, the change is visible in the student catalogue. Result: PASS.

### Scenario 7 — LLM offline degradation

1. Temporarily set `GOOGLE_API_KEY=""` in the production `.env` and restart the service. Repeat scenarios 2 and 3. Expected: the sandbox still grades correctness, the UI shows honest "AI grader offline" labels, and no endpoint returns 500. Result: PASS.

[TABLE 2: Full end-to-end scenario matrix — rows are the seven scenarios above, columns are { expected, actual, screenshot ref }. All scenarios passing in the most recent test run on the live deployment.]

## 4.3 Performance Measurement

We measured performance on the live EC2 (t3.small, 2 vCPU, 2 GB RAM, Windows Server 2025) using `wrk` for HTTP-level numbers and direct timing of representative interactive workflows from the browser.

The measurements below are placeholders pending the formal performance pass — the team must re-run these against the live deployment using the test scripts and record the actual numbers before the final submission.

[TABLE 3: Performance results — rows are endpoints (POST /api/auth/login, POST /api/diagnostic, POST /api/submissions accepted, POST /api/submissions wrong-answer, POST /api/problems/{id}/hint, GET /api/problems/{id}/ai-solution/stream first-byte, GET /api/me/skills), columns are { median latency, 95th percentile, max ms, sandbox subprocess count, LLM tokens consumed }. Numbers TBD.]

Indicative measurements from informal use during development:

- Login: comfortably under 100 ms median (bcrypt verify dominates).
- Diagnostic grading: 6–12 s median (single Gemini call grading all five items together).
- Submit on an easy problem: 3–7 s median (sandbox runs all cases in well under 1 s; Gemini grading is the long pole at 2–6 s).
- Hint: 1–3 s median (small Gemini call).
- Watch AI Solve first byte: under 1 s (Gemini streaming latency).

[FIGURE 13: Bar chart of median latency per endpoint, with error bars showing 95th percentile. Numbers TBD.]

These figures comfortably satisfy the SRS's non-functional target of "code evaluation results within 2 seconds for at least 90% of submissions" *when interpreted as sandbox latency*. The end-to-end Submit latency including the LLM exceeds 2 s for most submissions, which we view as an acceptable trade-off: the LLM-generated qualitative feedback is the product, and waiting 5 s for a paragraph of useful tutoring is far better than getting "Wrong Answer" in 200 ms.

## 4.4 LLM-Offline Robustness

A separate concern is that the LLM is the single hard external dependency. We deliberately structured every LLM path with a deterministic fallback so the system remains functional in degraded mode.

[TABLE 4: LLM-offline behavior matrix — rows are LLM-backed features (submission grading, diagnostic grading, hint generation, problem recommendation, canonical solution, live solve streaming), columns are { primary behavior, fallback behavior, user-visible signal }. Each row documents what happens when GOOGLE_API_KEY is unset or Gemini returns an error.]

Notable rows:

- **Submission grading.** Primary: sandbox + LLM qualitative. Fallback: sandbox-only with honest "AI grader offline" bullet — correctness is still graded by the sandbox, only the qualitative axes degrade.
- **Diagnostic grading.** Primary: LLM per-skill scoring with plain-English partial credit. Fallback: deterministic rule-based scorer (40 for short attempts, 70 for substantive attempts, 0 for blank).
- **Hint generation.** Primary: dynamic hint tailored to the student's code. Fallback: a generic level-appropriate canned hint with an explicit "AI hint engine is offline" disclosure.
- **Live solve streaming.** Primary: Gemini SSE stream. Fallback: a friendly error message — there is no useful offline behavior for a token-by-token live walkthrough.

## 4.5 Alpha and Beta Testing

In addition to the automated unit tests, the end-to-end scenarios, and the performance measurements, SmartCode went through two informal testing phases that produced specific bug fixes and feature additions. We distinguish them by *who* the testers were and *when* they ran: **alpha tests** were carried out by the four authors against a local-development build before any external user saw the system, and **beta tests** were carried out by classmates and friends against the deployed site after the team had signed off on the alpha. The two phases produced complementary findings — alpha exposed correctness and security issues, beta exposed pedagogical and user-experience issues that were invisible to the authors because we already knew how the system was supposed to behave.

### 4.5.1 Alpha Testing — Internal, Pre-Deployment

The alpha pass was run on each developer's local machine against the dev `npm run dev` + uvicorn stack. Each finding listed below was reproduced by at least one other team member and turned into a concrete fix in the codebase before the first public deployment.

**A1. Weak passwords were being accepted at registration.** The original `/api/auth/register` endpoint only enforced a minimum length of 8 characters, so passwords like `12345678`, `password`, and `qwerty12` registered successfully. The fix added an explicit strength check in `backend/app/schemas.py::_validate_strong_password()`: the password must contain at least one lowercase letter, one uppercase letter, and one digit, **and** must not appear in a 28-entry blacklist of the most commonly used weak passwords (`password`, `12345678`, `qwerty12`, `letmein`, etc.). The same check is applied to admin-created accounts via `AdminUserCreate`. The registration screen was updated to show live ✓/✗ indicators for each rule and a red warning banner when the typed password matches the blacklist, so the rejection reason is visible *before* the user submits.

**A2. Lucky-coincidence solutions were being marked correct.** During internal grading testing one team member submitted `class Solution: def twoSum(self, nums, target): return [0, 1]` for Two Sum. The LLM-only evaluator marked it accepted because the first sample case happened to expect `[0, 1]`. The fix is the AST cheater backstop described in §3.9.2: `_detect_lucky_coincidence()` parses the submission, finds the longest method on the `Solution` class, and flags it if the body is a single `return <literal>` or if the method never references any of its parameters. When either pattern matches, the system *overrides* the evaluator output — every test case becomes severe failure, the status becomes `wrong_answer`, and a prominent warning bullet is shown. The same logic was also added to the LLM grader's system prompt as a backup pattern check.

**A3. Buggy code passed because the LLM evaluator hallucinated correctness.** A team member's intentionally-broken Group Anagrams solution (`if key in groups: groups[key] = []`, which clobbers existing groups instead of appending to them) was being marked accepted by the LLM-only grader, which "mentally executed" the code wrongly. The fix made the **sandbox authoritative for correctness** (§3.9.1): every submission now runs in a real Python subprocess against the visible *and* hidden cases first, and only then does the LLM provide qualitative commentary on top. The router's `_overlay_sandbox()` forcibly replaces every case's `passed` field with the sandbox verdict so the LLM cannot lie about correctness even if it tries.

**A4. Submissions with any failing case were still being labeled "accepted" by an early version of the evaluator.** A submission that passed five of seven cases would receive a partial score and "accepted" status. We tightened the rule to: **the only path to `accepted` is all-pass**, and the failed-attempts penalty (§3.9.3) now uses the per-case severity points to differentiate "wrong on a hidden edge case" (minor) from "runtime error on the sample case" (severe). The submission detail page exposes the breakdown in plain English so the student understands exactly what cost them what.

**A5. A solved problem could be re-opened in edit mode and accidentally re-submitted.** Once a student accepts a problem we want to lock it down so they cannot accidentally lose their accepted score on a careless re-submit. The fix added a `_block_if_solved()` guard on Run, Run-with-AI, and Submit: a 409 Conflict is returned if a `ProblemStatus.status='solved'` row already exists for `(user, problem)`. The editor screen detects this state and renders in **read-only review mode**: the code editor displays the accepted source, the action buttons are hidden, and a "Solved" badge is shown.

**A6. The Submissions tab was empty even after multiple submit attempts.** A team member submitted a problem three times and the Submissions list rendered as blank. The fix surfaces every `Submission(kind='submit')` for the (user, problem) pair through `GET /api/problems/{id}/my-submissions`, ordered newest-first, with status, score, and a "View" link to the per-submission feedback page. Failed Run attempts (`kind='run'`) are intentionally hidden from this view — they exist only to feed the severity-points penalty and would clutter the student's history if shown.

### 4.5.2 Beta Testing — External Users, Post-Deployment

After the alpha sign-off the system was deployed to AWS EC2 and the URL was shared with classmates and friends. Beta findings came from real first-time users hitting the site, and several were issues that the authors could not have surfaced on our own because we already knew the intended flow. Each finding below was reproduced from a friend's report and turned into a deployed fix.

**B1. Diagnostic gate could be bypassed.** A friend reported that after registering a brand-new account they could navigate directly to `/problems` and `/dashboard` without completing the diagnostic, which broke the personalization premise. Investigation revealed that the bypass only happened in their browser, not in incognito — Chrome had cached an old `index.html` from before the route guard existed, and the cached JS still treated the diagnostic as optional. The fix has three layers, applied at three different points in the pipeline:

  1. **React route guard.** A `<DiagnosticGate>` component on every student route checks `hasCompletedDiagnostic` and redirects to `/diagnostic` if the user has not completed it.
  2. **Server-side dependency.** A `require_diagnostic_complete` FastAPI dependency was added to `/api/problems/*`, `/api/submissions/*`, `/api/me/skills`, and `/api/me/recommendations`. A fresh student without a completed diagnostic now receives 403 from those endpoints regardless of which client they use.
  3. **Cache-Control header.** `index.html` is now served with `Cache-Control: no-store, max-age=0, must-revalidate` so browsers cannot keep an obsolete version of the SPA after a redeploy. The hashed `/assets/*` files remain freely cacheable because their filenames change per build.

  After the fix, the same friend retested on the same machine (without clearing cache manually) and was correctly redirected to `/diagnostic`.

**B2. Only one next-problem recommendation felt restrictive.** Multiple beta users said that when the dashboard surfaces a single recommended problem, they sometimes ignored it and went hunting through the catalogue — they wanted *options*. The fix described in §3.8.7 expanded the recommender to return three picks ordered best → good-fallback, with the LLM prompt nudged to diversify across weak skills and difficulty. On the UI, the post-diagnostic review screen, the dashboard "Recommended for you" panel, and the post-submit feedback screen all became a three-card grid: a gradient "Top pick" and two white-bordered "Option 2 / Option 3" tiles. After the deploy, follow-up beta sessions showed users actually clicking the alternative tiles when the top pick didn't match their mood, which was the desired behavior.

**B3. Students stalled on Python syntax recall rather than on the algorithm.** A friend who clearly understood the algorithm for Valid Parentheses spent five minutes searching online for how to peek at the top of a Python list. We added the **per-problem cheatsheet drawer** described in §3.8.6: a slide-in left panel containing only the Python syntax that *this specific problem* needs, generated once per problem by Gemini using the problem statement as input. Beta users who came back after the deploy commented that the drawer "feels like a w3schools tab pinned to the page" and reported solving problems faster.

**B4. The AI walkthrough lectured instead of teaching.** Beta users watched the one-shot "Watch AI Solve" stream to the end, said "ok, cool" and forgot most of it within an hour. The pedagogical signal was that *the student was passive*. The fix (§3.8.4) replaced the one-shot stream with an **interactive step-by-step tutor**: six guided steps with a comprehension question after each, where the LLM evaluates the student's reply and decides whether to advance or re-explain. Beta follow-up showed students actually working through the steps and admitting they retained more.

**B5. FortiGuard-style content filtering blocked the original `*.duckdns.org` URL.** Some beta users on institutional Wi-Fi (the LAU campus network, in particular) reported the deployed site was outright blocked as "Dynamic DNS". The fix was operational rather than code-level: we registered a real `.com` domain (`smartcodelau.com`) at Cloudflare Registrar and configured Caddy to serve **both** `smartcodelau.com` and `lau-ai-tutor.duckdns.org` from the same site block. Friends already in possession of the old DuckDNS link kept access, and new users on networks that block dynamic-DNS hostnames now have a working alternative. The patched `enable-https.ps1` accepts a comma-separated `-Domain` list so any future domain can be added with one redeploy.

**B6. The catalogue felt too small.** A beta user solved six problems in a sitting and reached the end of the original 15. We expanded to 55 problems (§3.8.5) so beta users have enough material to actually build a streak.

### 4.5.3 Summary Table

| Phase | Finding | Fix shipped |
| --- | --- | --- |
| Alpha | Weak passwords accepted (A1) | Strong-password validator + blacklist + live UI indicators |
| Alpha | Lucky-coincidence solutions accepted (A2) | AST cheater backstop + LLM prompt rule |
| Alpha | LLM-only grader hallucinated correctness (A3) | Sandbox-first evaluator with LLM overlay |
| Alpha | Partial-pass marked as accepted (A4) | All-pass-or-fail rule + severity-weighted penalty |
| Alpha | Solved problem re-submittable (A5) | `_block_if_solved` guard + read-only editor mode |
| Alpha | Submissions tab empty (A6) | `GET /my-submissions` + tab rendering |
| Beta | Diagnostic gate bypass via cached SPA (B1) | Route guard + server-side dep + `Cache-Control: no-store` |
| Beta | Only one next-problem recommendation (B2) | 3-pick recommender + three-card UI everywhere |
| Beta | Students stalled on syntax recall (B3) | Per-problem Gemini-generated cheatsheet drawer |
| Beta | One-shot AI walkthrough was passive (B4) | Interactive 6-step tutor with comprehension checks |
| Beta | `*.duckdns.org` blocked on some networks (B5) | Registered `smartcodelau.com`; Caddy serves both |
| Beta | 15-problem catalogue too small (B6) | Expanded to 55 problems with full sandbox coverage |

The combination of A1–A6 (correctness + security) and B1–B6 (pedagogy + UX) is what took SmartCode from "the team thinks it works" to "real students keep coming back". The two phases were equally indispensable: alpha caught the bugs that would have made the system embarrassing in front of the grader, beta caught the pedagogical and UX gaps that would have made it forgettable. In retrospect, the most useful single decision was *deploying early* so beta could happen at all; an unshipped system collects no real-user feedback.

# 5 Conclusion

Throughout this report we have introduced the AI Programming Tutor, a web-based adaptive Python tutor that combines deterministic code execution with a state-of-the-art LLM to give students grading, hints, recommendations, and live solution walkthroughs that are tailored to their individual skill profile. The first stage of the project was a simple proposal in Submission 1 that laid out the idea. Submission 2 (the SRS) formalized the functional and non-functional requirements, the use-case model, and an Appendix B with a 21-table schema. Submission 3 (the agile workflow progress report) tracked our sprints through April and early May using JIRA, including the design decision to consolidate three tracks into a single Problem-Solving track. This final Submission 4 documents the working system end-to-end: deployed, public, HTTPS-enabled, and demonstrable.

The architecture is small enough to fit on a single t3.small EC2 and rich enough to deliver a personalized experience that no commercial alternative provides. The seventeen-table MariaDB schema captures the entire student journey from the first diagnostic answer through every submission, hint, and skill update. The FastAPI backend serves both the JSON API and the React SPA from a single process, with Caddy in front handling HTTPS and Let's Encrypt automatically. The Python sandbox grades correctness deterministically; the LLM grades everything else (severity, code quality, edge cases, complexity, the inferred Big-O, and the natural-language feedback). The AST cheater backstop catches `return 5`-style coincidences that an LLM might miss. The failed-attempts penalty, hint penalty, and final-score clamp keep the scoring honest *and* motivating. The skill-update math is difficulty-weighted, efficiency-scaled, capped per submission, and floored at zero so a bad attempt never erases progress. The recommender closes the loop by surfacing a next problem that targets the student's *current* weakest skills.

Developing the system was a substantial undertaking. From the early stages of implementation — even from picking which features to keep when the original three-track design proved more elaborate than the timeline supported — we came to realize that managing a software project end-to-end is a different discipline from writing one component well. Adhering to an agile workflow, defining requirements ahead of code, and persisting the discipline of writing a deterministic fallback for every LLM call were all new habits for us. The fallback discipline in particular turned out to be the single most important design decision: a system whose only behavior is "the LLM does it" is unusable in the inevitable Gemini outage; a system that grades correctness with a real interpreter and reaches for the LLM only for qualitative judgement is robust by construction.

The clear-cut requirements document made it materially easier to make the dozens of small architectural decisions that surfaced during implementation — knowing exactly which behaviors were in scope and which were out of scope meant we could de-scope the three-track concept, the `code_snapshots` table, and the Debugging skill without losing sleep over whether we were cutting something the grader expected. Implementing a thorough testing protocol — automated unit tests for the scoring math, manual scenarios for every screen, and an explicit LLM-offline scenario — proved to be far more important than we appreciated when the subject was first introduced.

Overall, we believe this project has exposed us to many of the practices that accompany the work of a software engineer in industry: writing an SRS and then building against it, managing scope, designing for failure of external dependencies, deploying behind a reverse proxy with automated HTTPS, structuring an agile workflow in JIRA, and writing code that is meant to be read by collaborators rather than only by the author. We are hopeful this will prepare us to enter the workforce with more experience and confidence in the future.

The system is publicly accessible at <https://lau-ai-tutor.duckdns.org/>. Future versions could extend support to JavaScript and C++ (the sandbox and the LLM grader are language-agnostic in design), introduce per-user notification when new problems are added, add a containerized seccomp-isolated sandbox for an externally-exposed deployment, and surface aggregate teacher-side analytics (which problems trip up the most students, which skills are most often weak, etc.).

---

# 6 References

[1] FastAPI — modern, fast (high-performance) web framework for building APIs with Python. <https://fastapi.tiangolo.com/>

[2] SQLAlchemy — the Python SQL toolkit and Object Relational Mapper. <https://www.sqlalchemy.org/>

[3] React — a JavaScript library for building user interfaces. <https://react.dev/>

[4] Vite — next-generation frontend build tool. <https://vitejs.dev/>

[5] Tailwind CSS — utility-first CSS framework. <https://tailwindcss.com/>

[6] Monaco Editor — the code editor that powers Visual Studio Code. <https://microsoft.github.io/monaco-editor/>

[7] Google AI for Developers — Gemini API reference. <https://ai.google.dev/>

[8] MariaDB — open source relational database. <https://mariadb.org/>

[9] Caddy — automatic HTTPS web server. <https://caddyserver.com/>

[10] Let's Encrypt — free, automated, and open certificate authority. <https://letsencrypt.org/>

[11] IEEE Software Engineering Standards Committee, "IEEE Std 830-1998, IEEE Recommended Practice for Software Requirements Specifications," October 20, 1998.

[12] Ian Sommerville, *Software Engineering*, 9th Edition, Pearson, 2011.

---

# 7 Appendix A — Submission 4 Checklist

| Submission 4 requirement | Where addressed |
| --- | --- |
| Introduction: subject and objective(s) of the project | Section 1 |
| Background: context, prerequisites, and existing solutions | Section 2 |
| Proposal — underlying concepts and building blocks | Sections 3.1, 3.3 |
| Proposal — requirements specification | Section 3.2 (user) and Section 3.4 (system) |
| Proposal — design models (use case, process, sequence, class, ERD) | Sections 3.5, 3.6, 3.7 |
| Proposal — implementation (frontend, backend, AI, sandbox, deployment) | Section 3.8 |
| Proposal — novel scoring and skill-update system | Section 3.9 |
| Experimental evaluation — test protocol | Sections 4.1, 4.2, 4.5 |
| Experimental evaluation — test metrics | Section 4.3 tables; §4.5.3 alpha/beta summary table |
| Experimental evaluation — test data | Section 4.2 scenarios + §4.5 alpha + beta findings |
| Experimental evaluation — experimental results | Sections 4.3, 4.4, 4.5 |
| Alpha + beta testing — internal pre-deploy + external post-deploy | Section 4.5 (A1–A6, B1–B6) |
| Conclusion — synthesis, personal experience, perspectives | Section 5 |
| Source code | Provided alongside report; live at <https://github.com/darwishmohammad433-droid/AI-Tutor-system> |
| Working deployment | <https://lau-ai-tutor.duckdns.org/> |
| 15–20 page final report following IEEE Computer Society Transactions style | This document |
| Final project presentation (20 min, 5 per member) | Scheduled separately by the instructor |
| De-scoped items documented (3 tracks → 1; 21 → 17 tables; Debugging skill dropped; diagnostic redesigned) | Section 3.8.1 |
