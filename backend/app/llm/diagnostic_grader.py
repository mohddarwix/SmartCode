"""
LLM-driven diagnostic grader.

Inputs: the questions the user just answered (question text, skill, type, the
user's answer, and the canonical correct answer for MCQs).

Outputs:
  - per-item: is_correct, score, an explanation of the mistake/right answer
  - per-skill score (0-100), used to populate user_skill
  - overall_score and summary_md (shown on the review screen)
  - 2-3 weak_skills (drives the follow-up problem recommendation)

If the LLM is unavailable or returns garbage we degrade to a deterministic
heuristic so the diagnostic always completes.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel

from . import client as llm_client

log = logging.getLogger("ai_tutor.llm.diagnostic")


class DiagnosticItemInput(BaseModel):
    order_index: int
    skill: str  # primary skill (kept for labels)
    tested_skills: list[str] = []  # all skills the item exercises; defaults to [skill]
    type: Literal["mcq", "coding"]
    question: str
    user_answer: str
    correct_answer: str | None = None  # set for MCQs; None for coding


class DiagnosticItemResult(BaseModel):
    order_index: int
    is_correct: bool
    score: int  # 0-100 overall
    per_skill_scores: dict[str, int] = {}  # for each tested_skill: 0-100
    answer_kind: Literal["code", "pseudo_english", "blank"] = "code"
    explanation_md: str
    correct_answer: str | None = None


class DiagnosticResult(BaseModel):
    items: list[DiagnosticItemResult]
    skill_scores: dict[str, int]  # skill_name -> 0..100 (averaged across items)
    overall_score: int  # 0..100
    summary_md: str
    weak_skills: list[str]  # 2-3 weakest skills, sorted weakest-first
    source: Literal["llm", "heuristic"]


_SYSTEM_PROMPT = """You are the evaluation engine for an adaptive programming tutor. Students sit a short diagnostic of small coding questions across these five skills:

- Algorithms — algorithmic problem solving and pattern recognition
- Data Structures — arrays, lists, trees, graphs, hash tables, heaps
- Edge Cases — identifying and handling boundary conditions
- Code Quality — readability, naming, structure, idiomatic style
- Time Complexity — analyzing asymptotic behavior

Each item lists `tested_skills` — the skills the question exercises (a single coding question typically tests several at once). For every item, grade it along EACH of its tested skills separately.

For each item produce:
  1) `is_correct` — bool. True only if the solution is essentially right (correct logic + handles obvious edges).
  2) `score` — overall 0-100 (rough average across the skills this item tests).
  3) `per_skill_scores` — a map from EACH tested skill name to its own 0-100 score for this item. Score independently:
       - Algorithms / Data Structures: did they pick the right approach? Right structure used correctly?
       - Edge Cases: empty / single-element / duplicate / overflow input handling.
       - Code Quality: naming, structure, idiomatic Python (don't conflate with correctness).
       - Time Complexity: is the asymptotic behavior appropriate for the constraints? Penalize O(n^2) when problem demands sub-quadratic.
  4) `answer_kind` — one of:
       - "code"           : the student wrote real, runnable (or near-runnable) Python.
       - "pseudo_english" : the student wrote plain English / pseudocode / commentary rather than runnable code.
       - "blank"          : the student left the answer empty or only the placeholder/stub.
  5) `explanation_md` — 2-4 sentences pointing at specific bugs / missed edges / complexity issues, and a corrected one-liner sketch if useful.

PLAIN ENGLISH / PSEUDOCODE RULE — VERY IMPORTANT:
If `answer_kind == "pseudo_english"`, do NOT give zero. Award partial credit based on conceptual understanding:
  - `score_code_quality`: very LOW (0-25). Real code wasn't written.
  - Algorithms / Data Structures / Edge Cases / Time Complexity: judge ONLY by whether the English description shows correct understanding. A clear, correct algorithm explanation with the right complexity discussion can earn 50-75 on those axes even with zero code.
  - Set `is_correct = false` (since it's not a working solution) but reflect partial mastery in per_skill_scores.

BLANK / STUB RULE: `answer_kind == "blank"` gets per_skill_scores all 0 and a one-line "no answer submitted" explanation.

Then aggregate across all items:
  - `skill_scores`: for each skill, average that skill's per-item per_skill_scores across every item that tested it. Omit skills no item tested.
  - `overall_score`: weighted average of per-item `score` values.
  - `summary_md`: 2-3 sentence written feedback identifying strengths and the most important gaps.
  - `weak_skills`: 2 or 3 skill names ordered weakest first, used to pick the next problem.

Respond with a single JSON object - no prose, no code fences. Schema:

{
  "items": [
    {
      "order_index": int,
      "is_correct": bool,
      "score": int,
      "per_skill_scores": {"Skill Name": int, ...},
      "answer_kind": "code" | "pseudo_english" | "blank",
      "explanation_md": str,
      "correct_answer": str | null
    }
  ],
  "skill_scores": {"Skill Name": int, ...},
  "overall_score": int,
  "summary_md": str,
  "weak_skills": [str, str, str]
}

Be encouraging but precise. Never punish the student to zero for trying — empty answers get zero, attempts always get something."""


def grade_diagnostic(items: list[DiagnosticItemInput]) -> DiagnosticResult:
    """Try the LLM grader; fall back to a deterministic heuristic on any failure."""
    if llm_client.is_available():
        try:
            return _grade_with_llm(items)
        except Exception as exc:  # noqa: BLE001 - we want to swallow everything here
            log.warning(
                "LLM diagnostic grading failed, falling back to heuristic: %s", exc
            )
    return _grade_with_heuristic(items)


# --------------------------- LLM path ---------------------------


def _grade_with_llm(items: list[DiagnosticItemInput]) -> DiagnosticResult:
    user_text = _build_user_prompt(items)
    raw = llm_client.call_json(system=_SYSTEM_PROMPT, user=user_text, max_tokens=4096)
    return _coerce_result(raw, items, source="llm")


def _build_user_prompt(items: list[DiagnosticItemInput]) -> str:
    lines = ["Student answers:\n"]
    for item in items:
        skills = item.tested_skills or [item.skill]
        lines.append(
            f"### Item {item.order_index} "
            f"(Primary skill: {item.skill}; Tested skills: {', '.join(skills)}; Type: {item.type})"
        )
        lines.append(f"Question: {item.question}")
        lines.append(f"User answer:\n```\n{item.user_answer or '(blank)'}\n```")
        if item.correct_answer is not None:
            lines.append(f"Correct answer (canonical): {item.correct_answer}")
        lines.append("")
    lines.append("Now respond with the JSON object specified in your instructions.")
    return "\n".join(lines)


def _coerce_result(
    raw: dict[str, Any],
    inputs: list[DiagnosticItemInput],
    *,
    source: Literal["llm", "heuristic"],
) -> DiagnosticResult:
    """Pull the JSON we got back into our DiagnosticResult shape, filling gaps."""
    items_by_index = {item.order_index: item for item in inputs}
    items_out: list[DiagnosticItemResult] = []

    for entry in raw.get("items") or []:
        try:
            idx = int(entry.get("order_index"))
        except (TypeError, ValueError):
            continue
        if idx not in items_by_index:
            continue

        # per_skill_scores: only keep skills the input claimed this item tests
        inp = items_by_index[idx]
        tested = set(inp.tested_skills or [inp.skill])
        per_skill_raw = entry.get("per_skill_scores") or {}
        per_skill = {
            str(k): _clamp_int(v, 0, 100)
            for k, v in per_skill_raw.items()
            if str(k) in tested
        }

        answer_kind = entry.get("answer_kind")
        if answer_kind not in ("code", "pseudo_english", "blank"):
            # Heuristic backstop if LLM forgot the label
            ans = (inp.user_answer or "").strip()
            if not ans:
                answer_kind = "blank"
            elif "def " not in ans and "return" not in ans:
                answer_kind = "pseudo_english"
            else:
                answer_kind = "code"

        # Hard caps the LLM tends to violate even when told.
        if answer_kind == "pseudo_english":
            # Plain English / pseudocode → Code Quality must be very low.
            if "Code Quality" in per_skill:
                per_skill["Code Quality"] = min(per_skill["Code Quality"], 25)
        elif answer_kind == "blank":
            # Blank answer → every tested skill is zero, no exceptions.
            per_skill = {k: 0 for k in per_skill}

        items_out.append(
            DiagnosticItemResult(
                order_index=idx,
                is_correct=bool(entry.get("is_correct", False)),
                score=_clamp_int(entry.get("score"), 0, 100),
                per_skill_scores=per_skill,
                answer_kind=answer_kind,
                explanation_md=str(entry.get("explanation_md") or ""),
                correct_answer=entry.get("correct_answer") or inp.correct_answer,
            )
        )

    # Ensure every input has a row (LLM may have dropped some)
    seen = {r.order_index for r in items_out}
    for inp in inputs:
        if inp.order_index in seen:
            continue
        items_out.append(_default_item_result(inp))

    items_out.sort(key=lambda r: r.order_index)

    # Aggregate per-skill: average each skill's per-item per_skill_scores across
    # every item that tested it. Prefer LLM-provided skill_scores if present and
    # within range, but rebuild from items if missing or inconsistent.
    skill_scores: dict[str, int] = {}
    bucket: dict[str, list[int]] = {}
    for r in items_out:
        for skill, score in (r.per_skill_scores or {}).items():
            bucket.setdefault(skill, []).append(score)
    for skill, scores in bucket.items():
        skill_scores[skill] = round(sum(scores) / len(scores)) if scores else 0

    # Fall back to LLM-aggregated for any skill the per-item map didn't cover
    skill_scores_raw = raw.get("skill_scores") or {}
    for k, v in skill_scores_raw.items():
        skill_scores.setdefault(str(k), _clamp_int(v, 0, 100))

    overall_score = _clamp_int(
        raw.get("overall_score"),
        0,
        100,
        default=(
            round(sum(r.score for r in items_out) / len(items_out)) if items_out else 0
        ),
    )
    summary = str(raw.get("summary_md") or "")
    weak_skills_raw = raw.get("weak_skills") or []
    weak_skills = [str(s) for s in weak_skills_raw if isinstance(s, str)]
    if not weak_skills:
        weak_skills = _compute_weak_skills(skill_scores)

    return DiagnosticResult(
        items=items_out,
        skill_scores=skill_scores,
        overall_score=overall_score,
        summary_md=summary or "Diagnostic complete.",
        weak_skills=weak_skills[:3],
        source=source,
    )


# --------------------------- Heuristic fallback ---------------------------


def _grade_with_heuristic(items: list[DiagnosticItemInput]) -> DiagnosticResult:
    """No-LLM grader. Crude but never explodes."""
    items_out: list[DiagnosticItemResult] = []
    for item in items:
        skills = item.tested_skills or [item.skill]
        if item.type == "mcq":
            is_correct = (item.user_answer or "").strip() == (
                item.correct_answer or ""
            ).strip()
            score = 100 if is_correct else 0
            per_skill = {s: score for s in skills}
            answer_kind = "blank" if not (item.user_answer or "").strip() else "code"
            explanation = (
                "Correct."
                if is_correct
                else f"The correct answer is **{item.correct_answer}**."
            )
        else:
            ans = (item.user_answer or "").strip()
            looks_pseudo = bool(ans) and "def " not in ans and "return" not in ans
            if not ans:
                answer_kind, is_correct, score = "blank", False, 0
                per_skill = {s: 0 for s in skills}
                explanation = "No answer submitted."
            elif looks_pseudo:
                # Plain English — partial credit per the rule. Code Quality near zero;
                # other skills get 40 if a substantive attempt.
                answer_kind, is_correct, score = "pseudo_english", False, 40
                per_skill = {s: (10 if s == "Code Quality" else 45) for s in skills}
                explanation = (
                    "Plain-English / pseudocode response: partial credit for the idea, "
                    "but Code Quality is low because no real code was written."
                )
            elif len(ans) < 30:
                answer_kind, is_correct, score = "code", False, 40
                per_skill = {s: 40 for s in skills}
                explanation = "Looks like a stub - try a full implementation that handles edge cases."
            else:
                answer_kind, is_correct, score = "code", True, 70
                per_skill = {s: 70 for s in skills}
                explanation = "Reasonable attempt - the AI grader is offline so this is a flat estimate."
        items_out.append(
            DiagnosticItemResult(
                order_index=item.order_index,
                is_correct=is_correct,
                score=score,
                per_skill_scores=per_skill,
                answer_kind=answer_kind,
                explanation_md=explanation,
                correct_answer=item.correct_answer,
            )
        )

    # Aggregate skill_scores from per-item per_skill_scores
    bucket: dict[str, list[int]] = {}
    for r in items_out:
        for skill, score in (r.per_skill_scores or {}).items():
            bucket.setdefault(skill, []).append(score)
    skill_scores: dict[str, int] = {
        skill: round(sum(scores) / len(scores)) for skill, scores in bucket.items()
    }

    overall = (
        round(sum(r.score for r in items_out) / len(items_out)) if items_out else 0
    )
    weak = _compute_weak_skills(skill_scores)
    return DiagnosticResult(
        items=items_out,
        skill_scores=skill_scores,
        overall_score=overall,
        summary_md=(
            "Diagnostic graded offline. The LLM was unavailable, so we used a "
            "rule-based scorer. Configure GOOGLE_API_KEY for AI-written explanations."
        ),
        weak_skills=weak,
        source="heuristic",
    )


# --------------------------- small helpers ---------------------------


def _clamp_int(value: Any, lo: int, hi: int, *, default: int = 0) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def _default_item_result(item: DiagnosticItemInput) -> DiagnosticItemResult:
    return DiagnosticItemResult(
        order_index=item.order_index,
        is_correct=False,
        score=0,
        explanation_md="(Not evaluated.)",
        correct_answer=item.correct_answer,
    )


def _compute_weak_skills(skill_scores: dict[str, int]) -> list[str]:
    return [skill for skill, _ in sorted(skill_scores.items(), key=lambda kv: kv[1])][
        :3
    ]


__all__ = [
    "DiagnosticItemInput",
    "DiagnosticItemResult",
    "DiagnosticResult",
    "grade_diagnostic",
]
