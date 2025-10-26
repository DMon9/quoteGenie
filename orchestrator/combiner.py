from typing import List, Dict
from cost_breakdown import generate_cost_breakdown

def combine_outputs(responses: List[Dict]) -> Dict:
    """
    Merge model outputs (estimates, phases, formatting).
    Expects responses to have keys like 'items', 'labor_hours', 'materials_cost', 'total', or phase lists.
    """
    final = {
        "items": [],
        "labor_hours": 0.0,
        "materials_cost": 0.0,
        "total": 0.0,
        "notes": []
    }
    phases = []

    for r in responses:
        if not r:
            continue
        if isinstance(r, dict) and r.get("error"):
            final["notes"].append({"model_error": r["error"]})
            continue

        # collect items
        items = r.get("items") or []
        final["items"].extend(items)

        # sums
        final["labor_hours"] += float(r.get("labor_hours", 0) or 0)
        final["materials_cost"] += float(r.get("materials_cost", 0) or 0)
        final["total"] += float(r.get("total", 0) or 0)

        # phases may be returned as list or stringified JSON
        p = r.get("phases")
        if p:
            # if string, try to parse
            if isinstance(p, str):
                try:
                    import json
                    parsed = json.loads(p)
                    phases.extend(parsed if isinstance(parsed, list) else [parsed])
                except Exception:
                    final["notes"].append({"phase_parse_error": "could not parse phases string"})
            elif isinstance(p, list):
                phases.extend(p)

    # Sanity checks / fallbacks
    if final["total"] == 0:
        final["total"] = round(final["materials_cost"] + (final["labor_hours"] * 50.0), 2)

    # If no explicit phases returned, create a single-phase fallback
    if not phases:
        phases = [{
            "phase_name": "Complete Job",
            "objective": "Full job completion",
            "estimated_hours": final["labor_hours"] or 1,
            "dependencies": None,
            "deliverables": final.get("items", [])
        }]

    # generate cost breakdown per phase (reconcile totals)
    cb = generate_cost_breakdown(phases, total_materials_cost=final["materials_cost"], total_estimated_hours=final["labor_hours"])

    combined = {
        "items": final["items"],
        "labor_hours": final["labor_hours"],
        "materials_cost": final["materials_cost"],
        "total": final["total"],
        "notes": final["notes"],
        "phases": cb["phases"],
        "cost_summary": cb["summary"]
    }
    # reconcile if model-provided total differs
    if combined["cost_summary"]["grand_total"] != 0 and combined["total"] and abs(combined["total"] - combined["cost_summary"]["grand_total"]) > 1:
        combined["cost_summary"]["reconciled_total"] = combined["total"]

    return combined
