# EstimateGenie - Authentication & Payment Integration

## Overview
This update adds complete user authentication, account management, pricing tiers, and Stripe payment integration to EstimateGenie.

## New Features

### 1. Fixed Documentation Page
- **File**: `docs-fixed.html`
- Complete API documentation with proper structure
- Interactive code examples
- Error handling guide
- Best practices section

### 2. Pricing Page
- **File**: `pricing.html`
- Three tiers: Starter (Free), Professional ($49/mo), Enterprise (Custom)
- Monthly/Annual billing toggle with savings calculator
- Feature comparison table
- FAQ section
- Direct signup integration

### 3. Authentication System

#### Frontend Pages
- **login.html**: User login with email/password
- **signup.html**: Registration with plan selection and Stripe integration
- Social login placeholders (Google, GitHub)

#### Backend Components
- **models/user.py**: User model with plan management and API key generation
- **services/auth_service.py**: JWT token authentication, user CRUD operations
- **services/payment_service.py**: Stripe subscription management
- **auth_endpoints.py**: FastAPI endpoints for auth and payments

### 4. User Account Features
- JWT-based authentication (7-day expiration)
- Secure API key generation per user
- Usage tracking (quotes and API calls)
- Plan-based limits enforcement
- Subscription status management

### 5. Payment Integration
- Stripe Checkout for Pro plan subscriptions
- Stripe Customer Portal for subscription management
- Webhook handling for payment events
- Automatic plan upgrades/downgrades

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables
Add to your `.env` file or Fly.io secrets:

```bash
# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRO_PRICE_ID=price_your_pro_monthly_price_id
STRIPE_PRO_ANNUAL_PRICE_ID=price_your_pro_annual_price_id
```

### 3. Set Fly.io Secrets
```bash
fly secrets set JWT_SECRET_KEY="your-secret-key"
fly secrets set STRIPE_SECRET_KEY="sk_live_your_key"
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_your_secret"
fly secrets set STRIPE_PRO_PRICE_ID="price_live_pro_monthly"
fly secrets set STRIPE_PRO_ANNUAL_PRICE_ID="price_live_pro_annual"
```

### 4. Stripe Setup

#### Create Products and Prices
1. Go to Stripe Dashboard → Products
2. Create "EstimateGenie Professional" product
3. Add two prices:
   - Monthly: $49/month
   - Annual: $468/year ($39/month)
4. Copy the Price IDs and add to environment variables

#### Configure Webhooks
1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://api.estimategenie.net/api/v1/webhooks/stripe`
3. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copy the webhook secret and add to environment variables

### 5. Update app.py
Add the authentication endpoints from `auth_endpoints.py` to your main `app.py`:

```python
from fastapi import Depends
from services.auth_service import AuthService
from services.payment_service import PaymentService

# Initialize services
auth_service = AuthService()
payment_service = PaymentService()

# Copy all the endpoints from auth_endpoints.py
```

### 6. Deploy Frontend
Copy the new HTML files to your frontend deployment:

```bash
# Copy to Cloudflare Pages directory
cp docs-fixed.html frontend-deploy/docs.html
cp pricing.html frontend-deploy/
cp login.html frontend-deploy/
cp signup.html frontend-deploy/

# Deploy to Cloudflare Pages
npx wrangler pages deploy frontend-deploy --project-name=estimategenie
```

### 7. Deploy Backend
```bash
fly deploy
```

## API Endpoints

### Authentication

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123",
  "plan": "free"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "plan": "free",
    "api_key": "eg_sk_...",
    "limits": {...}
  }
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Get Usage Stats
```http
GET /api/v1/auth/usage
Authorization: Bearer YOUR_JWT_TOKEN
```

### Payments

#### Create Billing Portal Session
```http
POST /api/v1/payment/create-portal-session
Authorization: Bearer YOUR_JWT_TOKEN
```

Response:
```json
{
  "url": "https://billing.stripe.com/session/..."
}
```

### Quotes (Updated)
Now requires authentication:

```http
POST /api/v1/quotes
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: multipart/form-data

file: [image file]
project_type: kitchen
description: Full kitchen remodel
```

## Plan Limits

### Starter (Free)
- 10 quotes per month
- Basic AI analysis
- Email support
- PDF exports
- ❌ No API access

### Professional ($49/mo)
- ✅ Unlimited quotes
- Advanced AI with vision
- API access (10,000 calls/month)
- Priority support
- Custom branding
- Team collaboration (5 users)
- Analytics dashboard

### Enterprise (Custom)
- ✅ Everything unlimited
- Custom AI training
- Dedicated account manager
- 24/7 support
- On-premise deployment
- SLA guarantee
- Advanced compliance

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    api_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stripe_customer_id TEXT,
    subscription_status TEXT DEFAULT 'inactive',
    subscription_id TEXT,
    quotes_used INTEGER DEFAULT 0,
    api_calls_used INTEGER DEFAULT 0
);
```

## Testing

### 1. Test Registration
```bash
curl -X POST https://api.estimategenie.net/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "testpassword123",
    "plan": "free"
  }'
```

### 2. Test Login
```bash
curl -X POST https://api.estimategenie.net/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 3. Test Usage Stats
```bash
curl -X GET https://api.estimategenie.net/api/v1/auth/usage \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Considerations

1. **Password Hashing**: Using SHA256 (consider upgrading to bcrypt for production)
2. **JWT Tokens**: 7-day expiration, stored in localStorage
3. **API Keys**: Securely generated using `secrets.token_urlsafe`
4. **CORS**: Configured for your domains
5. **Stripe Webhooks**: Signature verification for all events

## Next Steps

1. Create dashboard.html for user account management
2. Add password reset functionality
3. Implement email verification
4. Add usage analytics charts
5. Create admin panel for user management
6. Add rate limiting middleware
7. Implement refresh tokens
8. Add OAuth providers (Google, GitHub)

## Troubleshooting

### Issue: JWT tokens not working
- Check JWT_SECRET_KEY is set in environment
- Verify token format: `Bearer <token>`
- Check token expiration

### Issue: Stripe checkout not working
- Verify STRIPE_SECRET_KEY is set
- Check Price IDs match your Stripe products
- Ensure webhooks are configured correctly

### Issue: User can't generate quotes
- Check plan limits with `/api/v1/auth/usage`
- Verify subscription status is "active"
- Check quotes_used counter hasn't exceeded limit

## Support

For questions or issues:
- Email: support@estimategenie.net
- Docs: https://estimategenie.net/docs.html
- Dashboard: https://estimategenie.net/dashboard.html

## License

Copyright © 2025 EstimateGenie. All rights reserved.
