from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime
import uuid
import json

from services.vision_service import VisionService
from services.estimation_service import EstimationService
from services.llm_service import LLMService
from database.db import DatabaseService
from models.quote import QuoteResponse
from services.auth_service import AuthService
from services.payment_service import PaymentService
from models.user import User

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
auth_service = AuthService()
payment_service = PaymentService()

# Initialize authentication database on startup
auth_service.init_database()

# Database path for direct sqlite operations
DB_PATH = os.getenv("DATABASE_PATH", "estimategenie.db")

# Request/Response Models for Authentication
class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    plan: str = "free"

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    name: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Dependency for authentication
async def get_current_user(authorization: str = Header(None)):
    """Verify JWT token and return current user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = auth_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Debug endpoint for environment variables
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "llm_provider": os.getenv("LLM_PROVIDER", "not_set"),
        "google_api_key_present": bool(os.getenv("GOOGLE_API_KEY")),
        "google_api_key_length": len(os.getenv("GOOGLE_API_KEY", "")),
        "gemini_model": os.getenv("GEMINI_MODEL", "not_set"),
        "llm_service_ready": llm_service.is_ready(),
        "llm_service_provider": getattr(llm_service, 'provider', 'unknown'),
        "llm_service_google_api_key_present": bool(getattr(llm_service, 'google_api_key', None))
    }

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

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    user = auth_service.register_user(
        email=request.email,
        name=request.name,
        password=request.password,
        plan=request.plan
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # For pro plan, create Stripe customer and checkout session
    if request.plan == "pro":
        customer_id = payment_service.create_customer(request.email, request.name)
        if customer_id:
            # Update user with Stripe customer ID
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET stripe_customer_id = ? WHERE id = ?", (customer_id, user.id))
            conn.commit()
            conn.close()
            
            # Create checkout session
            checkout = payment_service.create_checkout_session(
                customer_id=customer_id,
                plan="pro",
                success_url="https://estimategenie.net/dashboard.html?payment=success",
                cancel_url="https://estimategenie.net/pricing.html?payment=canceled",
                user_id=user.id
            )
            
            if checkout:
                return {
                    "message": "User registered. Complete payment to activate Pro plan.",
                    "user": user.to_dict(),
                    "checkout_session_id": checkout["session_id"],
                    "checkout_url": checkout["url"]
                }
    
    # Free plan - generate token immediately
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(include_sensitive=True)
    }

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(include_sensitive=True)
    }

@app.get("/api/v1/auth/me")
async def get_me(user = Depends(get_current_user)):
    """Get current user information"""
    return user.to_dict(include_sensitive=True)

@app.get("/api/v1/auth/usage")
async def get_usage(user = Depends(get_current_user)):
    """Get user usage statistics"""
    return {
        "quotes_used": user.quotes_used,
        "api_calls_used": user.api_calls_used,
        "limits": user.get_plan_limits(),
        "can_generate_quote": user.can_generate_quote(),
        "can_use_api": user.can_use_api()
    }

@app.put("/api/v1/auth/update-profile")
async def update_profile(request: UpdateProfileRequest, user = Depends(get_current_user)):
    """Update user profile"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (request.name, user.id))
    conn.commit()
    conn.close()
    
    return {"message": "Profile updated successfully"}

@app.put("/api/v1/auth/change-password")
async def change_password(request: ChangePasswordRequest, user = Depends(get_current_user)):
    """Change user password"""
    if not user.verify_password(request.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hash = User.hash_password(request.new_password)
    
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user.id))
    conn.commit()
    conn.close()
    
    return {"message": "Password changed successfully"}

@app.post("/api/v1/auth/regenerate-key")
async def regenerate_api_key(user = Depends(get_current_user)):
    """Regenerate user API key"""
    new_key = User(id="", email="", name="", password_hash="")._generate_api_key()
    
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET api_key = ? WHERE id = ?", (new_key, user.id))
    conn.commit()
    conn.close()
    
    return {"api_key": new_key}

@app.delete("/api/v1/auth/delete-account")
async def delete_account(user = Depends(get_current_user)):
    """Delete user account"""
    if user.subscription_id:
        payment_service.cancel_subscription(user.subscription_id)
    
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user.id,))
    conn.commit()
    conn.close()
    
    return {"message": "Account deleted successfully"}

# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/payment/create-portal-session")
async def create_portal_session(user = Depends(get_current_user)):
    """Create Stripe billing portal session"""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No payment method on file")
    
    url = payment_service.create_portal_session(
        customer_id=user.stripe_customer_id,
        return_url="https://estimategenie.net/dashboard.html"
    )
    
    if not url:
        raise HTTPException(status_code=500, detail="Failed to create portal session")
    
    return {"url": url}

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = payment_service.verify_webhook_signature(payload, sig_header)
    
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    success = payment_service.handle_webhook_event(event, auth_service)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process webhook")
    
    return {"status": "success"}

# ============================================================================
# QUOTE ENDPOINTS (with authentication)
# ============================================================================

# Main estimation endpoint
@app.post("/v1/quotes", response_model=QuoteResponse)
async def create_quote(
    file: UploadFile = File(...),
    project_type: str = "general",
    description: str = "",
    options: str = "{}",
    authorization: str = Header(None)
):
    """
    Upload an image and generate an AI-powered estimate.
    Requires authentication via Bearer token or API key.
    
    - **file**: Image file (JPEG, PNG)
    - **project_type**: Type of project (bathroom, kitchen, roofing, etc.)
    - **description**: Optional text description of the project
    - **options**: JSON string with advanced options (quality, contingency_pct, profit_pct, region)
    """
    
    # Authenticate user
    user = None
    if authorization:
        if authorization.startswith("Bearer "):
            # JWT token
            token = authorization.replace("Bearer ", "")
            payload = auth_service.verify_token(token)
            if payload:
                user = auth_service.get_user_by_id(payload["sub"])
        else:
            # API key
            user = auth_service.get_user_by_api_key(authorization)
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please login or provide an API key.")
    
    # Check if user can generate quote
    if not user.can_generate_quote():
        limits = user.get_plan_limits()
        raise HTTPException(
            status_code=403, 
            detail=f"Quote limit reached. Your {user.plan} plan allows {limits['quotes_per_month']} quotes per month. Upgrade your plan to continue."
        )
    
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
        
        # Parse advanced options
        try:
            advanced_options = json.loads(options) if options else {}
        except Exception:
            advanced_options = {}
        
        # Step 3: Generate estimate with advanced options
        estimate = await estimation_service.calculate_estimate(
            vision_results,
            reasoning,
            project_type,
            advanced_options=advanced_options
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
        
        # Increment user usage
        user.increment_quote_usage()
        auth_service.update_user_usage(user.id, quotes_used=user.quotes_used)
        
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
            options_applied=estimate.get("options_applied"),
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
    # Respect environment variables for host/port and reload
    host = os.getenv("API_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("API_PORT", "8000"))
    except ValueError:
        port = 8000
    reload = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
    uvicorn.run("app:app", host=host, port=port, reload=reload)
