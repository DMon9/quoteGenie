# Deployment Guide - EstimateGenie Authentication & Payments

## Overview

Complete deployment checklist for EstimateGenie with JWT authentication and Stripe payments.

## Pre-Deployment Setup

### 1. Generate JWT Secret Key

```bash
openssl rand -hex 32
```

Save this value - you'll need it for environment variables.

### 2. Configure Stripe

#### Create Products in Stripe Dashboard

1. Go to: <https://dashboard.stripe.com/products>
2. Click "Add Product"
3. Product details:
   - Name: EstimateGenie Professional
   - Description: Unlimited quotes and API access
4. Add pricing:
   - **Monthly:** $49/month (recurring)
   - **Annual:** $468/year (recurring)
5. Copy both Price IDs (starts with `price_...`)

#### Set Up Webhook Endpoint

1. Go to: <https://dashboard.stripe.com/webhooks>
2. Click "Add endpoint"
3. Endpoint URL: `https://api.estimategenie.net/api/v1/webhooks/stripe`
4. Description: EstimateGenie subscription events
5. Events to send:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.payment_failed`
6. Click "Add endpoint"
7. Copy the "Signing secret" (starts with `whsec_...`)

### 3. Set Fly.io Environment Variables

```bash
# Navigate to backend directory
cd backend

# Set all secrets
fly secrets set JWT_SECRET_KEY=56ddd4c36b4a99cc6f4352a2e8d51f035b0a358005ae8f4de7010a1e336e5777
fly secrets set STRIPE_SECRET_KEY=sk_test_your_stripe_key
fly secrets set STRIPE_WEBHOOK_SECRET=whsec_5QeFbR28kakRecPOwobpgIuKbpgGq6GB
fly secrets set STRIPE_PRICE_ID_PRO_MONTHLY=price_1SOE2YENa3zBKoIjGn0yD5mN
fly secrets set STRIPE_PRICE_ID_PRO_ANNUAL=price_1SOE2YENa3zBKoIjVmHFP2GX
fly secrets set GOOGLE_API_KEY=AIzaSyBan9TR_G6naHIEWmu_ABvEMR0JNBRFMi4
fly secrets set GEMINI_MODEL=gemini-1.5-flash
fly secrets set LLM_PROVIDER=google
fly secrets set ALLOW_ORIGINS=https://estimategenie.net,https://f00e471b.estimategenie.pages.dev
```

## Deployment Steps

### 1. Deploy Backend to Fly.io

```bash
cd backend
fly deploy
```

Verify deployment:

```bash
curl https://api.estimategenie.net/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "services": {
    "vision": true,
    "llm": true,
    "database": true
  }
}
```

### 2. Deploy Frontend to Cloudflare Pages

```powershell
# Create deployment directory
New-Item -ItemType Directory -Force -Path frontend-deploy

# Copy updated HTML files (renamed)
Copy-Item docs-fixed.html frontend-deploy/docs.html
Copy-Item dashboard-new.html frontend-deploy/dashboard.html
Copy-Item pricing.html frontend-deploy/
Copy-Item login.html frontend-deploy/
Copy-Item signup.html frontend-deploy/

# Copy other pages
Copy-Item index.html, about.html, blog.html, case-studies.html, contact.html, features.html frontend-deploy/

# Copy static files
Copy-Item robots.txt, sitemaps.xml frontend-deploy/
Copy-Item -Recurse assets frontend-deploy/
```

Deploy:

```bash
cd frontend-deploy
npx wrangler pages deploy . --project-name=estimategenie
```

Your site will be available at:

- Custom domain: <https://estimategenie.net>
- Cloudflare domain: <https://f00e471b.estimategenie.pages.dev>

## Post-Deployment Testing

### Test 1: User Registration (Free Plan)

Using curl:

```bash
curl -X POST https://api.estimategenie.net/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "TestPassword123!",
    "plan": "free"
  }'
```

Or visit: <https://estimategenie.net/signup.html>

### Test 2: User Login

```bash
curl -X POST https://api.estimategenie.net/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

Save the `access_token` from the response.

### Test 3: Get User Profile

```bash
curl https://api.estimategenie.net/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

### Test 4: Generate Quote (Authenticated)

```bash
curl -X POST https://api.estimategenie.net/v1/quotes \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -F "file=@test-image.jpg" \
  -F "project_type=bathroom" \
  -F "description=Bathroom renovation"
```

### Test 5: Pro Plan Registration with Stripe

1. Go to: <https://estimategenie.net/signup.html>
2. Fill in registration form
3. Select "Professional" plan ($49/month)
4. Click "Get Started"
5. Should redirect to Stripe Checkout
6. Use test card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
7. Complete payment
8. Should redirect to dashboard
9. Verify plan shows "Professional"

### Test 6: Webhook Processing

Check Stripe Dashboard:

1. Go to: <https://dashboard.stripe.com/webhooks>
2. Click on your endpoint
3. View "Recent deliveries"
4. Should see `checkout.session.completed` event
5. Status should be 200 (Success)

### Test 7: Dashboard Features

Visit: <https://estimategenie.net/dashboard.html>

Test each tab:

**Overview:**

- [ ] User stats load correctly
- [ ] Chart displays usage data
- [ ] Plan information shows

**API Keys:**

- [ ] API key displays (hidden by default)
- [ ] Show/Hide toggle works
- [ ] Copy to clipboard works
- [ ] Regenerate creates new key

**Settings:**

- [ ] Update profile name
- [ ] Change password works
- [ ] "Manage Billing" opens Stripe portal
- [ ] Account deletion (careful!)

### Test 8: Usage Limits

**Free Plan Limit (5 quotes/month):**

```bash
# Generate 5 quotes
for i in {1..5}; do
  curl -X POST https://api.estimategenie.net/v1/quotes \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -F "file=@test.jpg" \
    -F "project_type=general"
done

# 6th quote should fail with 403
curl -X POST https://api.estimategenie.net/v1/quotes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.jpg" \
  -F "project_type=general"
```

Expected response:

```json
{
  "detail": "Quote limit reached. Your free plan allows 5 quotes per month. Upgrade your plan to continue."
}
```

**Pro Plan (Unlimited):**

- Should never hit quote limit
- Test by generating 10+ quotes

## Monitoring

### Check Application Logs

```bash
fly logs --app quotegenie-api
```

### Monitor Stripe Events

Dashboard: <https://dashboard.stripe.com/events>

Watch for:

- Failed payments
- Subscription updates
- Webhook failures

### Health Check

```bash
# Automated monitoring
curl https://api.estimategenie.net/health
```

Set up monitoring service (e.g., UptimeRobot) to ping every 5 minutes.

## Troubleshooting

### Issue: "Authentication required" error on quote generation

**Solution:**

1. Check Authorization header is present
2. Verify token format: `Bearer <token>`
3. Token may be expired (7-day lifetime)
4. Re-login to get new token

### Issue: Stripe webhook returns 400 error

**Solution:**

1. Verify `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
2. Check webhook endpoint URL is correct
3. Review Stripe Dashboard webhook logs
4. Check Fly.io logs: `fly logs`

### Issue: User can't access dashboard after payment

**Solution:**

1. Check Stripe webhook was received and processed
2. Query user in database to verify subscription_status
3. Verify checkout.session.completed event contains user_id in metadata
4. Check application logs for webhook processing errors

### Issue: Quote generation fails after authentication

**Solution:**

1. Verify LLM service is configured (GOOGLE_API_KEY)
2. Check vision service health endpoint
3. Review Fly.io logs for specific errors
4. Test with simpler image first

## Security Checklist

- [x] JWT_SECRET_KEY is random and secure (32+ bytes)
- [x] Stripe webhook signature verification enabled
- [x] HTTPS enforced on all endpoints
- [x] Passwords hashed before storage
- [x] API keys are unpredictable (token_urlsafe)
- [x] CORS configured to allow only known origins
- [ ] Rate limiting (future enhancement)
- [ ] Email verification (future enhancement)

## Maintenance Tasks

### Daily

- Monitor Fly.io application health
- Check Stripe dashboard for failed payments

### Weekly

- Review application logs for errors
- Check webhook delivery success rate
- Monitor user registration trends

### Monthly

- Review usage statistics
- Check database size
- Backup database

### Database Backup

```bash
fly ssh console --app quotegenie-api
cd /app
sqlite3 estimategenie.db ".backup backup-$(date +%Y%m%d).db"
```

## Support & Documentation

- **Authentication docs:** See AUTHENTICATION_SETUP.md
- **API docs:** <https://estimategenie.net/docs.html>
- **Stripe docs:** <https://stripe.com/docs/billing>
- **Fly.io docs:** <https://fly.io/docs/>

## Next Steps

After successful deployment:

1. **Switch to production Stripe keys:**

   ```bash
   fly secrets set STRIPE_SECRET_KEY=sk_live_your_key
   fly secrets set STRIPE_PRICE_ID_PRO_MONTHLY=price_live_monthly
   fly secrets set STRIPE_PRICE_ID_PRO_ANNUAL=price_live_annual
   ```

2. **Update webhook endpoint in Stripe:**
   - Use production mode in Stripe Dashboard
   - Create new webhook with same events
   - Update STRIPE_WEBHOOK_SECRET

3. **Test with real payment:**
   - Use real credit card (will charge $49)
   - Verify subscription activates
   - Check billing portal access

4. **Marketing:**
   - Update pricing page with launch offer
   - Announce on social media
   - Email existing users about new features

## Rollback Plan

If issues occur after deployment:

```bash
# View previous deployments
fly releases --app quotegenie-api

# Rollback to previous version
fly releases rollback <version> --app quotegenie-api
```

For frontend (Cloudflare Pages):

- Go to Cloudflare Dashboard → Pages → estimategenie
- View deployments
- Click "Rollback" on previous working deployment
