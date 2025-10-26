from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json

from combiner import combine_outputs
from feedback_loop import save_feedback
from ai_chain import generate_structured_estimate
from phase_chain import generate_project_phases
from timeline import generate_timeline
from cost_breakdown import generate_cost_breakdown

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_URL = os.getenv("DATABASE_URL")

class QuoteRequest(BaseModel):
    description: str
    job_type: str = "general"


@app.post('/api/quote')
async def create_quote(
    description: str = Form(...),
    job_type: str = Form('general'),
    start_date: str | None = Form(None),
    hourly_rate: float = Form(50.0),
    file: UploadFile | None = None
):
    # 1) Generate structured estimate (LangChain)
    base_estimate_raw = generate_structured_estimate(description)
    try:
        base_estimate = json.loads(base_estimate_raw) if isinstance(base_estimate_raw, str) else base_estimate_raw
    except Exception:
        base_estimate = {"job_type": job_type, "materials_cost": 0, "labor_hours": 0, "explanation": str(base_estimate_raw)}

    # 2) Project phases (LangChain)
    phases_raw = generate_project_phases(description)
    try:
        phases = json.loads(phases_raw) if isinstance(phases_raw, str) else phases_raw
    except Exception:
        phases = [{
            "phase_name": "Complete Job",
            "objective": description,
            "estimated_hours": base_estimate.get("labor_hours", 1),
            "dependencies": None,
            "deliverables": []
        }]

    # 3) All LLM operations now go through ai_chain and phase_chain using the configured Ollama endpoint
    # No additional model enrichment calls needed; chains already use OLLAMA_BASE_URL
    
    # 4) Combine outputs & produce cost-per-phase via combiner
    combined = combine_outputs([base_estimate, {"phases": phases}])

    # 5) Generate timeline (business days) using provided start_date
    timeline = generate_timeline(combined.get("phases", []), start_date_str=start_date)
    combined["timeline"] = timeline

    return {"status": "ok", "quote": combined}

@app.post('/api/feedback')
async def feedback(quote_id: str = Form(...), corrections: str = Form(...)):
    # Save feedback & queue for LoRA adapter
    saved = save_feedback(quote_id, corrections)
    return {"status": "saved", "detail": saved}
