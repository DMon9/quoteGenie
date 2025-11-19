from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime, timezone
import uuid
import json
import asyncio

import httpx

try:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
except ImportError:  # Sentry is optional; backend must still boot without it
    sentry_sdk = None
    SentryAsgiMiddleware = None

from services.vision_service import VisionService
from services.estimation_service import EstimationService
from services.llm_service import LLMService
from services.multi_model_service import MultiModelService
from database.db import DatabaseService
from models.quote import QuoteResponse
from pydantic import BaseModel, ValidationError


class OptionPhase(BaseModel):
    name: str
    description: str
    estimated_hours: float


class OptionRisk(BaseModel):
    id: str
    description: str
    impact: str


def validate_advanced_options(options: dict) -> dict:
    """Validate and normalize advanced `options` with phases and risks.

    - phases: list of objects with keys name, description, estimated_hours
    - risks: list of objects with keys id, description, impact (low/medium/high)
    """
    validated = {}

    # Copy simple keys
    for k in ("quality", "contingency_pct", "profit_pct", "region", "scope"):
        if k in options:
            validated[k] = options[k]

    # Validate phases
    phases = options.get("phases")
    if phases and isinstance(phases, list):
        out_phases = []
        for p in phases:
            try:
                ph = OptionPhase(**p)
                out_phases.append(ph.model_dump())
            except ValidationError:
                # skip invalid phase
                continue
        if out_phases:
            validated["phases"] = out_phases

    # Validate risks
    risks = options.get("risks")
    if risks and isinstance(risks, list):
        out_risks = []
        for r in risks:
            try:
                rk = OptionRisk(**r)
                # normalize impact levels
                impact = rk.impact.lower()
                if impact not in ("low", "medium", "high"):
                    impact = "medium"
                obj = rk.model_dump()
                obj["impact"] = impact
                out_risks.append(obj)
            except ValidationError:
                continue
        if out_risks:
            validated["risks"] = out_risks

    return validated
from services.auth_service import AuthService, is_valid_email, normalize_email
from services.auth0_service import Auth0Service
from services.payment_service import PaymentService
from models.user import User

# Initialize FastAPI app
app = FastAPI(
    title="EstimateGenie API",
    description="AI-powered construction estimation backend",
    version="1.0.0"
)

# Initialize Sentry if DSN present (should be set in deployment environment)
try:
    _sentry_dsn = os.getenv('SENTRY_DSN') or os.getenv('SENTRY_DSN_URL')
    if _sentry_dsn and sentry_sdk and SentryAsgiMiddleware:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=0.0,
            environment=os.getenv('ENV', 'production')
        )
        # Attach Sentry to ASGI app for automatic error capture
        app.add_middleware(SentryAsgiMiddleware)
        print('Sentry initialized with DSN')
    elif _sentry_dsn:
        print('Sentry DSN provided but sentry-sdk is not installed; skipping Sentry initialization')
    else:
        print('Sentry DSN not set; skipping Sentry initialization')
except Exception as e:
    print('Sentry initialization failed:', e)

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

# Uniform error payloads: include both `detail` (FastAPI default) and a `message` string
# so frontends can consistently display errors
from fastapi.exceptions import RequestValidationError as _RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    # If detail is a list/dict, create a simple message
    if isinstance(detail, list):
        msgs = []
        for d in detail:
            if isinstance(d, dict):
                msgs.append(d.get("msg") or d.get("detail") or d.get("message") or "Validation error")
        message = "; ".join([m for m in msgs if m]) or "Request error"
    elif isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or "Request error"
    else:
        message = str(detail)
    return JSONResponse(status_code=exc.status_code, content={
        "message": message,
        "detail": detail,
        "status_code": exc.status_code
    })

@app.exception_handler(_RequestValidationError)
async def validation_exception_handler(request: Request, exc: _RequestValidationError):
    # exc.errors() is a list with FastAPI validation details
    details = exc.errors()
    msgs = []
    for d in details:
        msg = d.get("msg")
        loc = d.get("loc")
        if loc and isinstance(loc, (list, tuple)) and len(loc) > 0:
            field = loc[-1]
            if isinstance(field, str):
                msg = f"{field}: {msg}"
        if msg:
            msgs.append(msg)
    message = "; ".join(msgs) if msgs else "Validation error"
    return JSONResponse(status_code=422, content={
        "message": message,
        "detail": details,
        "status_code": 422
    })

# Initialize services
vision_service = VisionService()
estimation_service = EstimationService()
llm_service = LLMService()
multi_model_service = MultiModelService()
db_service = DatabaseService()
auth_service = AuthService()
auth0_service = Auth0Service()
payment_service = PaymentService()

# Mount static files for Auth0 login pages
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize authentication database on startup
auth_service.init_database()

# Check if Auth0 is configured
if auth0_service.is_configured():
    print("✅ Auth0 configured and ready")
else:
    print("⚠️  Auth0 not configured - using local authentication")

# Database path for direct sqlite operations
DB_PATH = os.getenv("DATABASE_PATH", "estimategenie.db")
PASSWORD_MIN_LENGTH = 8

# Microservice URLs (can be local or remote)
VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://localhost:9001")
COST_SERVICE_URL = os.getenv("COST_SERVICE_URL", "http://localhost:9002")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:9003")

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

# Home: serve quote builder UI
@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # Fallback JSON if file missing
    return {
        "service": "EstimateGenie API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "auth0_enabled": auth0_service.is_configured()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "vision": vision_service.is_ready(),
            "llm": llm_service.is_ready(),
            "database": db_service.is_connected(),
            "auth0": auth0_service.is_configured()
        }
    }

# Auth0 Login Pages
@app.get("/login")
async def login_page():
    """Serve Auth0 login page"""
    return FileResponse(os.path.join(static_dir, "auth0-login.html"))

@app.get("/callback")
async def callback_page():
    """Serve Auth0 callback page"""
    return FileResponse(os.path.join(static_dir, "auth0-callback.html"))


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

# Auth0 Endpoints
@app.get("/api/v1/auth/auth0/login-url")
async def get_auth0_login_url(redirect_uri: str = "http://localhost:3000/callback"):
    """Get Auth0 login URL"""
    if not auth0_service.is_configured():
        raise HTTPException(status_code=503, detail="Auth0 is not configured")
    
    import secrets
    state = secrets.token_urlsafe(32)
    auth_url = auth0_service.get_authorization_url(redirect_uri, state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }

@app.post("/api/v1/auth/auth0/callback")
async def auth0_callback(code: str, redirect_uri: str):
    """Handle Auth0 callback and exchange code for token"""
    if not auth0_service.is_configured():
        raise HTTPException(status_code=503, detail="Auth0 is not configured")
    
    # Exchange code for token
    token_data = await auth0_service.exchange_code_for_token(code, redirect_uri)
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    # Verify the access token
    payload = await auth0_service.verify_token(token_data.get("access_token", ""))
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user info from Auth0
    auth0_user_id = payload.get("sub")
    user_info = auth0_service.get_user_info(auth0_user_id)
    
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user exists in local database, if not create them
    email = user_info.get("email")
    name = user_info.get("name", email)
    
    # Try to find existing user
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        user = User(
            id=row["id"],
            email=row["email"],
            name=row["name"],
            password_hash=row["password_hash"],
            plan=row["plan"],
            api_key=row["api_key"]
        )
    else:
        # Create new user
        import uuid
        user_id = str(uuid.uuid4())
        api_key = User(id="", email="", name="", password_hash="")._generate_api_key()
        
        cursor.execute("""
            INSERT INTO users (id, email, name, password_hash, plan, api_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (user_id, email, name, "auth0", "free", api_key))
        conn.commit()
        
        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash="auth0",
            plan="free",
            api_key=api_key
        )
    
    conn.close()
    
    # Create our own JWT token for the user
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(include_sensitive=True),
        "auth0_token": token_data.get("access_token")
    }

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
        
        # Parse and validate advanced options
        try:
            advanced_options = json.loads(options) if options else {}
            advanced_options = validate_advanced_options(advanced_options)
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
            "scope": advanced_options.get("scope"),
            "phases": advanced_options.get("phases"),
            "risks": advanced_options.get("risks"),
            "status": "completed",
            "created_at": datetime.now(timezone.utc)
        }
        
        await db_service.save_quote(quote_data)
        
        # Increment user usage
        user.increment_quote_usage()
        auth_service.update_user_usage(user.id, quotes_used=user.quotes_used)
        
        # Convert estimate data to proper types
        from models.quote import Material, LaborItem, Timeline, WorkStep, Phase, RiskItem
        
        # Build timeline object
        timeline_data = estimate["timeline"]
        timeline_obj = Timeline(
            estimated_hours=timeline_data.get("estimated_hours", 0),
            estimated_days=timeline_data.get("estimated_days", 1),
            min_days=timeline_data.get("min_days", 1),
            max_days=timeline_data.get("max_days", 1)
        )
        
        # Build materials list
        materials_list = [
            Material(
                name=m.get("name", ""),
                quantity=m.get("quantity", 0),
                unit=m.get("unit", "unit"),
                unit_price=m.get("unit_price", 0),
                total=m.get("total", 0)
            )
            for m in estimate.get("materials", [])
        ]
        
        # Build labor list
        labor_list = [
            LaborItem(
                trade=l.get("trade", ""),
                hours=l.get("hours", 0),
                rate=l.get("rate", 0),
                total=l.get("total", 0)
            )
            for l in estimate.get("labor", [])
        ]
        
        # Build steps list
        steps_list = [
            WorkStep(
                order=s.get("order", 0),
                description=s.get("description", ""),
                duration=s.get("duration", "")
            )
            for s in estimate.get("steps", [])
        ]
        
        # Build phases list if present
        phases_list = None
        if advanced_options.get("phases"):
            phases_list = [
                Phase(
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    estimated_hours=p.get("estimated_hours", 0)
                )
                for p in advanced_options.get("phases", [])
            ]
        
        # Build risks list if present
        risks_list = None
        if advanced_options.get("risks"):
            risks_list = [
                RiskItem(
                    id=r.get("id", ""),
                    description=r.get("description", ""),
                    impact=r.get("impact", "medium")
                )
                for r in advanced_options.get("risks", [])
            ]
        
        # Return response
        return QuoteResponse(
            id=quote_id,
            status="completed",
            total_cost=estimate["total_cost"],
            timeline=timeline_obj,
            materials=materials_list,
            labor=labor_list,
            steps=steps_list,
            confidence_score=estimate["confidence_score"],
            vision_analysis=vision_results,
            options_applied=estimate.get("options_applied"),
            scope=advanced_options.get("scope"),
            phases=phases_list,
            risks=risks_list,
            created_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        print(f"Error processing quote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

# Get quote by ID
@app.get("/v1/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str):
    """Retrieve a previously generated quote"""
    from models.quote import Material, LaborItem, Timeline, WorkStep, Phase, RiskItem
    
    quote = await db_service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    est = quote.get("estimate") or {}
    try:
        created_at = quote.get("created_at")
        created_dt = datetime.fromisoformat(created_at) if isinstance(created_at, str) else datetime.now(timezone.utc)
    except Exception:
        created_dt = datetime.now(timezone.utc)
    
    # Build timeline object
    timeline_data = est.get("timeline") or {"estimated_hours": 0, "estimated_days": 1, "min_days": 1, "max_days": 1}
    timeline_obj = Timeline(
        estimated_hours=timeline_data.get("estimated_hours", 0),
        estimated_days=timeline_data.get("estimated_days", 1),
        min_days=timeline_data.get("min_days", 1),
        max_days=timeline_data.get("max_days", 1)
    )
    
    # Build materials list
    materials_list = [
        Material(
            name=m.get("name", ""),
            quantity=m.get("quantity", 0),
            unit=m.get("unit", "unit"),
            unit_price=m.get("unit_price", 0),
            total=m.get("total", 0)
        )
        for m in est.get("materials", [])
    ]
    
    # Build labor list
    labor_list = [
        LaborItem(
            trade=l.get("trade", ""),
            hours=l.get("hours", 0),
            rate=l.get("rate", 0),
            total=l.get("total", 0)
        )
        for l in est.get("labor", [])
    ]
    
    # Build steps list
    steps_list = [
        WorkStep(
            order=s.get("order", 0),
            description=s.get("description", ""),
            duration=s.get("duration", "")
        )
        for s in est.get("steps", [])
    ]
    
    # Build phases list if present
    phases_list = None
    if quote.get("phases"):
        phases_list = [
            Phase(
                name=p.get("name", ""),
                description=p.get("description", ""),
                estimated_hours=p.get("estimated_hours", 0)
            )
            for p in quote.get("phases", [])
        ]
    
    # Build risks list if present
    risks_list = None
    if quote.get("risks"):
        risks_list = [
            RiskItem(
                id=r.get("id", ""),
                description=r.get("description", ""),
                impact=r.get("impact", "medium")
            )
            for r in quote.get("risks", [])
        ]
    
    return QuoteResponse(
        id=quote.get("id"),
        status=quote.get("status", "processing"),
        total_cost=est.get("total_cost") or {},
        timeline=timeline_obj,
        materials=materials_list,
        labor=labor_list,
        steps=steps_list,
        confidence_score=est.get("confidence_score", 0.0),
        vision_analysis=quote.get("vision_results"),
        options_applied=est.get("options_applied"),
        scope=quote.get("scope"),
        phases=phases_list,
        risks=risks_list,
        created_at=created_dt
    )

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

# ============================================================================
# ASYNC QUOTE PIPELINE (Microservices Orchestration)
# ============================================================================

async def _run_quote_pipeline(
    quote_id: str,
    user_id: str,
    image_path: str,
    project_type: str,
    description: str,
    options: Dict[str, Any],
):
    """Coordinated async pipeline across microservices (vision -> cost -> llm)."""
    try:
        # Helper: internal synchronous fallback using built-in services
        async def _internal_fallback():
            try:
                vr = await vision_service.analyze_image(image_path, project_type)
            except Exception as e:
                vr = {"error": f"internal vision failed: {e}"}
            try:
                reasoning = await llm_service.reason_about_project(vr, project_type, description)
            except Exception as e:
                reasoning = {"analysis": "{}", "recommendations": [f"llm fallback: {e}"], "materials_needed": []}
            estimate = await estimation_service.calculate_estimate(vr, reasoning, project_type, advanced_options=options)
            await db_service.update_quote(quote_id, {"vision_results": vr, "estimate": estimate, "reasoning": reasoning, "status": "completed"})
            return True

        # 1) Vision service
        vision_results: Dict[str, Any] = {}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                file_name = os.path.basename(image_path)
                mime = "image/jpeg" if file_name.lower().endswith((".jpg", ".jpeg")) else "image/png"
                with open(image_path, "rb") as f:
                    files = {"file": (file_name, f.read(), mime)}
                resp = await client.post(f"{VISION_SERVICE_URL}/infer", files=files)
                resp.raise_for_status()
                vision_results = resp.json()
            await db_service.update_quote(quote_id, {"vision_results": vision_results, "status": "vision_complete"})
        except Exception as e:
            # Fallback to internal pipeline
            await db_service.update_quote(quote_id, {"status": "vision_error", "reasoning": {"warn": f"vision microservice failed: {e}"}})
            ok = await _internal_fallback()
            if ok:
                return
            else:
                return

        # 2) Derive coarse materials from vision + project_type
        summary = vision_results.get("summary", {})
        total_area = 0.0
        try:
            for v in summary.values():
                total_area += float(v.get("total_area_sqft_est", 0.0))
        except Exception:
            total_area = 100.0
        total_area = max(total_area, 50.0)  # enforce minimum
        materials: List[Dict[str, Any]] = []
        if project_type.lower() == "bathroom":
            materials = [
                {"name": "Tile", "quantity": round(total_area, 2), "unit": "sqft"},
                {"name": "Grout", "quantity": round(total_area / 50.0, 2), "unit": "bags"},
                {"name": "Cement Backer Board", "quantity": round(total_area / 15.0, 2), "unit": "sheet"},
            ]
        elif project_type.lower() == "kitchen":
            materials = [
                {"name": "Backsplash tile", "quantity": round(min(total_area, 40.0), 2), "unit": "sqft"},
                {"name": "Cabinets", "quantity": 12, "unit": "linear_foot"},
                {"name": "Countertop", "quantity": 25, "unit": "sqft"},
            ]
        else:
            materials = [
                {"name": "Drywall", "quantity": round(total_area, 2), "unit": "sqft"},
                {"name": "Paint", "quantity": round(total_area / 350.0, 2), "unit": "gallon"},
            ]

        # 3) Cost service
        cost_baseline: Dict[str, Any] = {}
        try:
            cost_payload = {
                "zip": options.get("zip"),
                "region": options.get("region"),
                "project_type": project_type,
                "materials": materials,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{COST_SERVICE_URL}/estimate", json=cost_payload)
                resp.raise_for_status()
                cost_baseline = resp.json()
            await db_service.update_quote(quote_id, {"reasoning": {"cost_baseline": cost_baseline}, "status": "cost_complete"})
        except Exception as e:
            # Fallback to internal pipeline
            await db_service.update_quote(quote_id, {"status": "cost_error", "reasoning": {"warn": f"cost microservice failed: {e}"}})
            ok = await _internal_fallback()
            if ok:
                return
            else:
                return

        # 4) LLM service
        llm_output: Dict[str, Any] = {}
        try:
            compose_payload = {
                "user_inputs": {
                    "project_type": project_type,
                    "description": description,
                    "preferences": {k: v for k, v in options.items() if k in ("quality", "contingency_pct", "profit_pct")},
                },
                "vision": vision_results,
                "costs": cost_baseline,
                "template": {
                    "phases": ["inspection", "demolition", "rebuild", "finishing"],
                    "output": ["materials", "labor", "timeline", "steps", "risks", "total_cost", "notes"],
                },
                "model": options.get("llm_model", "gpt-4-turbo"),
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(f"{LLM_SERVICE_URL}/compose", json=compose_payload)
                resp.raise_for_status()
                data = resp.json()
                import json as _json
                llm_output = _json.loads(data.get("output") or "{}")
        except Exception as e:
            # proceed with cost baseline only; if nothing usable, fallback internal
            llm_output = {"error": str(e)}

        # 5) Build final estimate compatible with QuoteResponse
        try:
            materials_items = cost_baseline.get("materials", [])
            labor_items = cost_baseline.get("labor", [])
            totals = cost_baseline.get("totals", {})

            # Timeline
            timeline = llm_output.get("timeline") or {}
            if not timeline:
                # derive from labor hours
                hours = 0.0
                try:
                    hours = float(labor_items[0].get("hours", 8.0)) if labor_items else 8.0
                except Exception:
                    hours = 8.0
                timeline = {
                    "estimated_hours": hours,
                    "estimated_days": max(1, round(hours / 8.0)),
                    "min_days": max(1, round(hours / 8.0) - 1),
                    "max_days": max(1, round(hours / 8.0) + 2),
                }

            steps = llm_output.get("steps") or [
                {"order": 1, "description": "Site preparation and protection", "duration": "2 hours"},
                {"order": 2, "description": "Demolition (if required)", "duration": "4 hours"},
                {"order": 3, "description": "Installation of materials", "duration": "8 hours"},
                {"order": 4, "description": "Finishing and cleanup", "duration": "4 hours"},
            ]

            estimate = {
                "total_cost": {
                    "currency": "USD",
                    "amount": totals.get("total", 0.0),
                    "breakdown": {
                        "materials": totals.get("materials", 0.0),
                        "labor": totals.get("labor", 0.0),
                        "profit": 0.0,
                        "contingency": 0.0,
                    },
                },
                "materials": materials_items,
                "labor": labor_items,
                "timeline": timeline,
                "steps": steps,
                "confidence_score": 0.8,
                "options_applied": options,
            }

            await db_service.update_quote(quote_id, {"estimate": estimate, "reasoning": {"cost_baseline": cost_baseline, "llm": llm_output}, "status": "completed"})
        except Exception as e:
            # Final fallback to internal if composing failed unexpectedly
            await db_service.update_quote(quote_id, {"status": "error", "reasoning": {"warn": f"compose failed: {e}"}})
            await _internal_fallback()
    except Exception as e:
        # Catch any unexpected pipeline errors to avoid crashing worker
        try:
            await db_service.update_quote(quote_id, {"status": "error", "reasoning": {"error": f"pipeline failed: {e}"}})
        except Exception:
            pass


@app.post("/v1/quotes/async")
async def create_quote_async(
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    file: Optional[UploadFile] = File(None),
    project_type: str = "general",
    description: str = "",
    options: str = "{}",
    model: str = "auto",
):
    """Start asynchronous quote generation using microservices pipeline.

    Immediately returns a quote_id with status=processing. Client can poll /v1/quotes/{quote_id}.
    """

    # Authenticate user (same as sync endpoint)
    authorization_value = authorization.strip() if authorization else ""
    user: Optional[User] = None
    if authorization_value:
        if authorization_value.startswith("Bearer "):
            token = authorization_value.replace("Bearer ", "", 1).strip()
            payload = auth_service.verify_token(token)
            if payload:
                user = auth_service.get_user_by_id(payload["sub"])
        else:
            user = auth_service.get_user_by_api_key(authorization_value)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please login or provide an API key.")
    if not file:
        raise HTTPException(status_code=400, detail="File is required for quote generation")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Limits
    if not user.can_generate_quote():
        limits = user.get_plan_limits()
        raise HTTPException(
            status_code=403,
            detail=f"Quote limit reached. Your {user.plan} plan allows {limits['quotes_per_month']} quotes per month. Upgrade your plan to continue.",
        )

    quote_id = f"quote_{uuid.uuid4().hex[:12]}"
    try:
        image_path = await vision_service.save_image(file, quote_id)
        try:
            advanced_options = json.loads(options) if options else {}
        except Exception:
            advanced_options = {}
        # Save initial record
        await db_service.save_quote({
            "id": quote_id,
            "user_id": user.id,
            "project_type": project_type,
            "scope": advanced_options.get("scope"),
            "phases": advanced_options.get("phases"),
            "risks": advanced_options.get("risks"),
            "image_path": image_path,
            "vision_results": {},
            "reasoning": {"notes": "async pipeline started"},
            "estimate": {},
            "status": "processing",
            "created_at": datetime.now(timezone.utc),
        })

        # Increment user usage
        user.increment_quote_usage()
        auth_service.update_user_usage(user.id, quotes_used=user.quotes_used)

        # Launch background pipeline
        background_tasks.add_task(_run_quote_pipeline, quote_id, user.id, image_path, project_type, description, advanced_options)

        return {"quote_id": quote_id, "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e}")

# Demo quote endpoint (no authentication required)
@app.post("/v1/quotes/demo")
async def generate_demo_quote(project_type: Optional[str] = "general"):
    """
    Generate a demo quote without authentication.
    Used for trial flow to show AI capability without signup.
    
    - **project_type**: Type of demo (kitchen, bathroom, deck, custom)
    
    Returns mock estimate data for demonstration purposes.
    """
    demo_data = {
        "kitchen": {
            "estimate_low": 2450,
            "estimate_high": 3100,
            "estimate_mid": 2775,
            "timeline_days": 1.5,
            "timeline_hours": 16,
            "confidence_score": 0.87,
            "materials": [
                {"name": "Granite countertops", "quantity": 25, "unit": "sq ft", "unit_price": 45},
                {"name": "Cabinet replacement", "quantity": 1, "unit": "job", "unit_price": 1200},
                {"name": "Backsplash tile", "quantity": 40, "unit": "sq ft", "unit_price": 15},
                {"name": "Labor", "quantity": 16, "unit": "hours", "unit_price": 65}
            ]
        },
        "bathroom": {
            "estimate_low": 1800,
            "estimate_high": 2600,
            "estimate_mid": 2200,
            "timeline_days": 1,
            "timeline_hours": 12,
            "confidence_score": 0.84,
            "materials": [
                {"name": "Tile", "quantity": 100, "unit": "sq ft", "unit_price": 8},
                {"name": "Fixtures", "quantity": 3, "unit": "set", "unit_price": 300},
                {"name": "Mirror", "quantity": 1, "unit": "piece", "unit_price": 200},
                {"name": "Labor", "quantity": 12, "unit": "hours", "unit_price": 70}
            ]
        },
        "deck": {
            "estimate_low": 3200,
            "estimate_high": 4500,
            "estimate_mid": 3850,
            "timeline_days": 2,
            "timeline_hours": 20,
            "confidence_score": 0.91,
            "materials": [
                {"name": "Pressure-treated lumber", "quantity": 400, "unit": "board ft", "unit_price": 2.50},
                {"name": "Deck screws", "quantity": 5, "unit": "lbs", "unit_price": 12},
                {"name": "Railings", "quantity": 40, "unit": "linear ft", "unit_price": 30},
                {"name": "Labor", "quantity": 20, "unit": "hours", "unit_price": 60}
            ]
        }
    }
    
    # Get data for requested project type, default to kitchen
    data = demo_data.get(project_type, demo_data["kitchen"])
    
    return {
        "quote_id": f"demo-{uuid.uuid4()}",
        "project_type": project_type,
        "estimate": {
            "low": data["estimate_low"],
            "high": data["estimate_high"],
            "mid": data["estimate_mid"],
            "currency": "USD"
        },
        "timeline": {
            "days": data["timeline_days"],
            "hours": data["timeline_hours"],
            "readable": f"{int(data['timeline_hours'])}-{int(data['timeline_hours'] + 8)} hours"
        },
        "confidence": data["confidence_score"],
        "materials": data["materials"],
        "disclaimer": "This is a demo estimate for demonstration purposes only. Actual costs may vary based on location, materials, and site conditions. For accurate quotes, consult with local contractors.",
        "created_at": datetime.now(timezone.utc).isoformat()
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
