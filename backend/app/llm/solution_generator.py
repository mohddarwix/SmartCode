"""
LLM-driven solution generator.

Given a problem (statement + constraints + visible samples), produces a clean
canonical Python solution plus a teaching-quality explanation and complexity
analysis. Used to back the editor's "Solutions" tab once a student has
solved the problem.

Results are cached in the `ai_solutions` table by the caller, so we only pay
the Gemini cost once per problem.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel

from . import client as llm_client

log = logging.getLogger("ai_tutor.llm.solution_generator")


class SolutionInput(BaseModel):
    problem_title: str
    difficulty: Literal["easy", "medium", "hard"]
    statement_md: str
    constraints_md: str | None
    sample_cases: list[dict]  # [{name, input_blob, expected_blob}]
    starter_code_md: str | None
    language: str = "python"


class SolutionResult(BaseModel):
    explanation_md: str  # 3-6 short paragraphs walking through the approach
    solution_code: str  # complete, runnable Python (Solution class)
    time_complexity: str  # "O(n)", "O(n log n)", etc.
    space_complexity: str
    source: Literal["llm", "heuristic"]


_SYSTEM_PROMPT = """You are the canonical-solution author for an adaptive programming tutor. You will receive a problem statement and constraints; produce a clean, idiomatic Python solution and a short teaching explanation.

Hard rules:
  - Output MUST contain a complete `class Solution:` with the same method signature implied by the problem (twoSum, isValid, climbStairs, etc.).
  - The code should be production-quality: idiomatic Python, descriptive names, no unused imports, no dead code, no debug prints.
  - Prefer the algorithm that matches the constraints — don't use O(n^2) when the input bound is 10^5 and a linear/log-linear pass exists.
  - The explanation is for a student who just solved the problem themselves. Briefly: the key insight, why a naive approach fails, what state you maintain, and how each test case unfolds. 3-6 short paragraphs. Markdown headings are fine.
  - Time / space complexity must be honest (do not claim O(n) for a code path that's actually O(n log n)).

Respond with a single JSON object — no prose, no code fences:

{
  "solution_code": "class Solution:\\n    def twoSum(self, nums, target):\\n        ...",
  "explanation_md": "## Approach\\n...",
  "time_complexity": "O(n)",
  "space_complexity": "O(n)"
}"""


def generate_solution(inp: SolutionInput) -> SolutionResult:
    """Call the LLM; fall back to a minimal stub on failure."""
    if llm_client.is_available():
        try:
            return _generate_with_llm(inp)
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM solution generation failed, using heuristic: %s", exc)
    return _generate_with_heuristic(inp)


# --------------------------- LLM path ---------------------------


def _generate_with_llm(inp: SolutionInput) -> SolutionResult:
    parts = [
        f"# Problem: {inp.problem_title} ({inp.difficulty})",
        f"## Statement\n{inp.statement_md}",
    ]
    if inp.constraints_md:
        parts.append(f"## Constraints\n{inp.constraints_md}")
    if inp.sample_cases:
        parts.append("## Sample cases")
        for c in inp.sample_cases[:3]:
            name = c.get("name") or ""
            parts.append(f"### {name}")
            parts.append(f"Input:\n```\n{c.get('input_blob', '')}\n```")
            parts.append(f"Expected:\n```\n{c.get('expected_blob', '')}\n```")
    if inp.starter_code_md:
        parts.append(
            "## Starter signature (match this exactly)\n"
            f"```{inp.language}\n{inp.starter_code_md}\n```"
        )
    parts.append("Now produce the JSON solution object.")
    user_text = "\n\n".join(parts)

    # 6k is comfortably above what a clean solution + 3-6 paragraph explanation
    # typically needs (2048 truncated mid-output for Group Anagrams).
    raw = llm_client.call_json(system=_SYSTEM_PROMPT, user=user_text, max_tokens=6144)
    code = str(raw.get("solution_code") or "").strip()
    if not code or "class Solution" not in code:
        raise ValueError("LLM did not return a Solution class")

    return SolutionResult(
        solution_code=code,
        explanation_md=str(raw.get("explanation_md") or "").strip()
        or "_(no explanation provided)_",
        time_complexity=str(raw.get("time_complexity") or "").strip()
        or "(not specified)",
        space_complexity=str(raw.get("space_complexity") or "").strip()
        or "(not specified)",
        source="llm",
    )


# --------------------------- Heuristic fallback ---------------------------


def _generate_with_heuristic(inp: SolutionInput) -> SolutionResult:
    """Best-effort placeholder when Gemini is offline."""
    starter = (inp.starter_code_md or "class Solution:\n    pass\n").strip()
    return SolutionResult(
        solution_code=starter
        + "\n# Solution generation is offline. Re-open this view once the AI grader reconnects.\n",
        explanation_md=(
            "## Solution offline\n"
            "The AI couldn't generate the canonical solution right now. The student "
            "can re-open the Solutions tab later, or the instructor can pre-seed this "
            "problem's solution in `ai_solutions`."
        ),
        time_complexity="(unknown)",
        space_complexity="(unknown)",
        source="heuristic",
    )


__all__ = ["SolutionInput", "SolutionResult", "generate_solution", "stream_live_solve"]


# ===========================================================================
# Live "watch the AI solve" — streaming version
# ===========================================================================

_LIVE_SOLVE_SYSTEM = """You are an AI programming tutor solving a problem LIVE for a student who has just solved it themselves and wants to see your reasoning.

You are not writing a polished final solution — you are THINKING OUT LOUD, working the problem step by step like a tutor at a whiteboard. The student is watching the words appear in real time.

Structure your response in this exact order, using these EXACT markdown headings:

## Reading the problem
Restate the problem in your own words. Identify what's actually being asked.

## Looking at the constraints
What do the size bounds tell us? Is O(n^2) okay or do we need linear? Any tricky values (negatives, empties, duplicates)?

## First instinct: brute force
Describe the naive approach in 2-4 sentences. Be honest about why someone might think of it first. Don't write the code yet.

## Why we can do better
What's wasteful about the naive approach? What invariant can we maintain or what data structure can we use to avoid the repeated work?

## The clean solution
Now write the actual Python solution in a single fenced ```python block. Use class Solution: and the right method name. Use clean, descriptive names.

## Tracing through the first example
Pick the first sample case and walk through what your code does line-by-line for that specific input. 4-8 short bullet points. End with the returned value.

## Complexity
One sentence each on Time and Space, with the Big-O notation.

Voice rules:
  - First person ("I'd...", "Let's...", "Notice that..."). Sound like a tutor, not a textbook.
  - Short sentences. Streaming means the student reads as you type.
  - Don't apologize, don't hedge. Be decisive but explain WHY.
  - Never reveal the answer before you've explained the approach.
  - Always include the fenced ```python code block under the "## The clean solution" heading."""


def stream_live_solve(inp: SolutionInput) -> "Iterator[str]":
    """
    Stream the LLM solving the problem live. Yields plain-text chunks suitable
    for SSE forwarding. Raises LLMError if streaming isn't available (caller
    should surface a friendly message).
    """
    parts = [
        f"# Problem: {inp.problem_title} ({inp.difficulty})",
        f"## Statement\n{inp.statement_md}",
    ]
    if inp.constraints_md:
        parts.append(f"## Constraints\n{inp.constraints_md}")
    if inp.sample_cases:
        parts.append("## Sample cases")
        for c in inp.sample_cases[:3]:
            name = c.get("name") or ""
            parts.append(f"### {name}")
            parts.append(f"Input:\n```\n{c.get('input_blob', '')}\n```")
            parts.append(f"Expected:\n```\n{c.get('expected_blob', '')}\n```")
    if inp.starter_code_md:
        parts.append(
            "## Starter signature (match this exactly)\n"
            f"```{inp.language}\n{inp.starter_code_md}\n```"
        )
    parts.append(
        "Now solve the problem live, following the exact structure in your system instructions."
    )
    user_text = "\n\n".join(parts)

    yield from llm_client.call_text_stream(
        system=_LIVE_SOLVE_SYSTEM,
        user=user_text,
        max_tokens=6144,
        temperature=0.6,
    )


# Re-export at top of module so callers don't trip over forward refs
from typing import Iterator  # noqa: E402  (kept low for the local annotation)
