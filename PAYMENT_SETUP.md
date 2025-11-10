# Payment Integration Setup Guide

## Overview

EstimateGenie uses Stripe for secure payment processing. This guide walks through the complete setup.

## 🔑 Required Stripe Keys

### 1. **Stripe Secret Key** (Server-side only)

- **Purpose**: Create customers, sessions, process webhooks
- **Format**: `sk_test_...` (test) or `sk_live_...` (live)
- **Location**: Backend environment variable `STRIPE_SECRET_KEY`
- **Security**: ⚠️ NEVER expose in frontend code

### 2. **Stripe Publishable Key** (Client-side safe)

- **Purpose**: Initialize Stripe.js in frontend
- **Format**: `pk_test_...` (test) or `pk_live_...` (live)  
- **Location**: `assets/js/api-config.js` → `STRIPE_PUBLISHABLE_KEY`
- **Security**: ✅ Safe to include in public frontend code

### 3. **Stripe Webhook Secret**

- **Purpose**: Verify webhook signatures
- **Format**: `whsec_...`
- **Location**: Backend environment variable `STRIPE_WEBHOOK_SECRET`
- **Security**: ⚠️ Server-side only

## 📋 Setup Steps

### Step 1: Get Your Stripe Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers → API Keys**
3. Copy your:
   - **Publishable key** (pk_test_... or pk_live_...)
   - **Secret key** (sk_test_... or sk_live_...)

### Step 2: Configure Backend (Fly.io)

```bash
# Set Stripe secret key
fly secrets set STRIPE_SECRET_KEY="sk_test_your_actual_key_here" -a quotegenie-api

# Set webhook secret (get this after Step 3)
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret" -a quotegenie-api

# Optional: Set price IDs if different from defaults
fly secrets set STRIPE_PRICE_ID_PRO_MONTHLY="price_your_monthly_id" -a quotegenie-api
fly secrets set STRIPE_PRICE_ID_PRO_ANNUAL="price_your_annual_id" -a quotegenie-api
```

### Step 3: Configure Frontend

Edit `assets/js/api-config.js`:

```javascript
const STRIPE_PUBLISHABLE_KEY = 'pk_test_your_actual_publishable_key_here';
```

Then redeploy frontend:

```powershell
.\scripts\deploy_pages_clean.ps1 -CommitDirty
```

### Step 4: Create Stripe Products & Prices

1. In Stripe Dashboard → **Products**
2. Create product: "EstimateGenie Pro - Monthly"
   - Price: $49.00/month recurring
   - Copy the **Price ID** (starts with `price_...`)
3. Create product: "EstimateGenie Pro - Annual"
   - Price: $468.00/year recurring
   - Copy the **Price ID**
4. Update backend secrets with these Price IDs (see Step 2)

### Step 5: Configure Webhook Endpoint

1. In Stripe Dashboard → **Developers → Webhooks**
2. Click **Add endpoint**
3. **Endpoint URL**: `https://quotegenie-api.fly.dev/api/v1/webhooks/stripe`
4. **Events to send**:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (whsec_...)
6. Add to Fly.io secrets (see Step 2)

## 🧪 Testing

### Test Mode

- Use test keys (`sk_test_...` and `pk_test_...`)
- Use Stripe test cards: <https://stripe.com/docs/testing>
  - Success: `4242 4242 4242 4242`
  - Decline: `4000 0000 0000 0002`

### Test Signup Flow

1. Navigate to `https://estimategenie.net/signup.html`
2. Select "Pro Plan"
3. Fill in registration details
4. Should redirect to Stripe Checkout
5. Use test card: `4242 4242 4242 4242` (any future expiry, any CVC)
6. Complete payment
7. Should redirect to dashboard with Pro plan active

### Verify Webhook

```bash
# Check webhook endpoint is accessible
curl https://quotegenie-api.fly.dev/api/v1/webhooks/stripe

# Should return:
# {"status":"ready","method":"POST","instructions":"Configure this URL..."}
```

### Test Webhook Locally (Stripe CLI)

```bash
stripe listen --forward-to https://quotegenie-api.fly.dev/api/v1/webhooks/stripe
stripe trigger checkout.session.completed
```

## 🔍 Troubleshooting

### Issue: "Stripe is not configured"

**Cause**: Missing or invalid Stripe keys
**Fix**:

1. Verify keys are set: `fly secrets list -a quotegenie-api | grep STRIPE`
2. Check `payment_service.py` → `is_configured()` returns `True`
3. Restart app: `fly apps restart quotegenie-api`

### Issue: Checkout redirect fails

**Cause**: Wrong publishable key in frontend
**Fix**: Update `STRIPE_PUBLISHABLE_KEY` in `api-config.js` and redeploy

### Issue: Webhooks not working

**Cause**: Wrong webhook secret or endpoint URL
**Fix**:

1. Verify endpoint: `curl https://quotegenie-api.fly.dev/api/v1/webhooks/stripe`
2. Check Stripe Dashboard → Webhooks → Recent deliveries for errors
3. Ensure `STRIPE_WEBHOOK_SECRET` matches webhook signing secret

### Issue: Subscription not activating

**Cause**: Webhook event not processed
**Fix**:

1. Check Stripe Dashboard → Webhooks → Recent deliveries
2. Check Fly.io logs: `fly logs -a quotegenie-api`
3. Verify `checkout.session.completed` event is configured

## 🚀 Production Deployment

### Switch to Live Mode

1. Get live keys from Stripe Dashboard (toggle "Test mode" off)
2. Update backend secrets with `sk_live_...` key
3. Update frontend with `pk_live_...` key
4. Update webhook endpoint with live webhook secret
5. **IMPORTANT**: Test thoroughly before going live!

### Success URL & Cancel URL

Update in `backend/app.py` → `create_checkout_session`:

```python
success_url="https://estimategenie.net/dashboard.html?payment=success",
cancel_url="https://estimategenie.net/pricing.html?payment=canceled",
```

## 📊 Monitoring

### Stripe Dashboard

- Monitor subscriptions: **Customers → Subscriptions**
- Check failed payments: **Payments → Failed**
- View webhook logs: **Developers → Webhooks → Recent deliveries**

### Application Logs

```bash
# View Fly.io logs
fly logs -a quotegenie-api

# Filter for payment events
fly logs -a quotegenie-api | grep -i "stripe\|payment\|checkout"
```

## 🔐 Security Best Practices

1. ✅ **Never commit secret keys to git**
2. ✅ **Use environment variables for all secrets**
3. ✅ **Verify webhook signatures** (already implemented in `payment_service.py`)
4. ✅ **Use HTTPS only** (enforced by Stripe and Fly.io)
5. ✅ **Validate webhook events server-side** (implemented)
6. ✅ **Keep Stripe.js up to date** (using CDN version)

## 📞 Support

- Stripe Docs: <https://stripe.com/docs>
- Stripe Support: <https://support.stripe.com/>
- EstimateGenie Issues: Check application logs on Fly.io
