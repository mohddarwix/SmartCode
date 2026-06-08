"""
Thin wrapper around the Google Gemini SDK.

Design goals:
  - One place that knows how to talk to Gemini.
  - If `GOOGLE_API_KEY` is not configured, `is_available()` returns False and
    every other function refuses to call out. Callers then use a heuristic fallback.
  - Built-in JSON-extraction helper for prompts that ask Gemini to respond as JSON.
  - All SDK / network errors are caught and surfaced as `LLMError` so callers
    can degrade gracefully without leaking SDK internals.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterator

from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors

from ..config import settings

log = logging.getLogger("ai_tutor.llm")


class LLMError(RuntimeError):
    """Raised when an LLM call fails for any reason (no key, network, bad JSON)."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.llm_enabled:
            raise LLMError("GOOGLE_API_KEY is not set; LLM features are disabled.")
        _client = genai.Client(api_key=settings.google_api_key)
    return _client


def is_available() -> bool:
    """Cheap check used by callers to decide whether to even try the LLM path."""
    return settings.llm_enabled


def call_json(
    *, system: str, user: str, max_tokens: int | None = None
) -> dict[str, Any]:
    """Send a prompt and return parsed JSON.

    We ask Gemini to respond in `application/json` mode, which is enforced by
    the API. If the response still isn't valid JSON for some reason, we walk
    the text looking for a balanced object.
    """
    if not is_available():
        raise LLMError("LLM not configured.")

    # NOTE on `thinking_budget=0`:
    # Gemini 2.5 models default to "thinking mode" which eats output tokens
    # internally before producing a response. For structured JSON outputs we
    # don't need a thinking budget — disabling it ensures the full
    # max_output_tokens is available for the actual JSON body.
    config = genai_types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        max_output_tokens=max_tokens or settings.llm_max_tokens,
        temperature=0.4,
        thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
    )

    try:
        response = _get_client().models.generate_content(
            model=settings.llm_model,
            contents=user,
            config=config,
        )
    except genai_errors.APIError as exc:
        log.warning("Gemini API error: %s", exc)
        raise LLMError(f"LLM call failed: {exc}") from exc
    except Exception as exc:  # network errors etc.
        log.warning("LLM call error: %s", exc)
        raise LLMError(f"LLM call failed: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise LLMError("LLM returned an empty response.")

    return _extract_first_json_object(text)


def call_text_stream(
    *,
    system: str,
    user: str,
    max_tokens: int | None = None,
    temperature: float = 0.6,
) -> Iterator[str]:
    """Stream a text response from Gemini, chunk by chunk.

    Yields successive `str` chunks as soon as the model produces them. The full
    response is the concatenation of all chunks. Used for the "watch the AI
    solve" feature where we want the student to see the model think in real time.
    """
    if not is_available():
        raise LLMError("LLM not configured.")

    config = genai_types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens or settings.llm_max_tokens,
        temperature=temperature,
        thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
    )

    try:
        stream = _get_client().models.generate_content_stream(
            model=settings.llm_model,
            contents=user,
            config=config,
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text
    except genai_errors.APIError as exc:
        log.warning("Gemini streaming API error: %s", exc)
        raise LLMError(f"LLM stream failed: {exc}") from exc
    except Exception as exc:  # network / SDK errors
        log.warning("LLM streaming error: %s", exc)
        raise LLMError(f"LLM stream failed: {exc}") from exc


def _extract_first_json_object(text: str) -> dict[str, Any]:
    """Return the first balanced `{...}` block parsed as JSON."""
    # Fast path: try the whole thing.
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strip code fences and try again.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            result = json.loads(fenced.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # Last resort: brace-walker that finds the first balanced object.
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        break  # try the next opening brace
        start = text.find("{", start + 1)

    raise LLMError(
        f"LLM did not return valid JSON. Raw text (first 200 chars): {text[:200]}"
    )
