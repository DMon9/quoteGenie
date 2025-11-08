# EstimateGenie - Development Setup

## ⚠️ Important: Backend is on Fly.io

**The backend API is deployed on Fly.io, NOT running locally!**

- **Production Backend**: <https://quotegenie-api.fly.dev>
- **Your frontend connects to Fly.io automatically**

## 🚀 Quick Start

**You only need to run the frontend:**

```powershell
python -m http.server 8080
```

Then open: <http://localhost:8080>

That's it! The frontend automatically connects to `https://quotegenie-api.fly.dev`.

## ✅ Testing Signup Now

1. Open <http://localhost:8080/signup.html>
2. Fill in the form:
   - Name: Your Name
   - Email: <your-email@example.com>
   - Password: password123 (8+ chars)
   - Plan: Starter (Free)
3. Check "I agree to terms"
4. Click "Create Account"

**Result**: Account created in production Fly.io database, redirects to dashboard.

## 🔧 Local Backend Development (Optional)

Only if you need to test backend code changes locally:

### Override API URL

**Browser Console:**

```javascript
localStorage.setItem('API_BASE_URL', 'http://localhost:8000')
location.reload()
```

**Or use URL parameter:**

```
http://localhost:8080/signup.html?api=http://localhost:8000
```

### Start Local Backend

```powershell
cd backend
..\.venv-3\Scripts\Activate.ps1
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Reset to Fly.io

```javascript
localStorage.removeItem('API_BASE_URL')
location.reload()
```

## 📍 API Endpoints

- **Fly.io Production**: <https://quotegenie-api.fly.dev>
- **Health Check**: <https://quotegenie-api.fly.dev/health>
- **API Docs**: <https://quotegenie-api.fly.dev/docs>
- **Ping**: <https://quotegenie-api.fly.dev/api/v1/ping>

## 🗄️ Database

- **Production DB**: Fly.io persistent volume (production accounts live here)
- **Local DB**: `backend/estimategenie.db` (only used when testing locally)

## 🐛 Troubleshooting

### "Cannot connect to API server"

Check if Fly.io backend is up:

```powershell
curl https://quotegenie-api.fly.dev/health
```

### "Email already registered"

That email exists in the production database. Try a different email.

### Testing with Local Backend

1. Set localStorage override (see above)
2. Start local backend on port 8000
3. Use a different database by renaming `backend/estimategenie.db`

## 📦 Deployment

- **Frontend**: Cloudflare Pages (deploys from git)
- **Backend**: Fly.io (deploys via `fly deploy`)

See `DEPLOYMENT_README.md` for production deployment steps.
