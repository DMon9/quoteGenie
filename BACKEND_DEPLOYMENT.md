# Backend Deployment Guide

## Overview

The EstimateGenie backend consists of:

1. **Backend API** (`backend/`) - Main FastAPI service with vision, LLM, and estimation
2. **Orchestrator** (`orchestrator/`) - LangChain-based AI orchestration service
3. **API Worker** (`api-worker/`) - Cloudflare Worker for API routing

## Quick Deployment Options

### Option 1: Render.com (Recommended - Free Tier)

**Pros:** Free tier, auto-deploy from Git, managed PostgreSQL
**Cons:** Cold starts on free tier

```bash
# 1. Create account at render.com
# 2. Connect GitHub repo
# 3. Render will auto-detect render.yaml in /backend
# 4. Set environment variables:
#    - DATABASE_URL (auto-provided by Render PostgreSQL)
#    - OLLAMA_URL (leave as localhost or use external Ollama service)
#    - HF_TOKEN (if using gated models)
# 5. Deploy!
```

**Post-deployment:**
- Copy backend URL (e.g., `https://estimategenie-backend.onrender.com`)
- Update `api-worker/index.js` with the URL
- Deploy API worker (see step 4 below)

### Option 2: Railway.app

**Pros:** Easy deployment, good free tier, automatic HTTPS
**Cons:** Requires credit card for free tier

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Deploy backend
railway up

# Deploy orchestrator
cd ../orchestrator
railway up

# Get deployment URLs
railway status
```

### Option 3: Fly.io

**Pros:** Global edge deployment, excellent performance
**Cons:** Limited free tier

```bash
# Install flyctl
# Windows: iwr https://fly.io/install.ps1 -useb | iex

# Login
flyctl auth login

# Deploy backend
cd backend
flyctl launch --config ../fly.toml

# Deploy orchestrator
cd ../orchestrator
flyctl launch --name estimategenie-orchestrator
```

### Option 4: Docker Compose (Self-Hosted)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# With models
docker-compose --profile models up -d
```

## Step-by-Step: Render.com Deployment

### 1. Deploy Backend

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `estimategenie-backend`
   - **Root Directory:** `backend`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   ```
   PYTHON_VERSION=3.11
   OLLAMA_URL=http://localhost:11434
   ```
6. Click **Create Web Service**
7. Wait for deployment (~5-10 minutes)
8. Copy the service URL

### 2. Deploy Orchestrator

1. Click **New +** → **Web Service**
2. Same repository
3. Configure:
   - **Name:** `estimategenie-orchestrator`
   - **Root Directory:** `orchestrator`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   ```
   PYTHON_VERSION=3.11
   OLLAMA_BASE_URL=http://localhost:11435
   OLLAMA_MODEL=llama3.2:1b
   ```
5. Deploy and copy URL

### 3. Deploy PostgreSQL (Optional)

1. Click **New +** → **PostgreSQL**
2. Name: `estimategenie-db`
3. Copy connection string
4. Add `DATABASE_URL` to backend service environment variables

### 4. Deploy API Worker (Cloudflare)

```powershell
# Update api-worker/index.js with your backend URLs
# Then deploy:

cd api-worker
wrangler deploy
```

**Result:** Worker deployed at `https://estimategenie-api.workers.dev`

### 5. Update Frontend

Update your HTML files to use the API:

```javascript
// In your frontend JavaScript
const API_BASE = 'https://estimategenie-api.workers.dev/api';

// Create quote
fetch(`${API_BASE}/v1/quotes`, {
  method: 'POST',
  body: formData
});
```

## Environment Variables Reference

### Backend (`backend/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `OLLAMA_URL` | Ollama service URL | `http://localhost:11434` |
| `HF_TOKEN` | HuggingFace API token | `hf_...` |
| `MODELS_DIR` | Local model storage path | `/models` |

### Orchestrator (`orchestrator/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11435` |
| `OLLAMA_MODEL` | Default model name | `llama3.2:1b` |
| `DATABASE_URL` | PostgreSQL connection | Same as backend |

### API Worker (`api-worker/`)

| Variable | Description | Set in |
|----------|-------------|--------|
| `BACKEND_URL` | Backend service URL | `index.js` |
| `ORCHESTRATOR_URL` | Orchestrator URL | `index.js` |

## Testing Deployment

### 1. Health Check

```bash
curl https://estimategenie-backend.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T...",
  "services": {
    "vision": true,
    "llm": false,
    "database": true
  }
}
```

### 2. API Worker Health

```bash
curl https://estimategenie-api.workers.dev/api/health
```

### 3. Create Test Quote

```bash
curl -X POST https://estimategenie-api.workers.dev/api/v1/quotes \
  -F "file=@test-image.jpg" \
  -F "project_type=bathroom" \
  -F "description=Small bathroom renovation"
```

## Troubleshooting

### Backend shows "unhealthy" for LLM service

**Cause:** Ollama not running
**Solution:** Either:
1. Deploy Ollama separately (Modal, RunPod, Replicate)
2. Use OpenAI/Anthropic instead by updating `llm_service.py`
3. Accept that LLM features won't work (vision + estimation still work)

### Database connection errors

**Cause:** Missing `DATABASE_URL`
**Solution:** Add PostgreSQL instance and set environment variable

### API Worker returns 502

**Cause:** Backend URL incorrect or backend is down
**Solution:** 
1. Check backend is deployed and running
2. Verify URL in `api-worker/index.js`
3. Redeploy worker: `wrangler deploy`

### CORS errors in browser

**Cause:** CORS headers not set properly
**Solution:** Ensure API worker is deployed and routing requests (it adds CORS headers)

## Cost Estimates

### Free Tier (Recommended for testing)

| Service | Provider | Limits |
|---------|----------|--------|
| Backend | Render.com | 750 hours/month, sleeps after 15min inactive |
| Orchestrator | Render.com | 750 hours/month, sleeps after 15min inactive |
| Database | Render.com | 90 days free, then $7/month |
| API Worker | Cloudflare | 100k requests/day free |
| Static Site | Cloudflare Pages | Unlimited |

**Total:** $0/month for first 90 days, then $7/month

### Production Tier

| Service | Provider | Cost |
|---------|----------|------|
| Backend | Render.com Starter | $7/month |
| Orchestrator | Render.com Starter | $7/month |
| Database | Render.com Standard | $7/month |
| API Worker | Cloudflare Workers Paid | $5/month |
| Static Site | Cloudflare Pages | Free |

**Total:** ~$26/month

## Current Status

- ✅ Static frontend deployed to Cloudflare Pages
- ✅ API Worker code ready (`api-worker/`)
- ✅ Backend ready for deployment (`backend/`, `orchestrator/`)
- ⏳ Waiting for backend URL to deploy API Worker
- ⏳ Waiting for API Worker URL to update frontend

## Next Steps

1. **Choose deployment platform** (Render.com recommended)
2. **Deploy backend services** (follow steps above)
3. **Get backend URLs**
4. **Update `api-worker/index.js`** with backend URLs
5. **Deploy API Worker:** `cd api-worker && wrangler deploy`
6. **Test end-to-end**

---

**Need help?** See troubleshooting section or check service logs in your provider's dashboard.
