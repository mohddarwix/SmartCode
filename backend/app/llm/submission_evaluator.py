"""
LLM-driven submission evaluator.

Given a problem (statement + test cases) and the user's code, ask the LLM to:
  1) mentally execute the code on each test case and decide pass/fail
  2) for FAILED cases, predict the actual output and explain how to fix it
  3) produce overall scores (correctness, edge cases, code quality, time complexity)
  4) write summary + feedback bullets

Two flavors:
  - `run_submission(...)`  — only visible (sample/public) cases, used by Run button
  - `evaluate_submission(...)` — visible + hidden, used by Submit

Heuristic fallback runs when the LLM is unavailable. It does NOT pretend
to know whether the code is correct — it returns an honest "couldn't grade"
result so the user knows the AI is offline.
"""

from __future__ import annotations

import ast
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel

from . import client as llm_client
from ..sandbox import PROBLEM_CONFIGS as _SANDBOX_CONFIGS, run_all_cases as _sandbox_run

log = logging.getLogger("ai_tutor.llm.evaluator")


class TestCaseSnapshot(BaseModel):
    case_index: int  # 1-based, matches what the LLM should reference
    name: str | None
    visibility: Literal["sample", "public", "hidden"]
    input_blob: str
    expected_blob: str


class EvaluationInput(BaseModel):
    problem_slug: str  # routes the sandbox to the right method/adapters
    problem_title: str
    difficulty: Literal["easy", "medium", "hard"]
    statement_md: str
    constraints_md: str | None
    cases: list[TestCaseSnapshot]  # everything the LLM gets to see for this evaluation
    language: str
    code: str


Severity = Literal["minor", "moderate", "severe"]

# Score penalty (points) per failed-test-case severity. Used by the submissions
# router to discount the final score when a user finally passes after earlier
# failed attempts.
SEVERITY_POINTS: dict[str, int] = {"minor": 1, "moderate": 2, "severe": 3}


class TestCaseResult(BaseModel):
    case_index: int
    name: str | None
    visibility: Literal["sample", "public", "hidden"]
    input_blob: str
    expected_blob: str
    predicted_output: str  # what the LLM thinks the code returns
    passed: bool
    explanation_md: str  # populated mainly when passed=False
    severity: Severity | None = None  # only meaningful when passed=False


class FeedbackBullet(BaseModel):
    kind: Literal["good", "warn"]
    text: str


class EvaluationResult(BaseModel):
    cases: list[TestCaseResult]
    passed_count: int
    total_count: int
    status: Literal[
        "accepted", "wrong_answer", "runtime_error", "time_limit", "compile_error"
    ]
    score: int
    score_correctness: int
    score_edge_cases: int
    score_code_quality: int
    score_time_complexity: int
    inferred_big_o: str | None
    summary_md: str
    bullets: list[FeedbackBullet]
    source: Literal["llm", "heuristic"]
    runtime_ms: int = 50
    memory_kb: int = 10000


_SYSTEM_PROMPT = """You are the grading engine for an adaptive programming tutor. A student submits a Python solution to a problem; your job is to decide whether it actually works on each test case and to teach them where it falls short.

For each submission you are given:
  - the problem statement and constraints
  - a list of test cases (input + expected output), each with a 1-based `case_index`
  - the student's code

For EACH test case, mentally execute the student's code on that input and decide whether the produced output matches the expected output. Be honest - do NOT mark a case as passing just because the code looks reasonable. Common failure modes to flag:
  - wrong return value, wrong shape, wrong type
  - logical bugs (off-by-one, wrong sentinel, mishandled negatives/duplicates/empties)
  - empty function body, just `pass`, or only re-printing the input
  - missing the function signature the problem asks for
  - exponential or otherwise poor time complexity on the given constraints
  - missing edge-case handling (empty input, single element, max/min values)

CHEATER / LUCKY-COINCIDENCE CHECK (do this FIRST, before grading any case):
Decide whether the student's code is actually SOLVING the problem versus emitting a value that happens to match an expected output by coincidence. Flag ALL of the following as FAILED cases even when predicted_output == expected_blob:

  1. Function body is just `return <literal>` (e.g. `return 5`, `return []`, `return True`, `return "abc"`) regardless of input.
  2. Function body never references its parameters/arguments — it computes a value purely from constants and ignores `nums`, `target`, `head`, `s`, etc.
  3. Function hardcodes lookups of sample inputs (`if n == 2: return 2; elif n == 3: return 3; ...`). A real solution must compute from input via a general algorithm, not enumerate sample answers.
  4. Function returns an input unchanged when the problem clearly asks for a transformation (`return nums`, `return head`, `return s`).

When ANY of these patterns is detected:
  - For EVERY test case: set `passed=false`, `severity="severe"`, and `explanation_md` MUST start with: "This solution does not derive its answer from the input — <one-sentence reason>." `predicted_output` should still reflect what the code would actually produce.
  - Set overall `status="wrong_answer"`, `score_correctness=0`, `score_edge_cases=0`.
  - Add a `warn` bullet: "Hardcoded / constant-returning solutions are not accepted, even if they happen to match the sample outputs. Implement a real algorithm that uses the input."

A coincidence is never a correct answer.

Scoring rubric (0-100 each):
  - score_correctness: % of test cases the code would pass. Be strict.
  - score_edge_cases: how well it handles boundary inputs (empty arrays, n=1, max/min values). 0 if it would clearly crash on a common edge.
  - score_code_quality: naming, structure, idiomatic Python. 70 is normal; 90+ for clean, well-named code.
  - score_time_complexity: 100 for optimal, 70 for one factor off, 30-50 for clearly suboptimal.

`status`:
  - "accepted" only if every test case passes
  - "wrong_answer" if at least one fails
  - "runtime_error" if the code would clearly raise (IndexError, ZeroDivisionError, etc.) on a likely input
  - "compile_error" if the code is not syntactically valid Python
  - "time_limit" if you can prove it would TLE on the given constraints (rare)

`score` (overall): roughly 0.55*correctness + 0.15*edge_cases + 0.15*code_quality + 0.15*time_complexity, rounded.

For each TestCaseResult:
  - `case_index`: copy verbatim from the input
  - `predicted_output`: the EXACT output you believe the code would produce on this input (one line if possible; use the same format as `expected_blob`). For a runtime/compile error, put the error class + message here.
  - `passed`: true only if predicted_output is semantically equal to expected_blob
  - `explanation_md`: for FAILED cases, write 1-3 sentences explaining (a) what the code actually does on this input, (b) why that's wrong, (c) a concrete hint for fixing it. For PASSED cases, leave this empty string or a short positive note like "Handled correctly via X.".
  - `severity`: ONLY for FAILED cases — one of "minor", "moderate", "severe":
      * "minor": cosmetic mismatch (output formatting, extra whitespace, off-by-one only on a rare edge case, wrong sort order when problem allows any order).
      * "moderate": logic gap that breaks a clear edge case (empty input, single element, duplicates, negatives) while the core algorithm is on the right track.
      * "severe": fundamental error (algorithm is wrong, code crashes, wrong return type, ignores the problem, stub/empty body, or fails any of the main sample cases).
    Be honest. Multiple severe failures across cases is normal for a broken solution.
    For PASSED cases, omit severity or set it to null.

`bullets`: 3-5 specific, actionable items, each with kind="good" or kind="warn". Be concrete. Never just say "looks good".

Respond with a single JSON object, no prose, no code fences:

{
  "cases": [
    {
      "case_index": int,
      "predicted_output": str,
      "passed": bool,
      "explanation_md": str,
      "severity": "minor" | "moderate" | "severe" | null
    }
  ],
  "passed_count": int,
  "total_count": int,
  "status": "accepted" | "wrong_answer" | "runtime_error" | "time_limit" | "compile_error",
  "score": int,
  "score_correctness": int,
  "score_edge_cases": int,
  "score_code_quality": int,
  "score_time_complexity": int,
  "inferred_big_o": "O(...)",
  "summary_md": "1-2 sentences",
  "bullets": [{"kind": "good"|"warn", "text": "..."}]
}"""


def evaluate_submission(inp: EvaluationInput) -> EvaluationResult:
    """
    Evaluate a submission with the strongest signal we have:

      1) The Python sandbox actually executes the code against each case
         (when we have a config for this problem). Its pass/fail verdict is
         authoritative — LLMs hallucinate, real interpreters don't.
      2) The LLM (if available) layers qualitative judgement on top:
         severity per failed case, per-axis scores (edge cases / code
         quality / time complexity), summary, bullets. The LLM is informed
         of the sandbox verdicts so its severity/explanations stay consistent.
      3) The AST cheater backstop overrides the result if the code is just
         `return <literal>` or never references its params — even if the
         sandbox says "passed" (a constant can coincide with the expected
         output by luck), the submission is rejected as not-actually-solving.
    """
    sandbox_results = _run_sandbox(inp)

    if llm_client.is_available():
        try:
            result = _evaluate_with_llm(inp, sandbox_results)
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM submission evaluation failed, using sandbox-only: %s", exc)
            result = _evaluate_from_sandbox_only(inp, sandbox_results)
    else:
        result = _evaluate_from_sandbox_only(inp, sandbox_results)

    # Overlay sandbox truth onto the case verdicts (covers the LLM path).
    if sandbox_results:
        result = _overlay_sandbox(result, sandbox_results)

    # Cheater backstop: catches `return 5` even when the sandbox says it
    # coincidentally matched.
    cheat = _detect_lucky_coincidence(inp.code)
    if cheat is not None:
        result = _force_cheat_result(result, inp, cheat)
    return result


# ---- Sandbox helpers ----


def _run_sandbox(inp: EvaluationInput) -> dict[int, "object"]:
    """Run all cases through the Python subprocess sandbox.

    Returns {case_index: CaseExecutionResult}. Returns empty dict if we
    don't have a sandbox config for this problem (newly-admin-created
    problem with no method/param mapping yet).
    """
    if inp.problem_slug not in _SANDBOX_CONFIGS:
        log.info(
            "No sandbox config for slug %r — falling back to LLM-only", inp.problem_slug
        )
        return {}
    payload_cases = [
        {
            "case_index": c.case_index,
            "input_blob": c.input_blob,
            "expected_blob": c.expected_blob,
        }
        for c in inp.cases
    ]
    rows = _sandbox_run(slug=inp.problem_slug, user_code=inp.code, cases=payload_cases)
    return {r.case_index: r for r in rows}


def _overlay_sandbox(
    result: EvaluationResult, sandbox: dict[int, "object"]
) -> EvaluationResult:
    """Override LLM verdicts with sandbox truth, then recompute aggregates."""
    new_cases: list[TestCaseResult] = []
    any_runtime_error = False
    for c in result.cases:
        sb = sandbox.get(c.case_index)
        if sb is None:
            new_cases.append(c)
            continue
        if sb.timed_out:
            any_runtime_error = True
        predicted = sb.actual_output or (sb.error or "(no output)")
        if sb.passed:
            # Real interpreter says it works. Drop any LLM-fabricated explanation.
            new_cases.append(
                c.model_copy(
                    update={
                        "passed": True,
                        "predicted_output": predicted,
                        "explanation_md": (
                            ""
                            if c.explanation_md and not c.passed
                            else c.explanation_md
                        ),
                        "severity": None,
                    }
                )
            )
        else:
            # Real failure. Keep the LLM's explanation if it has one, else build
            # a tight one from the sandbox error.
            if c.explanation_md and not c.passed:
                exp = c.explanation_md
            elif sb.error:
                exp = (
                    f"Got `{predicted}` (expected `{sb.expected_output}`). "
                    f"The code raised {sb.error.split(':', 1)[0]} on this input."
                )
            else:
                exp = (
                    f"Got `{predicted}`, expected `{sb.expected_output}`. "
                    "Trace your algorithm on this input to find the divergence."
                )
            severity = c.severity or _infer_severity_from_visibility(
                c.visibility, sb.error
            )
            new_cases.append(
                c.model_copy(
                    update={
                        "passed": False,
                        "predicted_output": predicted,
                        "explanation_md": exp,
                        "severity": severity,
                    }
                )
            )

    passed = sum(1 for c in new_cases if c.passed)
    total = len(new_cases) or result.total_count
    new_status = (
        "accepted"
        if passed == total
        else ("runtime_error" if any_runtime_error else "wrong_answer")
    )
    new_correctness = round(100 * passed / total) if total else 0
    new_score = round(
        0.55 * new_correctness
        + 0.15 * result.score_edge_cases
        + 0.15 * result.score_code_quality
        + 0.15 * result.score_time_complexity
    )

    # Aggregate sandbox metrics across cases: sum runtime, peak across memory.
    runtime_ms = sum(int(getattr(sb, "elapsed_ms", 0) or 0) for sb in sandbox.values())
    memory_kb = max(
        (int(getattr(sb, "peak_memory_kb", 0) or 0) for sb in sandbox.values()),
        default=0,
    )

    return result.model_copy(
        update={
            "cases": new_cases,
            "passed_count": passed,
            "total_count": total,
            "status": new_status,
            "score": max(0, min(100, new_score)),
            "score_correctness": new_correctness,
            "runtime_ms": runtime_ms or result.runtime_ms,
            "memory_kb": memory_kb or result.memory_kb,
        }
    )


def _infer_severity_from_visibility(visibility: str, error: str | None) -> Severity:
    """Reasonable default severity when the LLM didn't label the case."""
    if error and ("Error" in error or "Exception" in error or "Timed out" in error):
        return "severe"
    if visibility == "sample":
        return "severe"  # failing a sample case is a fundamental break
    if visibility == "public":
        return "moderate"
    return "moderate"


def _evaluate_from_sandbox_only(
    inp: EvaluationInput, sandbox: dict[int, "object"]
) -> EvaluationResult:
    """Build a result from sandbox alone (LLM offline / no config)."""
    cases: list[TestCaseResult] = []
    for c in inp.cases:
        sb = sandbox.get(c.case_index)
        if sb is None:
            # No sandbox config — record honest "not evaluated" and let
            # the LLM-offline heuristic shape the rest.
            cases.append(
                TestCaseResult(
                    case_index=c.case_index,
                    name=c.name,
                    visibility=c.visibility,
                    input_blob=c.input_blob,
                    expected_blob=c.expected_blob,
                    predicted_output="(not evaluated)",
                    passed=False,
                    explanation_md="No sandbox config for this problem and the LLM grader is offline.",
                    severity="moderate",
                )
            )
            continue
        predicted = sb.actual_output or (sb.error or "(no output)")
        explanation = ""
        severity: Severity | None = None
        if not sb.passed:
            severity = _infer_severity_from_visibility(c.visibility, sb.error)
            explanation = f"Got `{predicted}`, expected `{sb.expected_output}`." + (
                f" ({sb.error})" if sb.error else ""
            )
        cases.append(
            TestCaseResult(
                case_index=c.case_index,
                name=c.name,
                visibility=c.visibility,
                input_blob=c.input_blob,
                expected_blob=c.expected_blob,
                predicted_output=predicted,
                passed=sb.passed,
                explanation_md=explanation,
                severity=severity,
            )
        )

    passed = sum(1 for c in cases if c.passed)
    total = len(cases) or 1
    status = "accepted" if passed == total else "wrong_answer"
    correctness = round(100 * passed / total)
    bullets = [
        FeedbackBullet(
            kind="good" if passed == total else "warn",
            text=(
                f"{passed}/{total} test cases passed in the Python sandbox."
                if not sandbox
                else f"{passed}/{total} test cases passed in the Python sandbox."
            ),
        ),
        FeedbackBullet(
            kind="warn",
            text="The AI grader is offline, so qualitative feedback (code quality, time complexity insights) isn't available right now — only pass/fail.",
        ),
    ]
    return EvaluationResult(
        cases=cases,
        passed_count=passed,
        total_count=total,
        status=status,
        score=correctness,  # without LLM axes, just correctness
        score_correctness=correctness,
        score_edge_cases=correctness,  # placeholder — no LLM signal
        score_code_quality=70,
        score_time_complexity=70,
        inferred_big_o=None,
        summary_md=(
            f"Sandbox-only grading: {passed}/{total} cases pass. "
            "AI commentary is unavailable."
        ),
        bullets=bullets,
        source="heuristic",
        runtime_ms=sum(
            int(getattr(sb, "elapsed_ms", 0) or 0) for sb in sandbox.values()
        )
        or 50,
        memory_kb=max(
            (int(getattr(sb, "peak_memory_kb", 0) or 0) for sb in sandbox.values()),
            default=0,
        )
        or 10000,
    )


def _detect_lucky_coincidence(code: str) -> str | None:
    """
    Return a reason string if the code is a trivial non-solution, else None.

    Detects:
      - The user-facing solver function has a body that's a single `return <constant>`
      - The user-facing solver function never references any of its parameters

    "User-facing solver" = the longest non-dunder method on the Solution class.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    target_fn: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Solution":
            for body in node.body:
                if isinstance(body, ast.FunctionDef) and not body.name.startswith("_"):
                    if target_fn is None or len(body.body) > len(target_fn.body):
                        target_fn = body
    if target_fn is None:
        return None

    # Pattern 1: single statement, `return <literal>`
    if len(target_fn.body) == 1 and isinstance(target_fn.body[0], ast.Return):
        ret = target_fn.body[0].value
        if isinstance(ret, ast.Constant):
            return (
                f"the function body is just `return {ret.value!r}` regardless of input"
            )
        if (
            isinstance(ret, (ast.List, ast.Dict, ast.Set, ast.Tuple))
            and not ret.elts
            and not getattr(ret, "keys", None)
        ):
            return "the function body is just `return <empty container>` regardless of input"

    # Pattern 2: function body never references its parameters/args.
    param_names = {a.arg for a in target_fn.args.args if a.arg != "self"}
    if param_names:
        referenced = {n.id for n in ast.walk(target_fn) if isinstance(n, ast.Name)}
        if not (param_names & referenced):
            return (
                f"the function body never references its parameters "
                f"({', '.join(sorted(param_names))})"
            )

    return None


def _force_cheat_result(
    result: EvaluationResult, inp: EvaluationInput, reason: str
) -> EvaluationResult:
    """Override the evaluator output to mark all cases as severe failures."""
    explanation = (
        f"This solution does not derive its answer from the input — {reason}. "
        "A coincidental match with an expected output is not a real solution."
    )
    new_cases = [
        TestCaseResult(
            case_index=c.case_index,
            name=c.name,
            visibility=c.visibility,
            input_blob=c.input_blob,
            expected_blob=c.expected_blob,
            predicted_output=c.predicted_output,
            passed=False,
            explanation_md=explanation,
            severity="severe",
        )
        for c in result.cases
    ]
    cheat_bullet = FeedbackBullet(
        kind="warn",
        text=(
            "Hardcoded / constant-returning solutions are not accepted, even if "
            "they happen to match the sample outputs. Implement a real algorithm "
            "that uses the input."
        ),
    )
    other_bullets = [b for b in result.bullets if "constant" not in b.text.lower()]
    return EvaluationResult(
        cases=new_cases,
        passed_count=0,
        total_count=result.total_count,
        status="wrong_answer",
        score=0,
        score_correctness=0,
        score_edge_cases=0,
        score_code_quality=max(0, min(result.score_code_quality, 30)),
        score_time_complexity=0,
        inferred_big_o=None,
        summary_md=(
            "Submission rejected: this solution does not actually solve the problem. "
            + reason.capitalize()
            + "."
        ),
        bullets=[cheat_bullet, *other_bullets],
        source=result.source,
        runtime_ms=result.runtime_ms,
        memory_kb=result.memory_kb,
    )


def run_submission(inp: EvaluationInput) -> EvaluationResult:
    """Lightweight Run: same evaluator, but the caller only supplies visible cases."""
    return evaluate_submission(inp)


# --------------------------- LLM path ---------------------------


def _evaluate_with_llm(
    inp: EvaluationInput, sandbox: dict[int, "object"] | None = None
) -> EvaluationResult:
    user_text = _build_user_prompt(inp, sandbox or {})
    raw = llm_client.call_json(system=_SYSTEM_PROMPT, user=user_text, max_tokens=8192)

    total = max(1, len(inp.cases))
    cases_by_idx = {c.case_index: c for c in inp.cases}

    cases_out: list[TestCaseResult] = []
    for entry in raw.get("cases") or []:
        if not isinstance(entry, dict):
            continue
        try:
            idx = int(entry.get("case_index"))
        except (TypeError, ValueError):
            continue
        snap = cases_by_idx.get(idx)
        if snap is None:
            continue
        passed = bool(entry.get("passed", False))
        sev_raw = entry.get("severity")
        severity = sev_raw if sev_raw in ("minor", "moderate", "severe") else None
        if passed:
            severity = None
        elif severity is None:
            # LLM forgot to label a failure; default to moderate so the penalty still
            # bites without over-punishing.
            severity = "moderate"
        cases_out.append(
            TestCaseResult(
                case_index=idx,
                name=snap.name,
                visibility=snap.visibility,
                input_blob=snap.input_blob,
                expected_blob=snap.expected_blob,
                predicted_output=str(entry.get("predicted_output") or ""),
                passed=passed,
                explanation_md=str(entry.get("explanation_md") or "").strip(),
                severity=severity,
            )
        )
    # Make sure every input case is present in the output (LLM may drop some).
    seen = {r.case_index for r in cases_out}
    for snap in inp.cases:
        if snap.case_index in seen:
            continue
        cases_out.append(
            TestCaseResult(
                case_index=snap.case_index,
                name=snap.name,
                visibility=snap.visibility,
                input_blob=snap.input_blob,
                expected_blob=snap.expected_blob,
                predicted_output="(not evaluated)",
                passed=False,
                explanation_md="The grader did not return a verdict for this case.",
                severity="moderate",
            )
        )
    cases_out.sort(key=lambda c: c.case_index)

    bullets = []
    for b in raw.get("bullets") or []:
        if not isinstance(b, dict):
            continue
        kind = b.get("kind")
        text = b.get("text")
        if kind in ("good", "warn") and isinstance(text, str) and text.strip():
            bullets.append(FeedbackBullet(kind=kind, text=text.strip()))
    if not bullets:
        bullets = [FeedbackBullet(kind="warn", text="No detailed feedback available.")]

    passed_count = sum(1 for c in cases_out if c.passed)
    status = raw.get("status")
    if status not in (
        "accepted",
        "wrong_answer",
        "runtime_error",
        "time_limit",
        "compile_error",
    ):
        status = "accepted" if passed_count == total else "wrong_answer"
    # Enforce internal consistency: any failure means not "accepted".
    if status == "accepted" and passed_count != total:
        status = "wrong_answer"

    return EvaluationResult(
        cases=cases_out,
        passed_count=passed_count,
        total_count=total,
        status=status,
        score=_clamp_int(raw.get("score"), 0, 100, default=_default_overall(raw)),
        score_correctness=_clamp_int(raw.get("score_correctness"), 0, 100),
        score_edge_cases=_clamp_int(raw.get("score_edge_cases"), 0, 100),
        score_code_quality=_clamp_int(raw.get("score_code_quality"), 0, 100),
        score_time_complexity=_clamp_int(raw.get("score_time_complexity"), 0, 100),
        inferred_big_o=(
            str(raw.get("inferred_big_o")) if raw.get("inferred_big_o") else None
        ),
        summary_md=str(raw.get("summary_md") or "").strip() or "Solution evaluated.",
        bullets=bullets,
        source="llm",
    )


def _build_user_prompt(inp: EvaluationInput, sandbox: dict[int, "object"]) -> str:
    parts = [
        f"# Problem: {inp.problem_title} ({inp.difficulty})\n",
        f"## Statement\n{inp.statement_md}\n",
    ]
    if inp.constraints_md:
        parts.append(f"## Constraints\n{inp.constraints_md}\n")

    if sandbox:
        parts.append(
            "## Sandbox execution results (AUTHORITATIVE)\n"
            "We already ran the student's code in a real Python interpreter against "
            "every case. Use these verdicts when setting `passed` — DO NOT contradict them. "
            "Your job is to provide good `explanation_md` for failed cases (what went wrong "
            "and how to fix it) and the qualitative scores (edge cases, code quality, time "
            "complexity).\n"
        )

    parts.append(f"## Test cases ({len(inp.cases)})")
    for tc in inp.cases:
        suffix = f" — {tc.name}" if tc.name else ""
        parts.append(f"### Case {tc.case_index}{suffix} (visibility: {tc.visibility})")
        parts.append(f"Input:\n```\n{tc.input_blob}\n```")
        parts.append(f"Expected output:\n```\n{tc.expected_blob}\n```")
        sb = sandbox.get(tc.case_index)
        if sb is not None:
            verdict = "PASSED" if sb.passed else "FAILED"
            actual = sb.actual_output or "(none)"
            err = f" — runtime: {sb.error}" if sb.error else ""
            parts.append(f"**Sandbox: {verdict}**. Actual output: `{actual}`{err}")

    parts.append(
        f"\n## Student submission ({inp.language})\n```{inp.language}\n{inp.code}\n```\n"
        "\nNow grade it. For each test case, copy the sandbox verdict into `passed`, "
        "set `predicted_output` to the sandbox's actual output (or your best guess if "
        "no sandbox row), and write a useful `explanation_md` for failures. "
        "Respond with the JSON object specified in your system instructions."
    )
    return "\n".join(parts)


def _default_overall(raw: dict[str, Any]) -> int:
    corr = _clamp_int(raw.get("score_correctness"), 0, 100)
    edge = _clamp_int(raw.get("score_edge_cases"), 0, 100)
    qual = _clamp_int(raw.get("score_code_quality"), 0, 100)
    timec = _clamp_int(raw.get("score_time_complexity"), 0, 100)
    return round(0.55 * corr + 0.15 * edge + 0.15 * qual + 0.15 * timec)


# --------------------------- Heuristic fallback ---------------------------

_STUB_PATTERNS = (
    re.compile(r"^\s*pass\s*$", re.MULTILINE),
    re.compile(r"#\s*Write your solution here", re.IGNORECASE),
    re.compile(r"#\s*your code here", re.IGNORECASE),
    re.compile(r"#\s*TODO", re.IGNORECASE),
)


def _evaluate_with_heuristic(inp: EvaluationInput) -> EvaluationResult:
    """Honest heuristic: we don't try to predict the code's output."""
    code = inp.code or ""
    stripped = code.strip()
    total = max(1, len(inp.cases))

    compile_error: str | None = None
    try:
        compile(code, "<submission>", "exec")
    except SyntaxError as exc:
        compile_error = str(exc)

    has_return = re.search(r"\breturn\b", code) is not None
    has_solution_class = "class Solution" in code
    looks_like_stub = (
        not stripped
        or len(stripped) < 30
        or (any(p.search(code) for p in _STUB_PATTERNS) and not has_return)
    )

    # Build per-case rows (all failing, with a generic explanation)
    def case_rows(reason: str, sev: Severity = "severe") -> list[TestCaseResult]:
        return [
            TestCaseResult(
                case_index=c.case_index,
                name=c.name,
                visibility=c.visibility,
                input_blob=c.input_blob,
                expected_blob=c.expected_blob,
                predicted_output="(not evaluated)",
                passed=False,
                explanation_md=reason,
                severity=sev,
            )
            for c in inp.cases
        ]

    if compile_error:
        return EvaluationResult(
            cases=case_rows(f"Code didn't compile: {compile_error}"),
            passed_count=0,
            total_count=total,
            status="compile_error",
            score=0,
            score_correctness=0,
            score_edge_cases=0,
            score_code_quality=10,
            score_time_complexity=0,
            inferred_big_o=None,
            summary_md=f"Your code didn't compile: `{compile_error[:120]}`.",
            bullets=[
                FeedbackBullet(kind="warn", text=f"Syntax error: {compile_error}"),
                FeedbackBullet(kind="warn", text="Fix the syntax error and resubmit."),
            ],
            source="heuristic",
        )

    if looks_like_stub:
        return EvaluationResult(
            cases=case_rows(
                "The function body is empty or only contains placeholder comments."
            ),
            passed_count=0,
            total_count=total,
            status="wrong_answer",
            score=10,
            score_correctness=0,
            score_edge_cases=0,
            score_code_quality=30,
            score_time_complexity=0,
            inferred_big_o=None,
            summary_md="Your submission looks like the starter template, not a real solution.",
            bullets=[
                FeedbackBullet(
                    kind="warn",
                    text="The function body is empty or only contains placeholder comments.",
                ),
                FeedbackBullet(
                    kind="warn", text="Implement the function and resubmit."
                ),
            ],
            source="heuristic",
        )

    reason = (
        "The AI grader is unavailable and the offline scorer can't execute code. "
        "We can't confirm this case passes — set GOOGLE_API_KEY for real grading."
    )
    return EvaluationResult(
        cases=case_rows(reason),
        passed_count=0,
        total_count=total,
        status="wrong_answer",
        score=40,
        score_correctness=30,
        score_edge_cases=40,
        score_code_quality=70 if has_solution_class else 60,
        score_time_complexity=50,
        inferred_big_o=None,
        summary_md=(
            "We received your submission but couldn't fully grade it. The AI grader "
            "is unavailable, and the offline scorer can't actually run the code. "
            "Add a GOOGLE_API_KEY to enable real grading."
        ),
        bullets=[
            FeedbackBullet(
                kind="warn",
                text="Real evaluation requires either the LLM grader (GOOGLE_API_KEY) or a code-execution sandbox; neither is active.",
            ),
            FeedbackBullet(
                kind="good" if has_return else "warn",
                text=(
                    "Your code does have a return statement."
                    if has_return
                    else "I didn't find a `return` in your code — make sure your function actually returns a result."
                ),
            ),
            FeedbackBullet(
                kind="good" if has_solution_class else "warn",
                text=(
                    "You defined a Solution class as expected."
                    if has_solution_class
                    else "Wrap your code in a `Solution` class for LeetCode-style problems."
                ),
            ),
        ],
        source="heuristic",
    )


# --------------------------- small helpers ---------------------------------


def _clamp_int(value: Any, lo: int, hi: int, *, default: int = 0) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


__all__ = [
    "TestCaseSnapshot",
    "EvaluationInput",
    "EvaluationResult",
    "TestCaseResult",
    "FeedbackBullet",
    "evaluate_submission",
    "run_submission",
]
