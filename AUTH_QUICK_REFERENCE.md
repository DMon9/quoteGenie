# Authentication & Payment System - Quick Reference

## 🚀 Quick Start

### Local Development
```bash
cd backend
.\start.ps1
```

This will:
1. Create `.env` from template
2. Set up Python virtual environment
3. Install dependencies
4. Prepare database

### Test the API
```bash
.\test-api.ps1
```

Runs complete test suite including:
- Registration, login, profile management
- API key generation
- Usage tracking
- Quote generation (if configured)

## 📋 Environment Variables

Required in `.env` or Fly.io secrets:

```bash
# Authentication
JWT_SECRET_KEY=your-secret-key-here

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO_MONTHLY=price_...
STRIPE_PRICE_ID_PRO_ANNUAL=price_...

# LLM (existing)
GOOGLE_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-flash
LLM_PROVIDER=google

# CORS
ALLOW_ORIGINS=https://estimategenie.net,...
```

## 🔐 Authentication Flow

### 1. Register
```bash
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!",
  "plan": "free"  # or "pro"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "email": "...", "plan": "free" }
}
```

### 2. Login
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** Same as registration

### 3. Access Protected Endpoints
```bash
# Using JWT token
GET /api/v1/auth/me
Authorization: Bearer eyJ...

# Or using API key
POST /v1/quotes
Authorization: gqg_1234567890abcdef
```

## 💰 Payment Integration

### Subscribe to Pro Plan

**Option 1: During Registration**
```bash
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123!",
  "plan": "pro"  # Triggers Stripe Checkout
}
```

**Response includes:**
```json
{
  "checkout_session_id": "cs_...",
  "checkout_url": "https://checkout.stripe.com/..."
}
```

Redirect user to `checkout_url` to complete payment.

**Option 2: Upgrade Existing Account**
Visit dashboard settings → "Upgrade Plan" → Stripe Checkout

### Access Billing Portal
```bash
POST /api/v1/payment/create-portal-session
Authorization: Bearer eyJ...
```

**Response:**
```json
{
  "url": "https://billing.stripe.com/..."
}
```

Redirect user to manage subscription, update payment method, view invoices.

## 📊 Usage Limits

### Free Plan (Starter)
- **5 quotes/month**
- **1,000 API calls/day**
- Resets monthly/daily

### Pro Plan ($49/month)
- **Unlimited quotes**
- **100,000 API calls/day**
- No monthly reset

### Checking Limits
```bash
GET /api/v1/auth/usage
Authorization: Bearer eyJ...
```

**Response:**
```json
{
  "quotes_used": 3,
  "api_calls_used": 150,
  "limits": {
    "quotes_per_month": 5,
    "api_calls_per_day": 1000
  },
  "can_generate_quote": true,
  "can_use_api": true
}
```

### When Limit Exceeded
```bash
POST /v1/quotes (6th time for free user)
```

**Response:** `403 Forbidden`
```json
{
  "detail": "Quote limit reached. Your free plan allows 5 quotes per month. Upgrade your plan to continue."
}
```

## 🔑 API Keys

### Get Current API Key
```bash
GET /api/v1/auth/me
Authorization: Bearer eyJ...
```

Returns user object including `api_key`.

### Regenerate API Key
```bash
POST /api/v1/auth/regenerate-key
Authorization: Bearer eyJ...
```

**Response:**
```json
{
  "api_key": "gqg_newapikey123456789"
}
```

⚠️ Old key immediately stops working.

### Using API Key for Quotes
```bash
POST /v1/quotes
Authorization: gqg_your_api_key_here
Content-Type: multipart/form-data

file=@image.jpg
project_type=bathroom
description=Renovation project
```

## 🎯 User Management

### Update Profile
```bash
PUT /api/v1/auth/update-profile
Authorization: Bearer eyJ...
{
  "name": "New Name"
}
```

### Change Password
```bash
PUT /api/v1/auth/change-password
Authorization: Bearer eyJ...
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

### Delete Account
```bash
DELETE /api/v1/auth/delete-account
Authorization: Bearer eyJ...
```

⚠️ Irreversible! Cancels Stripe subscription automatically.

## 🪝 Stripe Webhooks

### Events Handled

**1. `checkout.session.completed`**
- User completes payment
- Updates user to Pro plan
- Sets subscription_status to "active"

**2. `customer.subscription.updated`**
- Subscription changes (upgrade/downgrade)
- Updates user subscription status

**3. `customer.subscription.deleted`**
- Subscription cancelled
- Downgrades user to free plan

**4. `invoice.payment_failed`**
- Payment failed (expired card, etc.)
- Sets subscription_status to "past_due"

### Webhook Endpoint
```
POST /api/v1/webhooks/stripe
Stripe-Signature: t=123,v1=abc...
```

Always verifies signature before processing.

## 🧪 Testing

### Test User Registration
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","name":"Test","password":"Test123!","plan":"free"}'
```

### Test Stripe Checkout
Use test card in Stripe Checkout:
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

### Test Webhook Locally
Use Stripe CLI:
```bash
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

Trigger test event:
```bash
stripe trigger checkout.session.completed
```

## 📖 Frontend Integration

### Login Form
```javascript
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  window.location.href = '/dashboard.html';
}
```

### Protected API Call
```javascript
async function getProfile() {
  const token = localStorage.getItem('token');
  
  const response = await fetch('/api/v1/auth/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  return await response.json();
}
```

### Generate Quote
```javascript
async function generateQuote(file) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_type', 'bathroom');
  
  const response = await fetch('/v1/quotes', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  if (response.status === 403) {
    alert('Quote limit reached. Please upgrade your plan.');
    return;
  }
  
  return await response.json();
}
```

### Upgrade to Pro
```javascript
async function upgradeToPro() {
  // Register with pro plan
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: userEmail,
      name: userName,
      password: userPassword,
      plan: 'pro'
    })
  });
  
  const data = await response.json();
  // Redirect to Stripe Checkout
  window.location.href = data.checkout_url;
}
```

## 🐛 Troubleshooting

### "Invalid or expired token"
- Token expires after 7 days
- User needs to login again
- Check `localStorage.getItem('token')`

### "Authentication required"
- Check Authorization header is present
- Verify format: `Bearer <token>` or just `<api_key>`
- Token may be malformed

### Stripe webhook not working
- Verify webhook secret matches
- Check endpoint is publicly accessible
- Review Stripe Dashboard webhook logs
- Check application logs: `fly logs`

### Quote limit not resetting
- Currently manual reset required
- Use database query to reset:
  ```sql
  UPDATE users SET quotes_used = 0 WHERE plan = 'free';
  ```

### User can't access dashboard
- Verify token in localStorage
- Check `/api/v1/auth/me` returns user data
- Clear browser cache and re-login

## 📚 Additional Resources

- **Full Setup Guide:** AUTHENTICATION_SETUP.md
- **Deployment Guide:** DEPLOYMENT_GUIDE.md
- **System Summary:** AUTH_SYSTEM_SUMMARY.md
- **API Documentation:** https://estimategenie.net/docs.html
- **Stripe Docs:** https://stripe.com/docs/billing

## 🔄 Database Schema

```sql
-- Users table (auto-created on first run)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    api_key TEXT UNIQUE,
    stripe_customer_id TEXT,
    subscription_status TEXT,
    subscription_id TEXT,
    quotes_used INTEGER DEFAULT 0,
    api_calls_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎉 Success!

Your authentication and payment system is ready! 

**Next steps:**
1. Configure environment variables
2. Set up Stripe products
3. Deploy to production
4. Test complete user flow
5. Switch to Stripe live mode

Need help? Check DEPLOYMENT_GUIDE.md for detailed instructions.
