# EstimateGenie - Development Quick Start

## The Problem You Just Hit

When you clicked "Sign Up", you got an error because the **backend API server wasn't running**. The signup form tries to send data to `http://localhost:8000/api/v1/auth/register`, but nothing was listening on port 8000.

## Quick Fix (Run This First!)

**Option 1: Automated Startup (Recommended)**

```powershell
.\start-dev.ps1
```

This will start both:

- Backend API on <http://localhost:8000>
- Frontend on <http://localhost:8080>

**Option 2: Manual Startup**

Terminal 1 - Backend API:

```powershell
cd backend
..\.venv-3\Scripts\Activate.ps1
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:

```powershell
python -m http.server 8080
```

## Verify It's Working

1. Backend Health: <http://localhost:8000/health>
2. API Docs: <http://localhost:8000/docs>
3. Frontend: <http://localhost:8080>

## Now Try Signup Again

1. Go to <http://localhost:8080/signup.html>
2. Fill in the form:
   - Name: Test User
   - Email: <test@example.com>
   - Password: password123
   - Plan: Starter (Free)
3. Check "I agree to terms"
4. Click "Create Account"

If the backend is running, you'll either:

- **Success**: Redirect to dashboard
- **Error with details**: See specific error from API (e.g., "Email already registered")
- **Network error**: Backend still not running (check the terminal windows)

## Common Issues

### "Cannot connect to API server"

- Backend isn't running on port 8000
- Run: `.\start-dev.ps1` or manually start the backend

### "Email already registered"

- You already created an account with that email
- Try a different email or check `backend/estimategenie.db`

### "Payments are not configured" (for Pro plan)

- Set Stripe env vars in `backend/.env`:

  ```
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  STRIPE_PRICE_ID_PRO_MONTHLY=price_...
  ```

## Database Location

User accounts are stored in: `backend/estimategenie.db`

To reset (delete all users):

```powershell
Remove-Item backend\estimategenie.db
```

The database will be recreated on next API startup.

## Environment Configuration

1. Copy the example: `backend\.env.example` → `backend\.env`
2. Set required vars:

   ```
   JWT_SECRET_KEY=your-long-random-secret-here
   ALLOW_ORIGINS=http://localhost:8080,http://localhost:3000
   ```

## Testing the Full Flow

1. Start servers: `.\start-dev.ps1`
2. Open browser: <http://localhost:8080>
3. Click "Try Free Now" → redirects to signup
4. Create account → redirects to dashboard
5. Generate a quote with an image

## Production Deployment

See `DEPLOYMENT_README.md` for production setup.
