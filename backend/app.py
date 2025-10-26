from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime
import uuid

from services.vision_service import VisionService
from services.estimation_service import EstimationService
from services.llm_service import LLMService
from database.db import DatabaseService
from models.quote import QuoteResponse

# Initialize FastAPI app
app = FastAPI(
    title="EstimateGenie API",
    description="AI-powered construction estimation backend",
    version="1.0.0"
)

# CORS middleware for frontend (configurable via ALLOW_ORIGINS)
allow_origins_env = os.getenv("ALLOW_ORIGINS")
if allow_origins_env:
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
else:
    allow_origins = [
        "https://estimategenie.net",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vision_service = VisionService()
estimation_service = EstimationService()
llm_service = LLMService()
db_service = DatabaseService()

# Health check endpoint
@app.get("/")
async def root():
    return {
        "service": "EstimateGenie API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "vision": vision_service.is_ready(),
            "llm": llm_service.is_ready(),
            "database": db_service.is_connected()
        }
    }

# Main estimation endpoint
@app.post("/v1/quotes", response_model=QuoteResponse)
async def create_quote(
    file: UploadFile = File(...),
    project_type: str = "general",
    description: str = ""
):
    """
    Upload an image and generate an AI-powered estimate.
    
    - **file**: Image file (JPEG, PNG)
    - **project_type**: Type of project (bathroom, kitchen, roofing, etc.)
    - **description**: Optional text description of the project
    """
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique quote ID
    quote_id = f"quote_{uuid.uuid4().hex[:12]}"
    
    try:
        # Save uploaded image
        image_path = await vision_service.save_image(file, quote_id)
        
        # Step 1: Vision analysis
        vision_results = await vision_service.analyze_image(image_path, project_type)
        
        # Step 2: LLM reasoning
        reasoning = await llm_service.reason_about_project(
            vision_results,
            project_type,
            description
        )
        
        # Step 3: Generate estimate
        estimate = await estimation_service.calculate_estimate(
            vision_results,
            reasoning,
            project_type
        )
        
        # Step 4: Save to database
        quote_data = {
            "id": quote_id,
            "project_type": project_type,
            "image_path": image_path,
            "vision_results": vision_results,
            "reasoning": reasoning,
            "estimate": estimate,
            "status": "completed",
            "created_at": datetime.utcnow()
        }
        
        await db_service.save_quote(quote_data)
        
        # Return response
        return QuoteResponse(
            id=quote_id,
            status="completed",
            total_cost=estimate["total_cost"],
            timeline=estimate["timeline"],
            materials=estimate["materials"],
            labor=estimate["labor"],
            steps=estimate["steps"],
            confidence_score=estimate["confidence_score"],
            vision_analysis=vision_results,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"Error processing quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# Get quote by ID
@app.get("/v1/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str):
    """Retrieve a previously generated quote"""
    quote = await db_service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

# List all quotes
@app.get("/v1/quotes")
async def list_quotes(
    limit: int = 10,
    offset: int = 0,
    project_type: Optional[str] = None
):
    """List recent quotes with optional filtering"""
    quotes = await db_service.list_quotes(limit, offset, project_type)
    return quotes

# Update quote
@app.patch("/v1/quotes/{quote_id}")
async def update_quote(quote_id: str, updates: Dict[str, Any]):
    """Update a quote (manual adjustments)"""
    updated = await db_service.update_quote(quote_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"status": "updated", "quote_id": quote_id}

# Delete quote
@app.delete("/v1/quotes/{quote_id}")
async def delete_quote(quote_id: str):
    """Delete a quote"""
    deleted = await db_service.delete_quote(quote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"status": "deleted", "quote_id": quote_id}

# Material price lookup
@app.get("/v1/materials/search")
async def search_materials(query: str, limit: int = 10):
    """Search material database"""
    results = await estimation_service.search_materials(query, limit)
    return results

# Get labor rates
@app.get("/v1/labor/rates")
async def get_labor_rates(trade: Optional[str] = None):
    """Get current labor rates by trade"""
    rates = await estimation_service.get_labor_rates(trade)
    return rates

# Optional: force reload of external price lists
@app.post("/v1/pricing/reload")
async def pricing_reload():
    summary = estimation_service.reload_price_lists()
    return summary

# Optional: lookup price for a given key/name
@app.get("/v1/pricing/lookup")
async def pricing_lookup(key: str):
    return estimation_service.lookup_price(key)

# Optional: pricing system status
@app.get("/v1/pricing/status")
async def pricing_status():
    """Return pricing system status and configuration"""
    return {
        "external_files": [str(p) for p in estimation_service._external_price_files],
        "external_keys_count": len(estimation_service._external_keys),
        "total_materials_count": len(estimation_service.materials_db),
        "reload_interval_sec": estimation_service._price_list_reload_interval,
        "last_check_timestamp": estimation_service._price_list_last_check,
        "watsonx_enabled": estimation_service.pricing is not None,
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
