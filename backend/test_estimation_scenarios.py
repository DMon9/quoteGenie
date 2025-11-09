"""Scenario tests that load vision fixtures and validate estimation outputs.

These tests use the EstimationService and LLMService fallback to validate that
material multipliers and regional adjustments are applied, without requiring
live provider keys. Provider tests are covered separately.
"""
import json
import os
import asyncio
from pathlib import Path
import pytest

from services.estimation_service import EstimationService

# Fixtures: (filename, project_type, min_total_cost, max_total_cost, markers)
FIXTURES = [
    ("bathroom_small.json", "bathroom", 800, 2500, ["small"]),
    ("bathroom_large.json", "bathroom", 1500, 5000, ["large"]),
    ("kitchen_medium.json", "kitchen", 2000, 8000, ["medium"]),
    ("kitchen_luxury.json", "kitchen", 5000, 20000, ["large", "expensive"]),
    ("exterior_deck.json", "exterior", 1000, 4000, ["medium"]),
    ("exterior_roof_replace.json", "exterior", 8000, 30000, ["large", "expensive"]),
    ("interior_painting_medium.json", "interior", 1500, 8000, ["medium"])
]

FIXTURE_DIR = Path(__file__).parent / "tests" / "fixtures"
if not FIXTURE_DIR.exists():
    # fallback in case of relative run
    FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name):
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def scenario_test(advanced_options=None):
    service = EstimationService()
    results = []
    for fname, project_type, min_cost, max_cost, markers in FIXTURES:
        vision = load_fixture(fname)
        reasoning = {
            "materials_needed": [
                {"name": "generic_material", "quantity": 100, "unit": "unit"}
            ],
            "analysis": {"labor_hours": 16}
        }
        estimate = asyncio.run(service.calculate_estimate(
            vision, reasoning, project_type, advanced_options=advanced_options or {}
        ))
        results.append((fname, estimate, min_cost, max_cost, markers))
    return results


@pytest.mark.small
def test_baseline_estimates():
    """Validate all fixtures produce positive costs within expected ranges."""
    results = scenario_test()
    test_results = []
    for fname, est, min_cost, max_cost, markers in results:
        total = est['total_cost']['amount']
        mats = est['total_cost']['breakdown']['materials']
        labor = est['total_cost']['breakdown']['labor']
        
        assert mats > 0, f"materials should be > 0 for {fname}"
        assert labor > 0, f"labor should be > 0 for {fname}"
        assert min_cost <= total <= max_cost, \
            f"{fname}: total ${total:.2f} outside expected range ${min_cost}-${max_cost}"
        
        test_results.append({
            "fixture": fname,
            "total_cost": round(total, 2),
            "materials": round(mats, 2),
            "labor": round(labor, 2),
            "min_expected": min_cost,
            "max_expected": max_cost,
            "in_range": min_cost <= total <= max_cost,
            "markers": markers
        })
    
    # Write summary artifact
    summary_path = Path(__file__).parent / "test_results_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"baseline_estimates": test_results}, f, indent=2)


@pytest.mark.small
def test_premium_quality_multiplier():
    base = scenario_test()
    premium = scenario_test({"quality": "premium"})
    # Compare first fixture as a representative
    mats_base = base[0][1]['total_cost']['breakdown']['materials']
    mats_prem = premium[0][1]['total_cost']['breakdown']['materials']
    assert mats_prem > mats_base * 1.2, "premium should increase materials by ~30%"


@pytest.mark.medium
def test_region_west_multiplier():
    base = scenario_test()
    west = scenario_test({"region": "west"})
    labor_base = base[0][1]['total_cost']['breakdown']['labor']
    labor_west = west[0][1]['total_cost']['breakdown']['labor']
    assert labor_west > labor_base * 1.25, "west region should increase labor ~35%"


@pytest.mark.large
def test_area_scaling_within_project_type():
    """Compare bathroom_small vs bathroom_large to ensure materials/labor scale up."""
    service = EstimationService()
    import asyncio
    small = load_fixture("bathroom_small.json")
    large = load_fixture("bathroom_large.json")
    reasoning = {"materials_needed": [{"name": "generic_material", "quantity": 100, "unit": "unit"}],
                 "analysis": {"labor_hours": 16}}
    est_small = asyncio.run(service.calculate_estimate(small, reasoning, "bathroom"))
    est_large = asyncio.run(service.calculate_estimate(large, reasoning, "bathroom"))
    mats_small = est_small['total_cost']['breakdown']['materials']
    mats_large = est_large['total_cost']['breakdown']['materials']
    assert mats_large > mats_small, "Larger bathroom should have higher material cost"
    labor_small = est_small['total_cost']['breakdown']['labor']
    labor_large = est_large['total_cost']['breakdown']['labor']
    assert labor_large >= labor_small, "Larger area should not reduce labor"
