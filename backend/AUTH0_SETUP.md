# Auth0 Integration Setup Guide

## Overview

EstimateGenie now supports Auth0 authentication alongside local authentication. Users can choose between:

- **Auth0 Login**: Secure, enterprise-grade authentication with social logins
- **Local Authentication**: Traditional email/password stored in local database

## Setup Instructions

### 1. Create Auth0 Account

1. Go to [auth0.com](https://auth0.com) and sign up for a free account
2. Create a new tenant (e.g., `estimategenie.us.auth0.com`)

### 2. Create Auth0 Application

1. In Auth0 Dashboard, go to **Applications** → **Create Application**
2. Choose **Regular Web Application**
3. Name it "EstimateGenie"
4. Go to the **Settings** tab and note:
   - **Domain** (e.g., `estimategenie.us.auth0.com`)
   - **Client ID**
   - **Client Secret**

### 3. Configure Application Settings

In the Auth0 Application Settings:

**Allowed Callback URLs:**

```
http://localhost:8080/callback
https://quotegenie-api.fly.dev/callback
https://your-production-domain.com/callback
```

**Allowed Logout URLs:**

```
http://localhost:8080
https://quotegenie-api.fly.dev
https://your-production-domain.com
```

**Allowed Web Origins:**

```
http://localhost:8080
https://quotegenie-api.fly.dev
https://your-production-domain.com
```

### 4. Enable APIs

1. Go to **Applications** → **APIs**
2. Note the **Auth0 Management API** audience URL (usually `https://YOUR_DOMAIN.auth0.com/api/v2/`)

### 5. Configure Environment Variables

#### Local Development (.env file)

```bash
# Auth0 Configuration
AUTH0_DOMAIN=estimategenie.us.auth0.com
AUTH0_CLIENT_ID=your_client_id_here
AUTH0_CLIENT_SECRET=your_client_secret_here
AUTH0_AUDIENCE=https://estimategenie.us.auth0.com/api/v2/
```

#### Fly.io Deployment

```bash
# Set secrets
fly secrets set AUTH0_DOMAIN=estimategenie.us.auth0.com
fly secrets set AUTH0_CLIENT_ID=your_client_id_here
fly secrets set AUTH0_CLIENT_SECRET=your_client_secret_here
fly secrets set AUTH0_AUDIENCE=https://estimategenie.us.auth0.com/api/v2/

# Deploy
fly deploy
```

### 6. Update Frontend

The frontend has been updated to detect Auth0 availability. Users will see:

- "Sign in with Auth0" button if Auth0 is configured
- Traditional login form as fallback

**Login URLs:**

- Auth0 Login: `http://localhost:8080/login` or `https://quotegenie-api.fly.dev/login`
- Callback: `http://localhost:8080/callback` or `https://quotegenie-api.fly.dev/callback`

## Testing

### 1. Check Auth0 Status

```bash
curl http://localhost:8080/health
```

Response should include:

```json
{
  "status": "healthy",
  "services": {
    "auth0": true
  }
}
```

### 2. Test Login Flow

1. Navigate to `http://localhost:8080/login`
2. Click "Sign in with Auth0"
3. Complete Auth0 login (create account if needed)
4. You'll be redirected to `/callback`
5. Tokens will be stored in localStorage
6. You'll be redirected to the main app

### 3. Verify Authentication

```javascript
// In browser console
console.log(localStorage.getItem('auth_token'));
console.log(localStorage.getItem('api_key'));
```

## API Endpoints

### Auth0 Endpoints

**Get Login URL:**

```
GET /api/v1/auth/auth0/login-url?redirect_uri=http://localhost:8080/callback
```

**Handle Callback:**

```
POST /api/v1/auth/auth0/callback?code=xxx&redirect_uri=http://localhost:8080/callback
```

### Traditional Auth Endpoints (Still Available)

**Register:**

```
POST /api/v1/auth/register
```

**Login:**

```
POST /api/v1/auth/login
```

**Get User:**

```
GET /api/v1/auth/me
```

## User Data Storage

When users log in via Auth0:

1. User profile is fetched from Auth0
2. User record is created/updated in local database
3. JWT token is generated for API access
4. API key is provided for programmatic access

Both Auth0 and local users are stored in the same database with compatible schemas.

## Social Login (Optional)

To enable Google, Facebook, etc.:

1. In Auth0 Dashboard, go to **Authentication** → **Social**
2. Enable desired providers (Google, Facebook, GitHub, etc.)
3. Configure OAuth credentials for each provider
4. No code changes needed!

## Troubleshooting

**Error: Auth0 is not configured**

- Check that all AUTH0_* environment variables are set
- Restart the application after setting variables

**Error: Invalid state parameter**

- Clear browser cache and cookies
- Try logging in again

**Error: Failed to exchange code for token**

- Verify redirect_uri matches exactly in Auth0 settings
- Check that Client Secret is correct

**Users still showing as "Guest"**

- Clear localStorage and log in again
- Check browser console for errors
- Verify auth_token is being saved

## Migration Path

Existing users with local accounts can:

1. Continue using local authentication
2. Optionally link their Auth0 account to their existing account (manual process)

## Security Notes

- Auth0 tokens are verified using RS256 algorithm
- JWKS keys are fetched from Auth0 automatically
- Tokens are short-lived and must be refreshed
- User passwords for local auth are bcrypt hashed
- Auth0 users have "auth0" as password_hash (they don't use local passwords)

## Production Checklist

- [ ] Configure production Auth0 application
- [ ] Set all AUTH0_* secrets in Fly.io
- [ ] Update allowed callback URLs to production domain
- [ ] Enable rate limiting on auth endpoints
- [ ] Set up Auth0 monitoring and alerts
- [ ] Configure Auth0 branding (logo, colors)
- [ ] Enable MFA (Multi-Factor Authentication) in Auth0
- [ ] Review Auth0 security settings

## Support

If you encounter issues:

1. Check logs: `fly logs`
2. Verify Auth0 configuration
3. Test locally first before deploying
4. Check Auth0 Dashboard logs for authentication attempts
