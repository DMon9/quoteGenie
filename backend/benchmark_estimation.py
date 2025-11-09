"""Simple benchmark harness for estimation pipeline.

Measures:
- LLM reasoning latency (if provider ready, else fallback)
- Estimation service latency
- End-to-end latency (vision -> reasoning -> estimate)

Usage (PowerShell):
  C:\Users\user\quoteGenie\.venv-4\Scripts\python.exe backend\benchmark_estimation.py --iters 3 --provider fallback
  C:\Users\user\quoteGenie\.venv-4\Scripts\python.exe backend\benchmark_estimation.py --iters 3 --provider gemini
"""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from services.llm_service import LLMService
from services.estimation_service import EstimationService

FIXTURE = {
    'detections': [{'class': 'bathroom', 'confidence': 0.9}],
    'measurements': {'estimated_area_sqft': 50},
    'scene_description': 'Small bathroom with tub and vanity'
}

async def bench_once(llm: LLMService, est: EstimationService):
    t0 = time.perf_counter()
    result = await llm.reason_about_project(FIXTURE, 'bathroom', 'Benchmark run')
    t1 = time.perf_counter()
    estimate = await est.calculate_estimate(FIXTURE, result, 'bathroom')
    t2 = time.perf_counter()
    return (t1 - t0, t2 - t1, estimate)

async def main(iters: int):
    llm = LLMService()
    est = EstimationService()
    llm_times = []
    est_times = []

    for _ in range(iters):
        a, b, estimate = await bench_once(llm, est)
        llm_times.append(a)
        est_times.append(b)

    def stats(xs):
        return {
            'avg_ms': round(sum(xs) / len(xs) * 1000, 1),
            'min_ms': round(min(xs) * 1000, 1),
            'max_ms': round(max(xs) * 1000, 1)
        }

    print('\n=== Benchmark Results ===')
    print('LLM ready:', llm.is_ready(), 'provider:', llm.provider)
    print('LLM (ms):', stats(llm_times))
    print('Estimation (ms):', stats(est_times))
    total = estimate['total_cost']
    print('Total cost: $', round(total['amount'], 2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--iters', type=int, default=3)
    _ = parser.parse_args()
    asyncio.run(main(_ .iters))
