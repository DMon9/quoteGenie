# orchestrator/timeline.py
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from math import ceil
from typing import List, Dict

WORK_HOURS_PER_DAY = 8

def add_business_days(start_date: datetime, days: int) -> datetime:
    d = start_date
    added = 0
    while added < days:
        d += timedelta(days=1)
        # skip weekends
        if d.weekday() < 5:
            added += 1
    return d

def hours_to_business_days(hours: float) -> int:
    return max(1, ceil(hours / WORK_HOURS_PER_DAY))

def generate_timeline(phases: List[Dict], start_date_str: str | None = None) -> List[Dict]:
    """
    phases: list of dicts with keys: phase_name, estimated_hours, dependencies (optional)
    start_date_str: ISO date string or None -> uses today
    returns: list of phases augmented with start_date and end_date (ISO strings) and days_duration
    """
    if start_date_str:
        try:
            current = parse_date(start_date_str)
        except Exception:
            current = datetime.utcnow()
    else:
        current = datetime.utcnow()

    # normalize to next business day/time (start at 08:00)
    if current.weekday() >= 5:  # weekend -> move to next monday
        days_to_add = 7 - current.weekday()
        current = (current + timedelta(days=days_to_add)).replace(hour=8, minute=0, second=0, microsecond=0)
    else:
        current = current.replace(hour=8, minute=0, second=0, microsecond=0)

    timeline = []
    for p in phases:
        hours = float(p.get("estimated_hours", 1))
        days = hours_to_business_days(hours)
        start = current
        end = add_business_days(start, days - 1)  # inclusive of start day
        # set end to workday end (17:00)
        end = end.replace(hour=17, minute=0, second=0, microsecond=0)
        timeline.append({
            "phase_name": p.get("phase_name"),
            "objective": p.get("objective"),
            "estimated_hours": hours,
            "days_duration": days,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "dependencies": p.get("dependencies", None),
            "deliverables": p.get("deliverables", None)
        })
        # next phase starts next business day
        current = add_business_days(end, 1).replace(hour=8, minute=0, second=0, microsecond=0)

    return timeline
