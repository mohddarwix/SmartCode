"""
LLM-driven problem recommender.

Given a user's current skill profile and the catalogue of problems we have,
ask the LLM to pick THREE problems that target the user's weakest skills -
ordered best -> good fallback - so the student can choose. Each pick comes
with a one-sentence reason the student sees on screen.

Heuristic fallback (when LLM is unavailable or its response is invalid):
sort candidates by (overlap with weak skills DESC, difficulty ASC, id ASC)
and return the top three.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel

from . import client as llm_client

log = logging.getLogger("ai_tutor.llm.recommender")


class SkillScore(BaseModel):
    name: str
    score: int  # 0..100


class CatalogueProblem(BaseModel):
    problem_id: int
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    skills: list[str]
    is_solved: bool = False


class Pick(BaseModel):
    problem_id: int
    reason_md: str
    targeted_skills: list[str]


class RecommendationSet(BaseModel):
    picks: list[Pick]                  # 1..3 items; first is the strongest pick
    source: Literal["llm", "heuristic"]


_TARGET_PICKS = 3


_SYSTEM_PROMPT = f"""You are a problem-selection engine for a personalized programming tutor. You will be given:
  - The user's current skill profile (each skill 0-100).
  - The catalogue of available problems with title, difficulty, and the skills each problem trains.

Your job: pick THE {_TARGET_PICKS} BEST problems the student should try next, ordered from STRONGEST recommendation to GOOD-fallback. Across the three picks:
  1) the FIRST pick is the single best fit: trains 2-3 of the user's lowest-scoring skills AND matches their level,
  2) the OTHER picks should diversify - cover different weak skills or a different difficulty, so the student has real choice,
  3) never recommend a problem the user has already solved,
  4) don't recommend hard problems to a beginner or trivial ones to a strong student.

Respond with a single JSON object - no prose, no code fences:

{{
  "picks": [
    {{
      "problem_id": int,
      "reason_md": "1-2 sentence explanation the student will read, naming the skills it targets and why now",
      "targeted_skills": ["Skill A", "Skill B"]
    }},
    ...exactly {_TARGET_PICKS} entries, ordered best-first
  ]
}}

Each reason should sound encouraging and concrete (e.g. "Targets Edge Cases (45%) and Data Structures (65%) - your weakest areas - through stack-based string parsing.")."""


def recommend_problem(
    *,
    skills: list[SkillScore],
    catalogue: list[CatalogueProblem],
) -> RecommendationSet | None:
    """Try the LLM; fall back to heuristic. Returns None if no unsolved candidates."""
    candidates = [p for p in catalogue if not p.is_solved]
    if not candidates:
        return None

    if llm_client.is_available():
        try:
            return _recommend_with_llm(skills, candidates)
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM recommender failed, using heuristic: %s", exc)

    return _recommend_with_heuristic(skills, candidates)


# --------------------------- LLM path ---------------------------

def _recommend_with_llm(
    skills: list[SkillScore], candidates: list[CatalogueProblem]
) -> RecommendationSet:
    skill_block = "\n".join(f"- {s.name}: {s.score}/100" for s in skills) or "(no scores yet)"
    catalog_lines = []
    for p in candidates:
        catalog_lines.append(
            f"- id={p.problem_id} | {p.title} ({p.difficulty}) | skills: {', '.join(p.skills) or '-'}"
        )
    catalog_block = "\n".join(catalog_lines)

    user_text = (
        f"User skill profile:\n{skill_block}\n\n"
        f"Available problems the user hasn't solved:\n{catalog_block}\n\n"
        f"Pick the best {_TARGET_PICKS} problems."
    )

    raw = llm_client.call_json(system=_SYSTEM_PROMPT, user=user_text, max_tokens=1024)
    picks_raw = raw.get("picks") or []
    if not isinstance(picks_raw, list):
        raise ValueError("LLM 'picks' is not a list")

    valid_ids = {p.problem_id for p in candidates}
    picks: list[Pick] = []
    seen: set[int] = set()
    for pr in picks_raw:
        if not isinstance(pr, dict):
            continue
        try:
            pid = int(pr.get("problem_id", -1))
        except (TypeError, ValueError):
            continue
        if pid not in valid_ids or pid in seen:
            continue
        seen.add(pid)
        picks.append(Pick(
            problem_id=pid,
            reason_md=str(pr.get("reason_md") or "Recommended based on your skill profile."),
            targeted_skills=[str(s) for s in (pr.get("targeted_skills") or []) if isinstance(s, str)],
        ))
        if len(picks) >= _TARGET_PICKS:
            break

    if not picks:
        raise ValueError("LLM produced no valid picks")

    # Pad with the heuristic if the LLM returned fewer than 3 valid picks.
    if len(picks) < _TARGET_PICKS:
        remaining = [c for c in candidates if c.problem_id not in seen]
        if remaining:
            heur = _recommend_with_heuristic(skills, remaining)
            for hp in heur.picks:
                if hp.problem_id not in seen:
                    picks.append(hp)
                    seen.add(hp.problem_id)
                if len(picks) >= _TARGET_PICKS:
                    break

    return RecommendationSet(picks=picks, source="llm")


# --------------------------- Heuristic fallback ---------------------------

def _recommend_with_heuristic(
    skills: list[SkillScore], candidates: list[CatalogueProblem]
) -> RecommendationSet:
    """Pick up to 3 candidates: highest overlap with weak skills, then easiest, then lowest id."""
    sorted_weak = sorted(skills, key=lambda s: s.score)
    weak_names = [s.name for s in sorted_weak[:3]]
    difficulty_rank = {"easy": 0, "medium": 1, "hard": 2}

    def overlap(p: CatalogueProblem) -> int:
        return sum(1 for skill in p.skills if skill in weak_names)

    candidates_sorted = sorted(
        candidates,
        key=lambda p: (-overlap(p), difficulty_rank.get(p.difficulty, 99), p.problem_id),
    )

    picks: list[Pick] = []
    for c in candidates_sorted[:_TARGET_PICKS]:
        targeted = [s for s in c.skills if s in weak_names] or c.skills[:1]
        if targeted:
            reason = (
                f"Targets {', '.join(targeted)} - where your profile shows the most room to grow."
            )
        else:
            reason = "Suggested as a good next step based on your current level."
        picks.append(Pick(
            problem_id=c.problem_id,
            reason_md=reason,
            targeted_skills=targeted,
        ))

    return RecommendationSet(picks=picks, source="heuristic")


__all__ = [
    "SkillScore",
    "CatalogueProblem",
    "Pick",
    "RecommendationSet",
    "recommend_problem",
]
