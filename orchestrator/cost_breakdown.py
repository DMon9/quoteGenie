# orchestrator/cost_breakdown.py
from typing import List, Dict
from math import isfinite

DEFAULT_HOURLY_RATE = 50.0

def allocate_materials_cost(phases: List[Dict], total_materials_cost: float) -> List[Dict]:
    if total_materials_cost <= 0:
        for p in phases:
            p["materials_cost"] = 0.0
        return phases

    # allocate proportional to estimated_hours
    total_hours = sum(float(p.get("estimated_hours", 0) or 0) for p in phases) or 1
    for p in phases:
        hours = float(p.get("estimated_hours", 0) or 0)
        share = hours / total_hours
        p["materials_cost"] = round(total_materials_cost * share, 2)
    return phases

def allocate_labor_cost(phases: List[Dict], hourly_rate: float = DEFAULT_HOURLY_RATE) -> List[Dict]:
    for p in phases:
        hours = float(p.get("estimated_hours", 0) or 0)
        p["labor_cost"] = round(hours * hourly_rate, 2)
    return phases

def generate_cost_breakdown(phases: List[Dict], total_materials_cost: float, total_estimated_hours: float, hourly_rate: float = DEFAULT_HOURLY_RATE) -> Dict:
    """
    Returns:
    {
      "phases": [ {phase with materials_cost, labor_cost, total_cost}, ... ],
      "summary": { materials_total, labor_total, grand_total }
    }
    """
    # defensive copies
    phases_copy = [dict(p) for p in phases]
    allocate_materials_cost(phases_copy, total_materials_cost)
    allocate_labor_cost(phases_copy, hourly_rate)

    for p in phases_copy:
        mat = float(p.get("materials_cost", 0) or 0)
        lab = float(p.get("labor_cost", 0) or 0)
        p["phase_total"] = round(mat + lab, 2)

    materials_total = round(sum(float(p.get("materials_cost", 0) or 0) for p in phases_copy), 2)
    labor_total = round(sum(float(p.get("labor_cost", 0) or 0) for p in phases_copy), 2)
    grand_total = round(materials_total + labor_total, 2)

    # If grand_total is zero but user provided a 'total' (from LLM), reconcile:
    return {
        "phases": phases_copy,
        "summary": {
            "materials_total": materials_total,
            "labor_total": labor_total,
            "grand_total": grand_total,
            "reconciled_total": None
        }
    }
