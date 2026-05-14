"""
One-shot generator: ask Gemini to author a focused Python syntax cheatsheet
for every problem in the catalogue. Stores the result on `problems.cheatsheet_md`
AND writes a portable seed_cheatsheets.sql file for deployment.

Usage (from backend/ with the venv activated):
    python scripts/generate_cheatsheets.py                 # generates only missing
    python scripts/generate_cheatsheets.py --force         # regenerate everything
    python scripts/generate_cheatsheets.py --slug two-sum  # one problem
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make `app.*` imports work when this script is run from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.llm import client as llm_client
from app.models import Problem, ProblemSkill, Skill


SYSTEM_PROMPT = """You generate focused Python 3 syntax cheatsheets for programming-problem solvers.

Style: like the right-hand panel on w3schools - a tiny, scannable reference. NO prose explanations. ONLY the Python primitives the student needs to solve the SPECIFIC problem at hand. Imagine the student forgot Python syntax but already knows the algorithm.

Strict format (Markdown):
- 3 to 6 short sections.
- Each section header: `## <short topic>` (e.g. `## Stack`, `## Dictionary`, `## Two pointers`).
- Under each header: ONE python fenced code block with 3-7 short lines.
- Each code line should be a minimal snippet (1 statement) plus, optionally, a trailing `# brief comment`.
- NO extra paragraphs, NO bullet text outside code, NO closing summary.
- ALWAYS use real Python 3 syntax that runs.

What to include: only what THIS problem needs. If the problem is about strings, do NOT include trees. If it needs a stack, include stack ops, not heaps. Skip imports unless the problem actually needs them (e.g. heapq, collections.deque, Counter, bisect).

Output ONLY the Markdown - no JSON wrapping, no triple backticks around the whole thing, no preamble like "Here is...". Start directly with `## <heading>`."""


def build_user_prompt(problem: Problem, skills: list[str]) -> str:
    return (
        f"Problem: {problem.title} ({problem.difficulty})\n"
        f"Skills it trains: {', '.join(skills) or 'general'}\n\n"
        f"Statement:\n{problem.statement_md}\n\n"
        f"Constraints:\n{problem.constraints_md or '(none)'}\n\n"
        f"Starter code:\n{problem.starter_code_md or '(none)'}\n\n"
        "Write the Python syntax cheatsheet for this problem now."
    )


def gen_one(problem: Problem, skills: list[str]) -> str:
    """Call Gemini. Returns the markdown body. Raises on failure."""
    user_text = build_user_prompt(problem, skills)
    # The shared client has a JSON helper but we want plain text here, so we use the SDK directly.
    from google import genai
    from google.genai import types as gtypes

    sdk = genai.Client(api_key=settings.google_api_key)
    resp = sdk.models.generate_content(
        model=settings.llm_model,
        contents=user_text,
        config=gtypes.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            thinking_config=gtypes.ThinkingConfig(thinking_budget=0),
            max_output_tokens=1024,
        ),
    )
    text = (resp.text or "").strip()
    # Strip accidental ```markdown wrappers
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text.startswith("##"):
        raise ValueError(f"Cheatsheet for {problem.slug} doesn't start with `##`")
    return text


def sql_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Regenerate even where one exists")
    ap.add_argument("--slug", help="Only process this slug")
    ap.add_argument("--out", default="database/seed_cheatsheets.sql",
                    help="Where to write the portable UPDATE batch (relative to repo root)")
    args = ap.parse_args()

    if not llm_client.is_available():
        print("ERROR: GOOGLE_API_KEY not set or empty. Cannot call Gemini.", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        q = select(Problem).order_by(Problem.problem_id)
        if args.slug:
            q = q.where(Problem.slug == args.slug)
        problems = db.scalars(q).all()
        if not problems:
            print("No problems matched.")
            return 0

        # Pre-fetch skill names so we don't N+1 query
        skills_by_pid: dict[int, list[str]] = {}
        for pid, name in db.execute(
            select(ProblemSkill.problem_id, Skill.name)
            .join(Skill, Skill.skill_id == ProblemSkill.skill_id)
            .order_by(Skill.display_order)
        ).all():
            skills_by_pid.setdefault(pid, []).append(name)

        generated: list[tuple[int, str]] = []
        skipped = 0
        for p in problems:
            if p.cheatsheet_md and not args.force:
                skipped += 1
                continue
            print(f"  generating #{p.problem_id} {p.slug} ...", end="", flush=True)
            try:
                md = gen_one(p, skills_by_pid.get(p.problem_id, []))
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL: {exc}")
                continue
            p.cheatsheet_md = md
            db.add(p)
            db.flush()
            generated.append((p.problem_id, md))
            print(f"  ok ({len(md)} chars)")
            time.sleep(0.4)  # gentle on free-tier rate limits

        db.commit()

        # Write the portable SQL file (all rows, even ones we didn't regenerate
        # this run, so the file is the canonical source of truth)
        rows = db.execute(
            select(Problem.problem_id, Problem.slug, Problem.cheatsheet_md)
            .where(Problem.cheatsheet_md.isnot(None))
            .order_by(Problem.problem_id)
        ).all()
        out_path = Path(__file__).resolve().parent.parent.parent / args.out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("-- =========================================================\n")
            f.write("-- SmartCode - per-problem Python syntax cheatsheets\n")
            f.write("-- Auto-generated by backend/scripts/generate_cheatsheets.py\n")
            f.write("-- Safe to re-run; idempotent UPDATE per row.\n")
            f.write("-- =========================================================\n\n")
            f.write("USE ai_tutor_system;\n\n")
            for pid, slug, md in rows:
                escaped = sql_escape(md)
                f.write(f"-- #{pid} {slug}\n")
                f.write(f"UPDATE problems SET cheatsheet_md = '{escaped}' WHERE problem_id = {pid};\n\n")

        print(f"\nGenerated: {len(generated)}  Skipped (already had one): {skipped}")
        print(f"Wrote portable SQL: {out_path}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
