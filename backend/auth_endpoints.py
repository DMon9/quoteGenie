"""
Authentication and payment endpoints for app.py
Add these endpoints to your main app.py file
"""

from fastapi import Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
from services.auth_service import AuthService
from services.payment_service import PaymentService

# Initialize auth service
auth_service = AuthService()
payment_service = PaymentService()

# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    plan: str = "free"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Authentication dependency
async def get_current_user(authorization: str = Header(None)):
    """Dependency to get current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = auth_service.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def get_user_from_api_key(x_api_key: str = Header(None)):
    """Dependency to get user from API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    user = auth_service.get_user_by_api_key(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user

# Add these endpoints to your FastAPI app

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
    
    # For pro plan, create Stripe checkout session
    if request.plan == "pro":
        customer_id = payment_service.create_customer(user.email, user.name)
        if customer_id:
            checkout = payment_service.create_checkout_session(
                customer_id=customer_id,
                plan="pro",
                success_url=f"https://estimategenie.net/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url="https://estimategenie.net/pricing",
                user_id=user.id
            )
            
            if checkout:
                return {
                    "user": user.to_dict(),
                    "checkout_session_id": checkout["session_id"],
                    "checkout_url": checkout["url"]
                }
    
    # For free plan, return token immediately
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Login with email and password"""
    user = auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = auth_service.create_access_token(user.id, user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict(include_sensitive=True)

@app.get("/api/v1/auth/usage")
async def get_usage_stats(current_user = Depends(get_current_user)):
    """Get current user's usage statistics"""
    limits = current_user.get_plan_limits()
    
    return {
        "user_id": current_user.id,
        "plan": current_user.plan,
        "quotes_used": current_user.quotes_used,
        "api_calls_used": current_user.api_calls_used,
        "limits": limits,
        "can_generate_quote": current_user.can_generate_quote(),
        "can_use_api": current_user.can_use_api()
    }

@app.post("/api/v1/payment/create-portal-session")
async def create_portal_session(current_user = Depends(get_current_user)):
    """Create Stripe billing portal session"""
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No subscription found")
    
    portal_url = payment_service.create_portal_session(
        customer_id=current_user.stripe_customer_id,
        return_url="https://estimategenie.net/dashboard"
    )
    
    if not portal_url:
        raise HTTPException(status_code=500, detail="Failed to create portal session")
    
    return {"url": portal_url}

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    event = payment_service.verify_webhook_signature(payload, sig_header)
    
    if not event:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    success = payment_service.handle_webhook_event(event, auth_service)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process webhook")
    
    return {"status": "success"}

# Update the create_quote endpoint to include authentication
@app.post("/api/v1/quotes", response_model=QuoteResponse)
async def create_quote_authenticated(
    file: UploadFile = File(...),
    project_type: str = "general",
    description: str = "",
    current_user = Depends(get_current_user)
):
    """
    Create a quote (authenticated version)
    Checks user limits and increments usage
    """
    # Check if user can generate quotes
    if not current_user.can_generate_quote():
        raise HTTPException(
            status_code=429,
            detail="Quote limit reached. Please upgrade your plan."
        )
    
    # Generate quote (existing logic)
    # ... your existing quote generation code ...
    
    # Increment usage
    current_user.increment_quote_usage()
    auth_service.update_user_usage(
        user_id=current_user.id,
        quotes_used=current_user.quotes_used
    )
    
    # Return quote response
    return quote_response
