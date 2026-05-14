"""
Performance load test for NFR 3.2.6.

Targets each endpoint with N total requests at C concurrent threads.
Reports p50/p90/p99 latency, mean, max, and requests/sec.

Run:
    python deploy/perf_test.py --base https://lau-ai-tutor.duckdns.org

Output is printed as a markdown table you can paste straight into REPORT.md.
"""

from __future__ import annotations

import argparse
import json
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


@dataclass
class EndpointPlan:
    name: str
    method: str
    path: str
    body: dict | None = None
    needs_auth: bool = False


# Each scenario is repeated N times at C concurrency. Aim for ~30-60s total
# so we don't hammer the live demo box.
SCENARIOS = [
    EndpointPlan("GET /api/health (warm path)",        "GET",  "/api/health"),
    EndpointPlan("GET / (React SPA)",                  "GET",  "/"),
    EndpointPlan("POST /api/auth/login (DB + bcrypt)", "POST", "/api/auth/login",
                 body={"email": "alice@example.com", "password": "Test1234"}),
    EndpointPlan("GET /api/problems (auth + DB)",      "GET",  "/api/problems", needs_auth=True),
    EndpointPlan("GET /api/problems/1 (auth + detail)", "GET", "/api/problems/1", needs_auth=True),
]


def fetch_token(base: str, *, login_email: str, login_password: str) -> str:
    req = urllib.request.Request(
        base.rstrip("/") + "/api/auth/login",
        data=json.dumps({"email": login_email, "password": login_password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=_TLS_CTX, timeout=15) as r:
        return json.loads(r.read())["access_token"]


def one_request(base: str, plan: EndpointPlan, token: str | None) -> tuple[bool, float, int]:
    """Returns (ok, elapsed_seconds, status_code). Treats any exception as ok=False."""
    url = base.rstrip("/") + plan.path
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if plan.needs_auth and token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(plan.body).encode() if plan.body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=plan.method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, context=_TLS_CTX, timeout=20) as r:
            r.read()  # drain
            return True, time.perf_counter() - t0, r.status
    except urllib.error.HTTPError as e:
        # 4xx/5xx still counts as a "completed" request -- record the status.
        e.read()
        return e.code < 500, time.perf_counter() - t0, e.code
    except Exception:
        return False, time.perf_counter() - t0, 0


def run_scenario(base: str, plan: EndpointPlan, total: int, concurrency: int, token: str | None) -> dict:
    latencies: list[float] = []
    failures = 0
    status_counts: dict[int, int] = {}
    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(one_request, base, plan, token) for _ in range(total)]
        for f in as_completed(futures):
            ok, elapsed, status = f.result()
            latencies.append(elapsed * 1000.0)  # ms
            if not ok:
                failures += 1
            status_counts[status] = status_counts.get(status, 0) + 1
    wall = time.perf_counter() - wall_start
    latencies.sort()

    def pct(p: float) -> float:
        if not latencies:
            return 0.0
        i = max(0, min(len(latencies) - 1, int(round(p / 100 * (len(latencies) - 1)))))
        return latencies[i]

    return {
        "name": plan.name,
        "total": total,
        "concurrency": concurrency,
        "failures": failures,
        "status_counts": status_counts,
        "wall_s": round(wall, 2),
        "rps": round(total / wall, 1) if wall > 0 else 0,
        "p50_ms": round(pct(50), 1),
        "p90_ms": round(pct(90), 1),
        "p99_ms": round(pct(99), 1),
        "mean_ms": round(statistics.fmean(latencies), 1) if latencies else 0,
        "max_ms": round(max(latencies), 1) if latencies else 0,
    }


def print_markdown_table(rows: list[dict]) -> None:
    print()
    print("| Endpoint | N | Conc | RPS | p50 ms | p90 ms | p99 ms | mean ms | max ms | fail |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['name']} | {r['total']} | {r['concurrency']} | {r['rps']} | "
              f"{r['p50_ms']} | {r['p90_ms']} | {r['p99_ms']} | "
              f"{r['mean_ms']} | {r['max_ms']} | {r['failures']} |")
    print()
    # Also dump JSON for the report
    print("```json")
    print(json.dumps(rows, indent=2))
    print("```")


_TLS_CTX = ssl.create_default_context()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="e.g. https://lau-ai-tutor.duckdns.org")
    ap.add_argument("--total", type=int, default=200, help="requests per endpoint")
    ap.add_argument("--concurrency", type=int, default=20, help="concurrent threads")
    ap.add_argument("--email", default="alice@example.com")
    ap.add_argument("--password", default="Test1234")
    args = ap.parse_args()

    print(f"Target: {args.base}")
    print(f"Plan  : {args.total} requests per endpoint at {args.concurrency} concurrent threads")
    print()

    # Get a token first so the auth scenarios run
    try:
        token = fetch_token(args.base, login_email=args.email, login_password=args.password)
        print(f"[setup] obtained JWT for {args.email}")
    except Exception as exc:
        print(f"[setup] failed to login as {args.email}: {exc}", file=sys.stderr)
        sys.exit(2)

    rows = []
    for plan in SCENARIOS:
        print(f"  -> {plan.name}")
        rows.append(run_scenario(args.base, plan, args.total, args.concurrency, token))

    print_markdown_table(rows)


if __name__ == "__main__":
    main()
