from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime, timezone
import uuid
import json

from services.vision_service import VisionService
from services.estimation_service import EstimationService
from services.llm_service import LLMService
from services.multi_model_service import MultiModelService
from database.db import DatabaseService
from models.quote import QuoteResponse
from services.auth_service import AuthService, is_valid_email, normalize_email
from services.payment_service import PaymentService
from models.user import User

# Initialize FastAPI app
app = FastAPI(
    title="EstimateGenie API",
    description="AI-powered construction estimation backend",
    version="1.0.0"
)

# CORS middleware for frontend (configurable via ALLOW_ORIGINS / ALLOW_ORIGIN_REGEX)
allow_origins_env = os.getenv("ALLOW_ORIGINS")
allow_origin_regex_env = os.getenv("ALLOW_ORIGIN_REGEX")

# Explicit origins list (safe defaults)
if allow_origins_env:
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
else:
    allow_origins = [
        "https://estimategenie.net",
        "https://www.estimategenie.net",
        "https://estimategenie.pages.dev",  # Cloudflare Pages production
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

# Allow all preview deploys on Cloudflare Pages for this project (e.g., https://<hash>.estimategenie.pages.dev)
allow_origin_regex = allow_origin_regex_env or r"https://.*\.estimategenie\.pages\.dev"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vision_service = VisionService()
estimation_service = EstimationService()
llm_service = LLMService()
multi_model_service = MultiModelService()
db_service = DatabaseService()
auth_service = AuthService()
payment_service = PaymentService()

# Initialize authentication database on startup
auth_service.init_database()

# Database path for direct sqlite operations
DB_PATH = os.getenv("DATABASE_PATH", "estimategenie.db")
PASSWORD_MIN_LENGTH = 8

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

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class NewsletterSubscribeRequest(BaseModel):
    email: str

class ContactFormRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "vision": vision_service.is_ready(),
            "llm": llm_service.is_ready(),
            "database": db_service.is_connected()
        }
    }

# Lightweight ping endpoint for uptime checks and simple connectivity tests
@app.get("/api/v1/ping")
async def ping():
    return {
        "ok": True,
        "service": "EstimateGenie API",
        "version": "1.0.0",
        "time": datetime.now(timezone.utc).isoformat()
    }

# ============================================================================
# AI MODEL ENDPOINTS
# ============================================================================

@app.get("/api/v1/models/available")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "models": multi_model_service.get_available_models(),
        "preferred": multi_model_service.preferred_model
    }

@app.get("/api/v1/models/status")
async def get_models_status():
    """Get detailed status of all AI services"""
    return {
        "multi_model": {
            "ready": multi_model_service.is_ready(),
            "available": multi_model_service.available_models,
            "preferred": multi_model_service.preferred_model
        },
        "vision": {
            "ready": vision_service.is_ready(),
            "has_yolo": vision_service.has_yolo if hasattr(vision_service, 'has_yolo') else False
        },
        "llm": {
            "ready": llm_service.is_ready(),
            "provider": llm_service.provider if hasattr(llm_service, 'provider') else "unknown"
        }
    }

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    # Basic email normalization & validation (defense in depth; service also validates)
    incoming_email = request.email.strip().lower()
    if "@" not in incoming_email or len(incoming_email) < 5:
        raise HTTPException(status_code=400, detail="Invalid email format")
    request.email = incoming_email
    email = normalize_email(request.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if not request.password or len(request.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )
    
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    # Always register as 'free' - users upgrade via payment flow
    try:
        user = auth_service.register_user(
            email=email,
            name=name,
            password=request.password,
            plan="free"  # Force free plan on registration
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # If user requested pro plan in signup, return checkout info but keep them on free until payment completes
    if request.plan == "pro":
        if not payment_service.is_configured():
            raise HTTPException(status_code=503, detail="Payments are not configured. Please try again later or contact support.")
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
    email = normalize_email(request.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = auth_service.authenticate_user(email, request.password)
    
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
    
    if not request.new_password or len(request.new_password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"New password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )
    
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

@app.post("/api/v1/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    email = normalize_email(request.email)
    if not is_valid_email(email):
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    # Generate reset token
    reset_token = auth_service.create_password_reset_token(email)
    
    if not reset_token:
        # Return success even if email doesn't exist (security best practice)
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    # In production, send email here
    # For now, return the token (in production, this would be sent via email)
    reset_url = f"https://estimategenie.net/reset-password.html?token={reset_token}"
    
    return {
        "message": "If an account with that email exists, a password reset link has been sent.",
        "reset_url": reset_url,  # Remove this in production
        "token": reset_token  # Remove this in production
    }

@app.post("/api/v1/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    if not request.new_password or len(request.new_password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"New password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )
    
    success = auth_service.reset_password_with_token(request.token, request.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return {"message": "Password reset successfully. You can now login with your new password."}

# Get current user profile
@app.get("/v1/user/profile")
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get authenticated user's profile information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "plan": current_user.plan,
        "api_key": current_user.api_key,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "subscription_status": current_user.subscription_status,
        "quotes_used": current_user.quotes_used,
        "api_calls_used": current_user.api_calls_used,
        "plan_limits": current_user.get_plan_limits()
    }

# ============================================================================
# NEWSLETTER ENDPOINTS
# ============================================================================

@app.post("/api/v1/newsletter/subscribe")
async def subscribe_newsletter(request: NewsletterSubscribeRequest):
    """Subscribe to newsletter"""
    email = normalize_email(request.email)
    
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    # TODO: Integrate with actual email service (Mailchimp, SendGrid, etc.)
    # For now, just log and return success
    print(f"Newsletter subscription: {email}")
    
    # In production, you would:
    # 1. Store in newsletter_subscribers table
    # 2. Send confirmation email
    # 3. Add to email marketing platform
    
    return {
        "message": "Successfully subscribed! Check your email for confirmation.",
        "email": email
    }

# ============================================================================
# CONTACT FORM ENDPOINTS
# ============================================================================

@app.post("/api/v1/contact/submit")
async def submit_contact_form(request: ContactFormRequest):
    """Submit contact form"""
    # Validate inputs
    if not request.name or not request.email or not request.message:
        raise HTTPException(status_code=400, detail="Name, email, and message are required")
    
    email = normalize_email(request.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    # TODO: Send email notification to support team
    # For now, just log the submission
    print(f"Contact form submission from {request.name} ({email})")
    print(f"Subject: {request.subject}")
    print(f"Message: {request.message}")
    
    # In production, you would:
    # 1. Store in contact_submissions table
    # 2. Send email to support team
    # 3. Send auto-reply to user
    # 4. Create support ticket in system
    
    return {
        "message": "Thank you for contacting us! We'll get back to you shortly.",
        "submitted": True
    }

# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/payment/create-checkout-session")
async def create_checkout_session(
    request: Request,
    user = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
    # Only require API key for checkout (webhook secret is optional here)
    if not payment_service.is_configured(require_webhook=False):
        raise HTTPException(status_code=503, detail="Payments are not configured")
    
    body = await request.json()
    plan = body.get("plan", "professional")
    billing_period = body.get("billing_period", "monthly")
    success_url = body.get("success_url", "https://estimategenie.net/dashboard-new.html?subscription=success")
    cancel_url = body.get("cancel_url", "https://estimategenie.net/pricing.html?subscription=cancelled")
    
    # Map plan names to Stripe plan IDs
    plan_map = {
        "professional": "pro" if billing_period == "monthly" else "pro_annual",
        "business": "pro" if billing_period == "monthly" else "pro_annual",  # Using same for now
    }
    
    stripe_plan = plan_map.get(plan, "pro")
    
    # Create or get Stripe customer
    # get_current_user returns a User model instance
    customer_id = getattr(user, "stripe_customer_id", None)
    if not customer_id:
        # Create new customer
        # Safe casting to str to satisfy type expectations
        email_val = str(getattr(user, "email", ""))
        name_val = str(getattr(user, "name", email_val))
        customer_id = payment_service.create_customer(
            email=email_val,
            name=name_val
        )
        if customer_id:
            # Update user with customer ID
            auth_service.update_user_stripe_customer(getattr(user, "id"), customer_id)
    
    if not customer_id:
        raise HTTPException(status_code=500, detail="Failed to create customer")
    
    # Create checkout session
    session = payment_service.create_checkout_session(
        customer_id=customer_id,
        plan=stripe_plan,
        success_url=success_url,
        cancel_url=cancel_url,
    user_id=getattr(user, "id")
    )
    
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    
    return {
        "sessionId": session["session_id"],
        "url": session["url"]
    }

@app.post("/api/v1/payment/create-portal-session")
async def create_portal_session(user = Depends(get_current_user)):
    """Create Stripe billing portal session"""
    if not payment_service.is_configured():
        raise HTTPException(status_code=503, detail="Payments are not configured")
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
    if not payment_service.is_configured(require_webhook=True):
        raise HTTPException(status_code=503, detail="Payments are not configured")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # Validate signature header is present
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    event = payment_service.verify_webhook_signature(payload, sig_header)
    
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    success = payment_service.handle_webhook_event(event, auth_service)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process webhook")
    
    return {"status": "success"}

@app.get("/api/v1/webhooks/stripe")
async def stripe_webhook_info():
    """Informational endpoint for Stripe webhook (POST only accepted)"""
    return {
        "message": "This endpoint only accepts POST requests from Stripe",
        "configured": payment_service.is_configured(),
        "instructions": "Configure this URL in your Stripe Dashboard as a webhook endpoint",
        "url": "https://api.estimategenie.net/api/v1/webhooks/stripe",
        "method": "POST",
        "events": ["checkout.session.completed", "customer.subscription.updated", "customer.subscription.deleted", "invoice.payment_failed"]
    }

# Payment configuration status (simple readiness check)
@app.get("/api/v1/payment/status")
async def payment_status():
    return {"configured": payment_service.is_configured()}

# Get payment configuration (publishable key safe for frontend)
@app.get("/api/v1/payment/config")
async def payment_config():
    """Return client-safe Stripe configuration"""
    import os
    publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    if not publishable_key or publishable_key.startswith("sk_"):
        # Don't expose secret keys even if misconfigured
        return {
            "configured": False,
            "error": "Stripe publishable key not configured"
        }
    
    return {
        "configured": payment_service.is_configured(),
        "publishableKey": publishable_key
    }

# ============================================================================
# QUOTE ENDPOINTS (with authentication)
# ============================================================================

# Main estimation endpoint
@app.post("/v1/quotes", response_model=QuoteResponse)
async def create_quote(
    authorization: str = Header(None),
    file: Optional[UploadFile] = File(None),
    project_type: str = "general",
    description: str = "",
    options: str = "{}",
    model: str = "auto"
):
    """
    Upload an image and generate an AI-powered estimate.
    Requires authentication via Bearer token or API key.
    
    - **file**: Image file (JPEG, PNG)
    - **project_type**: Type of project (bathroom, kitchen, roofing, etc.)
    - **description**: Optional text description of the project
    - **options**: JSON string with advanced options (quality, contingency_pct, profit_pct, region)
    - **model**: AI model to use ("auto", "gemini", "gpt4v", "claude", "gpt-oss-20b")
    """
    
    # Authenticate user
    authorization_value = authorization.strip() if authorization else ""
    user: Optional[User] = None
    if authorization_value:
        if authorization_value.startswith("Bearer "):
            # JWT token
            token = authorization_value.replace("Bearer ", "", 1).strip()
            payload = auth_service.verify_token(token)
            if payload:
                user = auth_service.get_user_by_id(payload["sub"])
        else:
            # API key
            user = auth_service.get_user_by_api_key(authorization_value)
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please login or provide an API key.")
    
    if not file:
        raise HTTPException(status_code=400, detail="File is required for quote generation")
    
    # Check if user can generate quote
    if not user.can_generate_quote():
        limits = user.get_plan_limits()
        raise HTTPException(
            status_code=403, 
            detail=f"Quote limit reached. Your {user.plan} plan allows {limits['quotes_per_month']} quotes per month. Upgrade your plan to continue."
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique quote ID
    quote_id = f"quote_{uuid.uuid4().hex[:12]}"
    
    try:
        # Save uploaded image
        image_path = await vision_service.save_image(file, quote_id)
        
        # Step 1: Vision analysis
        vision_results = await vision_service.analyze_image(image_path, project_type)
        
        # Step 2: Use multi-model AI service for enhanced analysis
        if multi_model_service.is_ready():
            # Use advanced multi-model service
            # Cast model string to expected type
            model_type = model if model in ["gemini", "gpt4v", "claude", "gpt-oss-20b", "auto"] else "auto"
            ai_analysis = await multi_model_service.analyze_construction_image(
                image_path=image_path,
                project_type=project_type,
                description=description,
                model=model_type,  # type: ignore
                vision_results=vision_results
            )
            # Convert to reasoning format for backward compatibility
            reasoning = {
                "analysis": json.dumps(ai_analysis),
                "recommendations": ai_analysis.get("challenges", []),
                "materials_needed": ai_analysis.get("materials", [])
            }
        else:
            # Fallback to basic LLM service
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
            "user_id": user.id,
            "project_type": project_type,
            "image_path": image_path,
            "vision_results": vision_results,
            "reasoning": reasoning,
            "estimate": estimate,
            "status": "completed",
            "created_at": datetime.now(timezone.utc)
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
            created_at=datetime.now(timezone.utc)
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

# List all quotes (authenticated)
@app.get("/v1/quotes")
async def list_quotes(
    limit: int = 10,
    offset: int = 0,
    project_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List recent quotes for the authenticated user with optional filtering"""
    user_id = current_user.id
    quotes = await db_service.list_quotes(limit, offset, project_type, user_id=user_id)
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
