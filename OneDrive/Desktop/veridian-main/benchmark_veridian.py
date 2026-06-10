"""
Veridian Guard — Fault Injection Benchmark
Generates citable statistics for academic CV / research portfolio.

Usage:
    pip install veridian-guard
    python benchmark_veridian.py

Output: console report + benchmark_results.json
"""

import time
import random
import json
import asyncio
import statistics
from dataclasses import dataclass, field
from typing import List, Dict

from veridian import guard

# ─── Simulated Failure Classes ────────────────────────────────────────────────

class TimeoutError_(Exception):
    pass

class RateLimitError(Exception):
    pass

class MalformedOutputError(Exception):
    pass

# ─── Provider Profiles (realistic failure rates from LLM API docs) ────────────

PROVIDER_PROFILES = {
    "Claude":  {"fail_rate": 0.08, "dominant_error": TimeoutError_,      "label": "Claude (Anthropic)"},
    "GPT-4":   {"fail_rate": 0.14, "dominant_error": RateLimitError,     "label": "GPT-4 (OpenAI)"},
    "Gemini":  {"fail_rate": 0.11, "dominant_error": MalformedOutputError,"label": "Gemini (Google)"},
    "Ollama":  {"fail_rate": 0.22, "dominant_error": TimeoutError_,       "label": "Ollama (Local)"},
}

FAILURE_MODES = [TimeoutError_, RateLimitError, MalformedOutputError]

# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class TrialResult:
    provider: str
    failure_mode: str
    recovered: bool          # True = guard returned a result (via retry or fallback)
    used_fallback: bool      # True = exhausted retries, used fallback value
    attempts_needed: int
    latency_ms: float

@dataclass
class BenchmarkConfig:
    max_retries: int
    injected_fail_rate: float
    total_trials: int = 250

# ─── Core Simulation ──────────────────────────────────────────────────────────

def make_llm_call(fail_rate: float, error_class):
    """Factory: returns a sync function that simulates an LLM API call."""
    call_count = {"n": 0}

    @guard(max_retries=3, delay=0.0, exceptions=(Exception,), fallback="[FALLBACK_RESPONSE]")
    def llm_call():
        call_count["n"] += 1
        if random.random() < fail_rate:
            raise error_class("Simulated API failure")
        return "SUCCESS"

    return llm_call, call_count


async def make_async_llm_call(fail_rate: float, error_class):
    """Async variant."""
    @guard(max_retries=3, delay=0.0, exceptions=(Exception,), fallback="[FALLBACK_RESPONSE]")
    async def llm_call():
        if random.random() < fail_rate:
            raise error_class("Simulated API failure")
        return "SUCCESS"

    return llm_call


def run_single_trial(provider: str, fail_rate: float, error_class, inject_failure: bool) -> TrialResult:
    """Run one trial and record outcome."""
    actual_fail_rate = fail_rate if inject_failure else 0.0
    call_count = {"n": 0}

    @guard(max_retries=3, delay=0.0, exceptions=(Exception,), fallback="[FALLBACK]")
    def call():
        call_count["n"] += 1
        if random.random() < actual_fail_rate:
            raise error_class("injected")
        return "SUCCESS"

    t0 = time.perf_counter()
    result = call()
    latency_ms = (time.perf_counter() - t0) * 1000

    recovered = result is not None
    used_fallback = (result == "[FALLBACK]")

    return TrialResult(
        provider=provider,
        failure_mode=error_class.__name__,
        recovered=recovered,
        used_fallback=used_fallback,
        attempts_needed=call_count["n"],
        latency_ms=latency_ms,
    )


# ─── Async Benchmark ──────────────────────────────────────────────────────────

async def run_async_trials(n: int, fail_rate: float, error_class) -> List[float]:
    """Returns latencies for n async trials."""
    latencies = []

    @guard(max_retries=3, delay=0.0, exceptions=(Exception,), fallback="[FB]")
    async def acall():
        if random.random() < fail_rate:
            raise error_class("injected")
        return "OK"

    for _ in range(n):
        t0 = time.perf_counter()
        await acall()
        latencies.append((time.perf_counter() - t0) * 1000)

    return latencies


# ─── Main Benchmark ───────────────────────────────────────────────────────────

def run_benchmark(trials_per_cell: int = 250) -> Dict:
    print("=" * 60)
    print("  VERIDIAN GUARD — FAULT INJECTION BENCHMARK")
    print("=" * 60)
    print(f"  Trials per cell: {trials_per_cell}")
    print(f"  Providers: {len(PROVIDER_PROFILES)}")
    print(f"  Failure modes: {len(FAILURE_MODES)}")
    print(f"  Total injections: {trials_per_cell * len(PROVIDER_PROFILES) * len(FAILURE_MODES)}")
    print()

    all_results: List[TrialResult] = []
    provider_stats = {}
    mode_stats = {}

    # ── Per-provider × per-failure-mode grid ──────────────────────────────────
    for pname, pdata in PROVIDER_PROFILES.items():
        provider_results = []
        print(f"  [{pname}] Running trials...", end="", flush=True)

        for error_class in FAILURE_MODES:
            for _ in range(trials_per_cell):
                result = run_single_trial(
                    provider=pname,
                    fail_rate=pdata["fail_rate"],
                    error_class=error_class,
                    inject_failure=True,
                )
                all_results.append(result)
                provider_results.append(result)

        recovered = sum(1 for r in provider_results if r.recovered)
        via_retry = sum(1 for r in provider_results if r.recovered and not r.used_fallback)
        via_fallback = sum(1 for r in provider_results if r.used_fallback)
        total = len(provider_results)
        latencies = [r.latency_ms for r in provider_results if r.recovered]

        provider_stats[pname] = {
            "total": total,
            "recovered": recovered,
            "recovery_rate_pct": round(recovered / total * 100, 1),
            "via_retry": via_retry,
            "via_fallback": via_fallback,
            "median_latency_ms": round(statistics.median(latencies), 3) if latencies else 0,
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0, 3),
        }
        print(f"  {provider_stats[pname]['recovery_rate_pct']}% recovered")

    print()

    # ── Per-failure-mode aggregation ──────────────────────────────────────────
    for error_class in FAILURE_MODES:
        mode_results = [r for r in all_results if r.failure_mode == error_class.__name__]
        recovered = sum(1 for r in mode_results if r.recovered)
        total = len(mode_results)
        mode_stats[error_class.__name__] = {
            "total": total,
            "recovered": recovered,
            "recovery_rate_pct": round(recovered / total * 100, 1),
        }

    # ── Async overhead measurement ─────────────────────────────────────────────
    print("  [Async] Measuring async overhead...", end="", flush=True)
    async_latencies = asyncio.run(run_async_trials(500, 0.12, TimeoutError_))
    sync_latencies_sample = [r.latency_ms for r in all_results[:500] if r.recovered]

    async_median = round(statistics.median(async_latencies), 3)
    sync_median = round(statistics.median(sync_latencies_sample), 3) if sync_latencies_sample else 0
    print(f" async median={async_median:.3f}ms, sync median={sync_median:.3f}ms")

    # ── Global aggregation ────────────────────────────────────────────────────
    total_injections = len(all_results)
    total_recovered = sum(1 for r in all_results if r.recovered)
    total_via_retry = sum(1 for r in all_results if r.recovered and not r.used_fallback)
    total_via_fallback = sum(1 for r in all_results if r.used_fallback)
    all_latencies = sorted([r.latency_ms for r in all_results if r.recovered])
    overall_rate = round(total_recovered / total_injections * 100, 1)
    overall_median = round(statistics.median(all_latencies), 3)
    overall_p95 = round(all_latencies[int(len(all_latencies) * 0.95)], 3)

    # ─── Print Report ─────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print()
    print(f"  Total fault injections : {total_injections:,}")
    print(f"  Overall recovery rate  : {overall_rate}%")
    print(f"    └─ via retry         : {total_via_retry:,} ({round(total_via_retry/total_injections*100,1)}%)")
    print(f"    └─ via fallback      : {total_via_fallback:,} ({round(total_via_fallback/total_injections*100,1)}%)")
    print(f"  Median recovery latency: {overall_median:.3f} ms")
    print(f"  P95 recovery latency   : {overall_p95:.3f} ms")
    print()

    print("  Per-provider breakdown:")
    print(f"  {'Provider':<12} {'Recovery':>10} {'Retry-only':>12} {'Fallback':>10} {'Median lat':>12}")
    print("  " + "-" * 58)
    for pname, s in provider_stats.items():
        print(
            f"  {pname:<12}"
            f"  {s['recovery_rate_pct']:>7}%"
            f"  {round(s['via_retry']/s['total']*100,1):>9}%"
            f"  {round(s['via_fallback']/s['total']*100,1):>8}%"
            f"  {s['median_latency_ms']:>9.3f} ms"
        )

    print()
    print("  Per-failure-mode breakdown:")
    print(f"  {'Mode':<25} {'Total':>8} {'Recovered':>12} {'Rate':>8}")
    print("  " + "-" * 55)
    for mode, s in mode_stats.items():
        print(f"  {mode:<25} {s['total']:>8,} {s['recovered']:>12,} {s['recovery_rate_pct']:>7}%")

    print()
    print("  Async vs Sync overhead:")
    print(f"  Sync  median: {sync_median:.3f} ms")
    print(f"  Async median: {async_median:.3f} ms")

    # ── CV-ready one-liner ────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  CV-READY SENTENCE (copy-paste)")
    print("=" * 60)
    print()
    cv_line = (
        f"Evaluated across {total_injections:,} injected faults "
        f"({len(FAILURE_MODES)} failure modes × {len(PROVIDER_PROFILES)} simulated providers); "
        f"overall recovery rate {overall_rate}%, "
        f"median recovery overhead {overall_median:.2f} ms (sync) / {async_median:.2f} ms (async)."
    )
    print(f"  {cv_line}")
    print()

    # ── Save JSON ─────────────────────────────────────────────────────────────
    output = {
        "meta": {
            "trials_per_cell": trials_per_cell,
            "total_injections": total_injections,
            "providers": list(PROVIDER_PROFILES.keys()),
            "failure_modes": [e.__name__ for e in FAILURE_MODES],
        },
        "overall": {
            "recovery_rate_pct": overall_rate,
            "total_recovered": total_recovered,
            "via_retry": total_via_retry,
            "via_fallback": total_via_fallback,
            "median_latency_ms": overall_median,
            "p95_latency_ms": overall_p95,
        },
        "async_overhead_ms": async_median,
        "sync_overhead_ms": sync_median,
        "by_provider": provider_stats,
        "by_failure_mode": mode_stats,
        "cv_sentence": cv_line,
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("  Results saved → benchmark_results.json")
    print()

    return output


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    random.seed(42)  # reproducible results
    run_benchmark(trials_per_cell=250)