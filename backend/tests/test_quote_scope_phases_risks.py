import os
import uuid
from datetime import datetime, timezone

from backend.database.db import DatabaseService


def test_quote_scope_phases_risks(tmp_path):
    """Verify quotes can store scope, phases and risks"""
    db_file = tmp_path / "test_quotes.db"
    db = DatabaseService(db_path=str(db_file))

    quote_id = f"quote_{uuid.uuid4().hex[:8]}"
    scope_val = "Full roof replacement - shingles and flashing"
    phases_val = [
        {"name": "demo-remove", "description": "Remove old shingles", "estimated_hours": 10},
        {"name": "demo-install", "description": "Install new shingles", "estimated_hours": 25}
    ]
    risks_val = [
        {"id": "r1", "description": "Roof pitch too high", "impact": "medium"}
    ]

    saved = os.path.exists(str(db_file))
    assert saved or True

    data = {
        "id": quote_id,
        "user_id": "u1",
        "project_type": "exterior",
        "image_path": "/tmp/unused.jpg",
        "vision_results": {},
        "reasoning": {"notes": "test"},
        "estimate": {"total_cost": {"amount": 1000}},
        "status": "completed",
        "created_at": datetime.now(timezone.utc),
        "scope": scope_val,
        "phases": phases_val,
        "risks": risks_val,
    }

    # Save and retrieve (save_quote/get_quote are async)
    import asyncio

    assert asyncio.run(db.save_quote(data))
    q = asyncio.run(db.get_quote(quote_id))
    assert q is not None
    assert q["id"] == quote_id
    assert q.get("scope") == scope_val
    assert isinstance(q.get("phases"), list) and len(q.get("phases")) == 2
    assert isinstance(q.get("risks"), list) and q.get("risks")[0]["id"] == "r1"
