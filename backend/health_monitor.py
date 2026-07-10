#!/usr/bin/env python3
"""AI数字名片 — Health Monitor & Alerting Script.

Checks critical service endpoints, logs failures, and outputs JSON health reports.
Supports --once (single check) and --watch (continuous every 60s) modes.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8201"
ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/payment/products",
    "/api/v1/nfc/tap/stats",
]
FAILURE_THRESHOLD = 3  # consecutive failures before CRITICAL
WATCH_INTERVAL = 60    # seconds between checks in --watch mode
LOG_DIR = "/var/log/ai-digital-card"
LOG_FILE = os.path.join(LOG_DIR, "health_alerts.log")

# Per-endpoint state for consecutive-failure tracking
_consecutive_failures: dict[str, int] = {ep: 0 for ep in ENDPOINTS}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _fallback_log_dir() -> None:
    """Fallback when /var/log/ai-digital-card is not writable."""
    global LOG_DIR, LOG_FILE  # noqa: PLW0603
    fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(fallback, exist_ok=True)
    LOG_DIR = fallback
    LOG_FILE = os.path.join(LOG_DIR, "health_alerts.log")


def _ensure_log_dir() -> None:
    """Create the log directory (and parents) if it does not exist."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except PermissionError:
        _fallback_log_dir()


def _append_alert(message: str, level: str = "WARNING") -> None:
    """Append a timestamped alert line to the log file."""
    _ensure_log_dir()
    timestamp = _now_iso()
    line = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as exc:
        # Last resort: write to stderr if log file is unavailable
        print(f"CRITICAL: cannot write to {LOG_FILE}: {exc}", file=sys.stderr)


def _check_endpoint(endpoint: str, timeout: int = 10) -> dict:
    """Probe a single endpoint and return a result dictionary.

    Returns:
        {
            "endpoint": str,
            "status": "ok" | "error",
            "http_status": int | None,
            "latency_ms": float,
            "error": str | None,
        }
    """
    url = f"{BASE_URL}{endpoint}"
    start = time.perf_counter()

    result: dict = {
        "endpoint": endpoint,
        "status": "ok",
        "http_status": None,
        "latency_ms": 0.0,
        "error": None,
    }

    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            result["latency_ms"] = round(elapsed, 2)
            result["http_status"] = resp.status

            if resp.status != 200:
                result["status"] = "error"
                result["error"] = f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        elapsed = (time.perf_counter() - start) * 1000
        result["latency_ms"] = round(elapsed, 2)
        result["http_status"] = exc.code
        result["status"] = "error"
        result["error"] = f"HTTP {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        elapsed = (time.perf_counter() - start) * 1000
        result["latency_ms"] = round(elapsed, 2)
        result["status"] = "error"
        result["error"] = str(exc.reason)
    except TimeoutError:
        elapsed = (time.perf_counter() - start) * 1000
        result["latency_ms"] = round(elapsed, 2)
        result["status"] = "error"
        result["error"] = "timeout"

    return result


def _update_consecutive_count(endpoint: str, is_error: bool) -> int:
    """Update the consecutive-failure counter for an endpoint.

    Returns the current count *after* the update.
    """
    if is_error:
        _consecutive_failures[endpoint] += 1
    else:
        _consecutive_failures[endpoint] = 0
    return _consecutive_failures[endpoint]


# ── Core ───────────────────────────────────────────────────────────────────────

def run_checks() -> list[dict]:
    """Run health checks against all configured endpoints.

    Returns a list of result dictionaries (one per endpoint).
    Side effect: writes alerts to the log file for any failures.
    """
    overall_status = "healthy"
    results = []

    for endpoint in ENDPOINTS:
        check = _check_endpoint(endpoint)
        results.append(check)
        is_error = check["status"] == "error"

        # Update consecutive-failure counter
        consecutive = _update_consecutive_count(endpoint, is_error)

        if is_error:
            level = "CRITICAL" if consecutive >= FAILURE_THRESHOLD else "WARNING"
            _append_alert(
                f"{endpoint} — {check['error']} "
                f"(consecutive failures: {consecutive})",
                level=level,
            )
            overall_status = "degraded"

    return results


def build_report(results: list[dict]) -> dict:
    """Build a complete health report dictionary from check results."""
    total = len(results)
    failed = sum(1 for r in results if r["status"] == "error")
    ok = total - failed

    # Determine overall status string
    if failed == 0:
        overall = "healthy"
    elif failed == total:
        overall = "down"
    else:
        overall = "degraded"

    return {
        "timestamp": _now_iso(),
        "overall_status": overall,
        "summary": {
            "total": total,
            "ok": ok,
            "failed": failed,
        },
        "endpoints": results,
        "consecutive_failures": dict(_consecutive_failures),
    }


def print_report(report: dict) -> None:
    """Print the health report as pretty-printed JSON to stdout."""
    print(json.dumps(report, indent=2, ensure_ascii=False))


# ── CLI Modes ──────────────────────────────────────────────────────────────────

def mode_once() -> None:
    """Run a single health-check pass and print the report."""
    results = run_checks()
    report = build_report(results)
    print_report(report)

    # Exit with non-zero code if any endpoint failed
    if report["summary"]["failed"] > 0:
        sys.exit(1)


def mode_watch() -> None:
    """Run health checks continuously every WATCH_INTERVAL seconds."""
    print(f"Health monitor started — polling every {WATCH_INTERVAL}s "
          f"(endpoints: {', '.join(ENDPOINTS)})",
          flush=True)
    print(f"Logging alerts to: {LOG_FILE}", flush=True)
    print("-" * 60, flush=True)

    while True:
        results = run_checks()
        report = build_report(results)
        print_report(report)
        print(flush=True)

        time.sleep(WATCH_INTERVAL)


def print_usage() -> None:
    """Print usage information and exit."""
    prog = os.path.basename(sys.argv[0])
    print(f"Usage: {prog} [--once|--watch]")
    print()
    print("Options:")
    print("  --once    Run a single health check and print the report (default)")
    print("  --watch   Continuously poll every 60 seconds")
    print()
    print("Endpoints monitored:")
    for ep in ENDPOINTS:
        print(f"  {BASE_URL}{ep}")
    sys.exit(0)


# ── Entry Point ────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("-h", "--help"):
            print_usage()
        elif arg == "--once":
            mode_once()
        elif arg == "--watch":
            mode_watch()
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            print_usage()
    else:
        # Default to --once
        mode_once()


if __name__ == "__main__":
    main()
