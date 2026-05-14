"""
Subprocess-based Python sandbox for student code.

Runs student-submitted Python code against a real interpreter and reports
authoritative pass/fail for each test case. The LLM evaluator then layers
qualitative feedback (severity, explanations, code quality) on top.

Design:
  - One subprocess per case (cross-platform timeout protection — Windows
    doesn't have signal.alarm).
  - The subprocess is `python -c <harness>` with the user's code + case
    payload piped in as JSON on stdin; result comes back as JSON on stdout.
  - Per-problem PROBLEM_CONFIGS map slug -> method/params/adapters. Some
    problems need input adaptation (linked list construction from list)
    or output normalization (sort-canonicalize for unordered output).
  - Timeout is 3 s per case; an empty/invalid response is treated as a
    failure on that case with `error` populated.

This is NOT a security sandbox — student code can still read files or open
sockets. For a school project that's fine; if we ever expose this externally
we'd run it in a Docker container with seccomp filters.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Literal

from pydantic import BaseModel

# --------------------------- Problem configuration -------------------------

class ProblemConfig(BaseModel):
    method: str                                                  # method name on Solution
    params: list[str]                                            # variable names in input_blob, in call order
    input_adapter: Literal["default", "linked_list"] = "default"
    output_adapter: Literal["default", "linked_list", "sorted_list_of_lists", "float_5dp"] = "default"


PROBLEM_CONFIGS: dict[str, ProblemConfig] = {
    "two-sum": ProblemConfig(method="twoSum", params=["nums", "target"]),
    "valid-parentheses": ProblemConfig(method="isValid", params=["s"]),
    "reverse-linked-list": ProblemConfig(
        method="reverseList", params=["head"],
        input_adapter="linked_list", output_adapter="linked_list",
    ),
    "climbing-stairs": ProblemConfig(method="climbStairs", params=["n"]),
    "best-time-to-buy-and-sell-stock": ProblemConfig(method="maxProfit", params=["prices"]),
    "maximum-subarray": ProblemConfig(method="maxSubArray", params=["nums"]),
    "container-with-most-water": ProblemConfig(method="maxArea", params=["height"]),
    "three-sum": ProblemConfig(method="threeSum", params=["nums"], output_adapter="sorted_list_of_lists"),
    "group-anagrams": ProblemConfig(method="groupAnagrams", params=["strs"], output_adapter="sorted_list_of_lists"),
    "number-of-islands": ProblemConfig(method="numIslands", params=["grid"]),
    "coin-change": ProblemConfig(method="coinChange", params=["coins", "amount"]),
    "longest-substring-without-repeating-characters": ProblemConfig(
        method="lengthOfLongestSubstring", params=["s"],
    ),
    "trapping-rain-water": ProblemConfig(method="trap", params=["height"]),
    "word-ladder": ProblemConfig(method="ladderLength", params=["beginWord", "endWord", "wordList"]),
    "median-of-two-sorted-arrays": ProblemConfig(
        method="findMedianSortedArrays", params=["nums1", "nums2"],
        output_adapter="float_5dp",
    ),
    # Easy (16-30)
    "contains-duplicate": ProblemConfig(method="containsDuplicate", params=["nums"]),
    "valid-anagram": ProblemConfig(method="isAnagram", params=["s", "t"]),
    "fizz-buzz": ProblemConfig(method="fizzBuzz", params=["n"]),
    "plus-one": ProblemConfig(method="plusOne", params=["digits"]),
    "single-number": ProblemConfig(method="singleNumber", params=["nums"]),
    "missing-number": ProblemConfig(method="missingNumber", params=["nums"]),
    "palindrome-number": ProblemConfig(method="isPalindrome", params=["x"]),
    "reverse-integer": ProblemConfig(method="reverse", params=["x"]),
    "roman-to-integer": ProblemConfig(method="romanToInt", params=["s"]),
    "majority-element": ProblemConfig(method="majorityElement", params=["nums"]),
    "move-zeroes": ProblemConfig(method="moveZeroes", params=["nums"]),
    "happy-number": ProblemConfig(method="isHappy", params=["n"]),
    "power-of-two": ProblemConfig(method="isPowerOfTwo", params=["n"]),
    "excel-sheet-column-number": ProblemConfig(method="titleToNumber", params=["columnTitle"]),
    "length-of-last-word": ProblemConfig(method="lengthOfLastWord", params=["s"]),
    # Medium (31-45)
    "product-of-array-except-self": ProblemConfig(method="productExceptSelf", params=["nums"]),
    "rotate-array": ProblemConfig(method="rotate", params=["nums", "k"]),
    "search-in-rotated-sorted-array": ProblemConfig(method="search", params=["nums", "target"]),
    "sort-colors": ProblemConfig(method="sortColors", params=["nums"]),
    "rotate-image": ProblemConfig(method="rotate", params=["matrix"]),
    "subsets": ProblemConfig(method="subsets", params=["nums"], output_adapter="sorted_list_of_lists"),
    "combination-sum": ProblemConfig(method="combinationSum", params=["candidates", "target"], output_adapter="sorted_list_of_lists"),
    "spiral-matrix": ProblemConfig(method="spiralOrder", params=["matrix"]),
    "unique-paths": ProblemConfig(method="uniquePaths", params=["m", "n"]),
    "minimum-path-sum": ProblemConfig(method="minPathSum", params=["grid"]),
    "jump-game": ProblemConfig(method="canJump", params=["nums"]),
    "word-break": ProblemConfig(method="wordBreak", params=["s", "wordDict"]),
    "longest-increasing-subsequence": ProblemConfig(method="lengthOfLIS", params=["nums"]),
    "house-robber": ProblemConfig(method="rob", params=["nums"]),
    "kth-largest-element-in-an-array": ProblemConfig(method="findKthLargest", params=["nums", "k"]),
    # Hard (46-55)
    "edit-distance": ProblemConfig(method="minDistance", params=["word1", "word2"]),
    "first-missing-positive": ProblemConfig(method="firstMissingPositive", params=["nums"]),
    "largest-rectangle-in-histogram": ProblemConfig(method="largestRectangleArea", params=["heights"]),
    "n-queens-count": ProblemConfig(method="totalNQueens", params=["n"]),
    "sliding-window-maximum": ProblemConfig(method="maxSlidingWindow", params=["nums", "k"]),
    "minimum-window-substring": ProblemConfig(method="minWindow", params=["s", "t"]),
    "burst-balloons": ProblemConfig(method="maxCoins", params=["nums"]),
    "wildcard-matching": ProblemConfig(method="isMatch", params=["s", "p"]),
    "regular-expression-matching": ProblemConfig(method="isMatch", params=["s", "p"]),
    "longest-valid-parentheses": ProblemConfig(method="longestValidParentheses", params=["s"]),
}


# --------------------------- Result model ---------------------------------

class CaseExecutionResult(BaseModel):
    case_index: int
    passed: bool
    actual_output: str        # canonical LC-style string ("" if error)
    expected_output: str      # normalized expected for comparison/display
    error: str | None = None  # exception class+message, or sandbox/config error
    timed_out: bool = False
    elapsed_ms: int = 0       # wall time the user method took (per case)
    peak_memory_kb: int = 0   # peak Python-allocated memory during user method


# --------------------------- Subprocess harness ---------------------------
# This string is executed as `python -c <_HARNESS>`. It reads a single JSON
# payload from stdin, runs the user's code against ONE case, and writes a
# single JSON object to stdout. All stderr is swallowed; failures are returned
# in the JSON's "error" field.

_HARNESS = r"""
import json
import sys
import time
import tracemalloc
import traceback

# ---- ListNode for linked-list problems ----
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def list_to_linked(lst):
    if not lst:
        return None
    head = ListNode(lst[0])
    cur = head
    for x in lst[1:]:
        cur.next = ListNode(x)
        cur = cur.next
    return head

def linked_to_list(head):
    out = []
    cur = head
    seen = set()  # cycle guard
    while cur is not None:
        if id(cur) in seen:
            out.append("...cycle...")
            break
        seen.add(id(cur))
        out.append(cur.val)
        cur = cur.next
    return out

def to_lc_str(v):
    # JSON's serialization matches LC's compact format almost exactly
    return json.dumps(v, separators=(',', ':'))

def adapt_output(value, kind):
    if kind == "linked_list":
        value = linked_to_list(value)
    elif kind == "sorted_list_of_lists":
        # Canonicalize: sort each inner list, then sort outer list by repr
        if isinstance(value, list):
            inner = []
            for x in value:
                if isinstance(x, list):
                    inner.append(sorted(x, key=lambda y: (type(y).__name__, y)))
                else:
                    inner.append(x)
            inner.sort(key=lambda x: json.dumps(x))
            value = inner
    elif kind == "float_5dp":
        try:
            return ("%.5f" % float(value))
        except (TypeError, ValueError):
            return to_lc_str(value)
    return to_lc_str(value)

try:
    payload = json.loads(sys.stdin.read())
    user_code = payload["user_code"]
    method_name = payload["method"]
    params = payload["params"]
    input_blob = payload["input_blob"]
    input_adapter = payload.get("input_adapter", "default")
    output_adapter = payload.get("output_adapter", "default")

    # Parse the input blob into named variables.
    input_ns = {}
    try:
        exec(compile(input_blob, "<input_blob>", "exec"), input_ns)
    except Exception as exc:
        print(json.dumps({
            "actual_output": "",
            "error": "Could not parse input case: " + repr(exc),
        }))
        sys.exit(0)

    args = []
    for name in params:
        if name not in input_ns:
            print(json.dumps({
                "actual_output": "",
                "error": "Input case missing variable '" + name + "'",
            }))
            sys.exit(0)
        v = input_ns[name]
        # Per-input adaptation. Only one adapter today (linked_list applies
        # to the FIRST list-shaped arg, which matches our 15-problem catalog).
        if input_adapter == "linked_list" and isinstance(v, list):
            v = list_to_linked(v)
        args.append(v)

    # Execute the user's code, surfacing ListNode (some solutions reference it
    # in type hints or stringified annotations).
    user_ns = {"ListNode": ListNode}
    try:
        exec(compile(user_code, "<user_code>", "exec"), user_ns)
    except Exception as exc:
        print(json.dumps({
            "actual_output": "",
            "error": type(exc).__name__ + " at import/compile: " + str(exc),
        }))
        sys.exit(0)

    Solution = user_ns.get("Solution")
    if Solution is None:
        print(json.dumps({
            "actual_output": "",
            "error": "No `class Solution` found in submission",
        }))
        sys.exit(0)

    instance = Solution()
    method = getattr(instance, method_name, None)
    if method is None:
        print(json.dumps({
            "actual_output": "",
            "error": "Solution has no method '" + method_name + "'",
        }))
        sys.exit(0)

    # Measure peak Python-allocated memory + wall time around the user method.
    # tracemalloc only tracks Python allocations (not C-extension arenas or
    # interpreter overhead), but for student-written algorithms it's the
    # dominant signal and ships in the stdlib (no new dependency).
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        result = method(*args)
    except Exception as exc:
        tracemalloc.stop()
        # Capture last frame in user_code only
        tb = traceback.extract_tb(exc.__traceback__)
        user_frames = [f for f in tb if f.filename == "<user_code>"]
        loc = ""
        if user_frames:
            f = user_frames[-1]
            loc = " (line " + str(f.lineno) + ")"
        print(json.dumps({
            "actual_output": "",
            "error": type(exc).__name__ + loc + ": " + str(exc),
            "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            "peak_memory_kb": 0,
        }))
        sys.exit(0)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_kb = max(1, int(peak_bytes / 1024))

    try:
        out_str = adapt_output(result, output_adapter)
    except Exception as exc:
        print(json.dumps({
            "actual_output": repr(result)[:200],
            "error": "Could not serialize return value: " + repr(exc),
            "elapsed_ms": elapsed_ms,
            "peak_memory_kb": peak_kb,
        }))
        sys.exit(0)

    print(json.dumps({
        "actual_output": out_str,
        "error": None,
        "elapsed_ms": elapsed_ms,
        "peak_memory_kb": peak_kb,
    }))
except Exception as exc:  # pragma: no cover — last-ditch harness safety
    print(json.dumps({
        "actual_output": "",
        "error": "Sandbox harness error: " + repr(exc),
    }))
"""


# --------------------------- Public API -----------------------------------

def _normalize_expected(expected_blob: str, output_adapter: str) -> str:
    """Apply the same canonicalization to expected_blob that adapt_output
    applies to actual values, so a string-equality compare works."""
    if output_adapter in ("default", "linked_list"):
        # Already in compact form, but tolerate extra whitespace
        return expected_blob.replace(" ", "").strip()
    if output_adapter == "float_5dp":
        try:
            return ("%.5f" % float(expected_blob.strip()))
        except ValueError:
            return expected_blob.strip()
    if output_adapter == "sorted_list_of_lists":
        try:
            parsed = json.loads(expected_blob.replace(" ", ""))
        except json.JSONDecodeError:
            return expected_blob.replace(" ", "").strip()
        if isinstance(parsed, list):
            inner: list = []
            for x in parsed:
                if isinstance(x, list):
                    inner.append(sorted(x, key=lambda y: (type(y).__name__, y)))
                else:
                    inner.append(x)
            inner.sort(key=lambda x: json.dumps(x))
            return json.dumps(inner, separators=(",", ":"))
        return expected_blob.replace(" ", "").strip()
    return expected_blob.strip()


def run_case(
    *,
    slug: str,
    user_code: str,
    input_blob: str,
    expected_blob: str,
    case_index: int,
    timeout: float = 3.0,
) -> CaseExecutionResult:
    """Run a single test case in a subprocess and decide pass/fail."""
    cfg = PROBLEM_CONFIGS.get(slug)
    if cfg is None:
        return CaseExecutionResult(
            case_index=case_index, passed=False, actual_output="",
            expected_output=expected_blob.strip(),
            error=f"No sandbox config for problem '{slug}'",
        )

    payload = {
        "user_code": user_code,
        "method": cfg.method,
        "params": cfg.params,
        "input_blob": input_blob,
        "input_adapter": cfg.input_adapter,
        "output_adapter": cfg.output_adapter,
    }

    expected_normalized = _normalize_expected(expected_blob, cfg.output_adapter)

    try:
        proc = subprocess.run(
            [sys.executable, "-c", _HARNESS],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CaseExecutionResult(
            case_index=case_index, passed=False, actual_output="",
            expected_output=expected_normalized,
            error=f"Timed out after {timeout}s", timed_out=True,
        )

    if proc.returncode != 0:
        return CaseExecutionResult(
            case_index=case_index, passed=False, actual_output="",
            expected_output=expected_normalized,
            error=f"Sandbox crashed (exit {proc.returncode}): {proc.stderr[-200:]}",
        )

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return CaseExecutionResult(
            case_index=case_index, passed=False, actual_output="",
            expected_output=expected_normalized,
            error=f"Non-JSON sandbox response: {proc.stdout[-200:]}",
        )

    err = result.get("error")
    actual = str(result.get("actual_output") or "")
    elapsed = int(result.get("elapsed_ms") or 0)
    peak_kb = int(result.get("peak_memory_kb") or 0)
    if err:
        return CaseExecutionResult(
            case_index=case_index, passed=False, actual_output=actual,
            expected_output=expected_normalized, error=err,
            elapsed_ms=elapsed, peak_memory_kb=peak_kb,
        )

    passed = actual == expected_normalized
    return CaseExecutionResult(
        case_index=case_index, passed=passed, actual_output=actual,
        expected_output=expected_normalized,
        elapsed_ms=elapsed, peak_memory_kb=peak_kb,
    )


def run_all_cases(
    *,
    slug: str,
    user_code: str,
    cases: list[dict],
    timeout_per_case: float = 3.0,
) -> list[CaseExecutionResult]:
    """
    Run a batch of cases. Each `case` dict has at least
    {case_index, input_blob, expected_blob}.

    Subprocesses run serially. Returns one result per case, in the same order.
    """
    out: list[CaseExecutionResult] = []
    for c in cases:
        out.append(run_case(
            slug=slug,
            user_code=user_code,
            input_blob=c["input_blob"],
            expected_blob=c["expected_blob"],
            case_index=c["case_index"],
            timeout=timeout_per_case,
        ))
    return out


__all__ = ["CaseExecutionResult", "ProblemConfig", "PROBLEM_CONFIGS", "run_case", "run_all_cases"]
