"""
Health check for local model endpoints (Ollama and HF model_server containers).

This script probes the following by default:
- Ollama on ports 11434 (backend default) and 11435 (orchestrator default)
- HuggingFace model_server instances on ports 11400-11405 if running

It prints a concise PASS/FAIL summary and basic timings.

Run:
  D:/sd/Scripts/python.exe scripts/healthcheck_models.py
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


OLLAMA_PORTS = [
    11435,  # orchestrator default
    11434,  # backend default
]

# Common model_server ports we map in docker-compose.yml
MODEL_SERVER_PORTS = [11400, 11401, 11402, 11403, 11404, 11405, 11406, 11407]


@dataclass
class CheckResult:
    name: str
    ok: bool
    status: int | None
    latency_ms: int | None
    detail: str = ""


async def check_ollama(port: int, model_hint: Optional[str] = None) -> List[CheckResult]:
    base = f"http://localhost:{port}"
    results: List[CheckResult] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        # tags
        t0 = time.perf_counter()
        try:
            r = await client.get(f"{base}/api/tags")
            dt = int((time.perf_counter() - t0) * 1000)
            ok = r.status_code == 200
            detail = ""
            if ok:
                tags = [m.get("name", "?") for m in r.json().get("models", [])]
                detail = f"models: {', '.join(tags) or 'none'}"
            results.append(CheckResult(name=f"ollama:{port}/tags", ok=ok, status=r.status_code, latency_ms=dt, detail=detail))
        except Exception as e:
            results.append(CheckResult(name=f"ollama:{port}/tags", ok=False, status=None, latency_ms=None, detail=str(e)))

        # simple generate if we have a model to try
        model = model_hint or os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        payload = {"model": model, "prompt": "Say OK", "stream": False}
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{base}/api/generate", json=payload)
            dt = int((time.perf_counter() - t0) * 1000)
            ok = r.status_code == 200 and "OK" in r.json().get("response", "").upper()
            results.append(CheckResult(name=f"ollama:{port}/generate[{model}]", ok=ok, status=r.status_code, latency_ms=dt))
        except Exception as e:
            results.append(CheckResult(name=f"ollama:{port}/generate[{model}]", ok=False, status=None, latency_ms=None, detail=str(e)))

    return results


async def check_model_server(port: int) -> List[CheckResult]:
    base = f"http://localhost:{port}"
    results: List[CheckResult] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        # health
        t0 = time.perf_counter()
        try:
            r = await client.get(f"{base}/health")
            dt = int((time.perf_counter() - t0) * 1000)
            ok = r.status_code == 200 and bool(r.json().get("model_loaded"))
            desc = f"type={r.json().get('model_type')}, device={r.json().get('device')}"
            results.append(CheckResult(name=f"model_server:{port}/health", ok=ok, status=r.status_code, latency_ms=dt, detail=desc))
        except Exception as e:
            results.append(CheckResult(name=f"model_server:{port}/health", ok=False, status=None, latency_ms=None, detail=str(e)))
    return results


async def main() -> int:
    print("\n=== Model Health Check ===\n")
    tasks: List[asyncio.Task] = []

    for p in OLLAMA_PORTS:
        tasks.append(asyncio.create_task(check_ollama(p)))

    for p in MODEL_SERVER_PORTS:
        tasks.append(asyncio.create_task(check_model_server(p)))

    all_results: List[CheckResult] = []
    for t in tasks:
        res = await t
        all_results.extend(res)

    # Print summary
    passed = sum(1 for r in all_results if r.ok)
    total = len(all_results)

    for r in all_results:
        status_str = "PASS" if r.ok else "FAIL"
        lat = f"{r.latency_ms}ms" if r.latency_ms is not None else "-"
        extra = f" | {r.detail}" if r.detail else ""
        print(f"[{status_str}] {r.name} (status={r.status or '-'}, time={lat}){extra}")

    print(f"\nSummary: {passed}/{total} checks passed")
    return 0 if passed == total or passed > 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("Interrupted")
        raise SystemExit(130)
