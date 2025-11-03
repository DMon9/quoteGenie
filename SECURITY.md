# API Key Security Guide

## ⚠️ IMPORTANT: API Keys Removed from Repository

All sensitive API keys, tokens, and secrets have been removed from the codebase to prevent unauthorized access.

## Affected Keys (Now Secured)

The following keys were removed from public code:

1. **Google API Key** (Gemini AI)
   - Previously exposed in: `.env`, deployment docs
   - **Action Required**: Regenerate in Google Cloud Console
   - Get new key: https://makersuite.google.com/app/apikey

2. **Stripe API Keys**
   - Secret Key, Webhook Secret, Price IDs
   - **Action Required**: Rotate keys in Stripe Dashboard
   - Dashboard: https://dashboard.stripe.com/apikeys

3. **HuggingFace Token**
   - Previously in `.env`
   - **Action Required**: Regenerate if needed
   - Settings: https://huggingface.co/settings/tokens

4. **JWT Secret Key**
   - Used for authentication tokens
   - **Action Required**: Generate new secret

## How to Configure API Keys Securely

### Local Development

1. Copy the template:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` with your actual keys (this file is git-ignored)

3. **NEVER commit `.env` to git**

### Production (Fly.io)

Set secrets using Fly CLI (keys are encrypted):

```powershell
# Google Gemini API
fly secrets set GOOGLE_API_KEY=<your-new-key> -a quotegenie-api

# Stripe
fly secrets set STRIPE_SECRET_KEY=<your-stripe-key> -a quotegenie-api
fly secrets set STRIPE_WEBHOOK_SECRET=<your-webhook-secret> -a quotegenie-api
fly secrets set STRIPE_PRICE_ID_PRO_MONTHLY=<your-price-id> -a quotegenie-api

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
fly secrets set JWT_SECRET_KEY=<your-jwt-secret> -a quotegenie-api
```

### Verify Secrets Are Set

```powershell
fly secrets list -a quotegenie-api
```

## Security Best Practices

✅ **DO:**
- Use environment variables for all secrets
- Rotate API keys immediately after exposure
- Use `.env.example` as template (no real values)
- Set secrets via Fly CLI for production
- Enable API key restrictions in Google Cloud Console
- Use Stripe test keys for development

❌ **DON'T:**
- Commit `.env` files to git
- Hardcode API keys in source code
- Share API keys in documentation
- Use production keys in development
- Expose keys in public endpoints (e.g., `/debug/env` removed)

## Immediate Actions Taken

1. ✅ Removed `/debug/env` endpoint that exposed API key info
2. ✅ Sanitized `.env` file (replaced real keys with placeholders)
3. ✅ Updated all documentation to use `<your-key>` placeholders
4. ✅ Verified `.env` is in `.gitignore`

## Next Steps

1. **Regenerate all exposed keys** (Google, Stripe, HuggingFace)
2. **Update production secrets** on Fly.io with new keys
3. **Test API functionality** after key rotation
4. **Enable IP restrictions** on Google API key (optional)
5. **Monitor usage** for unauthorized access

## API Key Restrictions (Recommended)

### Google API Key Restrictions

In Google Cloud Console:
1. Go to API & Services → Credentials
2. Edit your API key
3. Set "Application restrictions" → HTTP referrers
4. Add: `https://api.estimategenie.net/*`
5. Set "API restrictions" → Restrict key → Select only "Generative Language API"

### Stripe Webhook Security

1. Configure webhook URL: `https://api.estimategenie.net/api/v1/webhooks/stripe`
2. Select events: `checkout.session.completed`, `customer.subscription.*`
3. Copy webhook signing secret to STRIPE_WEBHOOK_SECRET

## Questions?

If you need help rotating keys or have security concerns, refer to:
- Google Cloud: https://cloud.google.com/docs/authentication/api-keys
- Stripe: https://stripe.com/docs/keys
- Fly.io Secrets: https://fly.io/docs/reference/secrets/
