"""
Interactive AI tutor: walks the student through ONE step at a time,
asks a comprehension question after each step, and only advances after
the student's answer shows understanding.

This is the LLM equivalent of a patient teacher -- never dumps the full
answer, builds the solution one insight at a time.

Stateless on the backend: the frontend keeps the conversation history
and replays it on every turn. The LLM decides whether to advance
(`step_index` bumps) or re-explain (`step_index` stays the same).
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic import BaseModel

from . import client as llm_client

log = logging.getLogger("ai_tutor.llm.interactive_tutor")


class TutorMessage(BaseModel):
    role: Literal["tutor", "student"]
    content: str
    step_index: Optional[int] = None  # only meaningful on tutor turns


class TutorInput(BaseModel):
    problem_title: str
    difficulty: Literal["easy", "medium", "hard"]
    statement_md: str
    constraints_md: Optional[str] = None
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None
    history: list[TutorMessage] = []
    student_message: Optional[str] = None   # None on the very first turn


class TutorTurn(BaseModel):
    tutor_response: str                     # markdown OK; ends with a check question unless is_complete
    step_index: int                         # 1..total_steps
    total_steps: int = 6
    is_complete: bool = False
    source: Literal["llm", "heuristic"] = "llm"


_TOTAL_STEPS = 6


_SYSTEM_PROMPT = f"""You are a patient, encouraging programming tutor guiding a student through ONE problem, step by step. You behave like a real teacher with a student: never dump the full solution; build understanding piece by piece.

You have a plan of {_TOTAL_STEPS} steps:
  1. Restate the problem. Make sure they understand what is being asked. Ask them to restate it in their own words or identify the input/output shape.
  2. Identify the trickiest input / edge case. Ask them what input would be easy to miss.
  3. Brute force. Have them propose the slow obvious approach. Ask its time complexity.
  4. Spot the bottleneck and the smart insight (e.g. hash map / two pointers / DP / monotonic stack). Reveal it ONLY after they have tried.
  5. Sketch the code together. Show ONE or two key lines, ask them to predict what comes next. Do not paste the whole solution.
  6. Trace through the sample case together, asking them to predict variable values along the way. End with "Nice -- you've got it!" and set is_complete=true.

PER-TURN RULES (very important):
- Keep each turn SHORT: 2-4 sentences of teaching + ONE check question. Never lecture.
- After the student answers, evaluate gently:
  * Right or close: brief affirmation ("Exactly." / "Right idea -- ...") then advance step_index by 1.
  * Partially right: name what they got, fill in the missing piece briefly, ask a follow-up that focuses on the gap. Keep step_index the same.
  * Wrong: do NOT correct them harshly. Give a small hint ("Think about what would happen if the array is empty -- what does your idea do then?") and re-ask. Keep step_index the same.
  * "I don't know" / silence: give ONE concrete nudge (a tiny example, a leading question) and ask again. Keep step_index the same.
- Always end with a single question (unless is_complete=true).
- Use Markdown sparingly: bold for KEY concepts, fenced ```python``` for tiny code snippets (max 5 lines).
- Tone: warm, like a TA who's done this 50 times. No emojis. No "great question!" sycophancy.

OUTPUT FORMAT (JSON only, no prose, no code fences):
{{
  "tutor_response": "<markdown message to the student, ending with the check question>",
  "step_index": <integer 1..{_TOTAL_STEPS}>,
  "total_steps": {_TOTAL_STEPS},
  "is_complete": <true ONLY after step {_TOTAL_STEPS}'s trace is complete>
}}
"""


def teach(payload: TutorInput) -> TutorTurn:
    """Run one tutor turn. Stateless: the full conversation comes in via `payload`."""
    if not llm_client.is_available():
        log.info("LLM unavailable, returning offline notice")
        return TutorTurn(
            tutor_response=(
                "The AI tutor is offline right now (the language model is unreachable). "
                "Try again in a minute, or use the cheatsheet drawer on the left for syntax help."
            ),
            step_index=1, total_steps=_TOTAL_STEPS, is_complete=False, source="heuristic",
        )

    user_text = _build_user_prompt(payload)
    try:
        raw = llm_client.call_json(system=_SYSTEM_PROMPT, user=user_text, max_tokens=900)
    except Exception as exc:  # noqa: BLE001
        log.warning("Tutor turn LLM call failed: %s", exc)
        return TutorTurn(
            tutor_response=(
                "The AI tutor hit a snag while thinking. Try sending your message again -- "
                "if it keeps failing, the language model may be rate-limited."
            ),
            step_index=_last_step_index(payload.history),
            total_steps=_TOTAL_STEPS, is_complete=False, source="heuristic",
        )

    response_text = str(raw.get("tutor_response") or "").strip()
    if not response_text:
        # Bad shape — degrade.
        return TutorTurn(
            tutor_response="(The tutor gave an empty response. Try sending again.)",
            step_index=_last_step_index(payload.history),
            total_steps=_TOTAL_STEPS, is_complete=False, source="heuristic",
        )

    try:
        step_index = int(raw.get("step_index", _last_step_index(payload.history)))
    except (TypeError, ValueError):
        step_index = _last_step_index(payload.history)
    step_index = max(1, min(step_index, _TOTAL_STEPS))

    is_complete = bool(raw.get("is_complete", False))

    return TutorTurn(
        tutor_response=response_text,
        step_index=step_index,
        total_steps=_TOTAL_STEPS,
        is_complete=is_complete,
        source="llm",
    )


def _last_step_index(history: list[TutorMessage]) -> int:
    for m in reversed(history):
        if m.role == "tutor" and m.step_index is not None:
            return m.step_index
    return 1


def _build_user_prompt(payload: TutorInput) -> str:
    sample_block = ""
    if payload.sample_input:
        sample_block = (
            f"\nSAMPLE INPUT:\n{payload.sample_input}\n"
            f"SAMPLE OUTPUT:\n{payload.sample_output or '(unspecified)'}\n"
        )

    if not payload.history:
        history_text = "(empty - this is the very first turn; greet the student and begin step 1)"
    else:
        lines = []
        for m in payload.history:
            tag = "TUTOR" if m.role == "tutor" else "STUDENT"
            step = f" [step {m.step_index}]" if m.step_index else ""
            lines.append(f"{tag}{step}: {m.content}")
        history_text = "\n".join(lines)

    student_block = (
        f"\nNEW STUDENT MESSAGE:\n{payload.student_message}\n"
        if payload.student_message
        else "\n(No new student message - this is the opening turn. Greet briefly and start step 1.)\n"
    )

    return (
        f"PROBLEM: {payload.problem_title} ({payload.difficulty})\n\n"
        f"STATEMENT:\n{payload.statement_md}\n\n"
        f"CONSTRAINTS:\n{payload.constraints_md or '(none provided)'}"
        f"{sample_block}\n"
        f"CONVERSATION SO FAR:\n{history_text}\n"
        f"{student_block}\n"
        "Produce your next turn now."
    )


__all__ = ["TutorInput", "TutorMessage", "TutorTurn", "teach"]
