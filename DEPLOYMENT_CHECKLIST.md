# QuoteGenie Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment Preparation

- [ ] Read `BACKEND_HOSTING.md` and choose provider (Render/Railway/Fly.io)
- [ ] Read `DEPLOY_CLOUDFLARE.md` for complete deployment guide
- [ ] Ensure you have your `GOOGLE_API_KEY` for Gemini ready
- [ ] Have `pricing/materials_pricing_400.json` file ready for upload
- [ ] Install required CLI tools:
  - [ ] Node.js and npm
  - [ ] wrangler: `npm install -g wrangler`
  - [ ] railway CLI (if using Railway): `npm install -g railway`
  - [ ] flyctl (if using Fly.io): Download from fly.io/docs

---

## Phase 1: Backend Deployment

### Option A: Render (Easiest) ⭐

- [ ] Go to https://dashboard.render.com
- [ ] Connect GitHub repository
- [ ] Create new Blueprint
- [ ] Select `backend/render-updated.yaml`
- [ ] Add Secret: `GOOGLE_API_KEY` = your_key
- [ ] Click "Apply" to deploy
- [ ] Wait for deployment (~3-5 minutes)
- [ ] Note backend URL: `https://quotegenie-api.onrender.com`
- [ ] Access Render Shell from dashboard
- [ ] Create directory: `mkdir -p /data/pricing`
- [ ] Upload `materials_pricing_400.json` via SFTP or paste content
- [ ] Test: `curl https://your-backend-url/health`
- [ ] Test: `curl https://your-backend-url/v1/pricing/status`

### Option B: Railway (Best Performance)

- [ ] Install Railway CLI: `npm install -g railway`
- [ ] Login: `railway login`
- [ ] Create new project in dashboard
- [ ] Link local repo: `railway link`
- [ ] Set environment variables:
  ```bash
  railway variables set PYTHON_VERSION=3.11
  railway variables set LLM_PROVIDER=gemini
  railway variables set GEMINI_MODEL=gemini-2.5-flash
  railway variables set GOOGLE_API_KEY=your_key
  railway variables set PRICE_LIST_FILE=/data/pricing/materials_pricing_400.json
  railway variables set PRICE_LIST_RELOAD_SEC=10
  railway variables set ALLOW_ORIGINS=https://quotegenie.pages.dev
  ```
- [ ] Create volume: `railway volume create pricing-data /data/pricing 1`
- [ ] Deploy: `railway up`
- [ ] Wait for deployment (~2 minutes)
- [ ] Note backend URL from Railway dashboard
- [ ] Upload pricing: `railway run bash` then copy file
- [ ] Test: `curl https://your-backend-url/health`
- [ ] Test: `curl https://your-backend-url/v1/pricing/status`

### Option C: Fly.io (Best Scale)

- [ ] Install Fly CLI from https://fly.io/docs/hands-on/install-flyctl/
- [ ] Login: `flyctl auth login`
- [ ] Navigate to backend: `cd backend`
- [ ] Launch: `flyctl launch` (use existing fly.toml)
- [ ] Set secret: `flyctl secrets set GOOGLE_API_KEY=your_key`
- [ ] Create volume: `flyctl volumes create pricing_data --size 1`
- [ ] Deploy: `flyctl deploy`
- [ ] Wait for deployment (~5 minutes)
- [ ] Note backend URL: `https://quotegenie-api.fly.dev`
- [ ] Upload pricing: `flyctl ssh console` then copy file
- [ ] Test: `curl https://your-backend-url/health`
- [ ] Test: `curl https://your-backend-url/v1/pricing/status`

**Backend URL:** _______________________________________________

---

## Phase 2: Verify Backend

- [ ] Health check passes:
  ```bash
  curl https://your-backend-url/health
  ```
  Expected: `{"status":"healthy","services":{"vision":true,"llm":true,"database":true}}`

- [ ] Pricing loaded correctly:
  ```bash
  curl https://your-backend-url/v1/pricing/status
  ```
  Expected: `{"external_price_keys":134,"total_materials":143,...}`

- [ ] Sample price lookup works:
  ```bash
  curl https://your-backend-url/v1/pricing/lookup?key=lumber_2x4
  ```
  Expected: `{"key":"lumber_2x4","price":6.49,"source":"external-list",...}`

- [ ] Force reload works:
  ```bash
  curl -X POST https://your-backend-url/v1/pricing/reload
  ```
  Expected: `{"success":true,"loaded_from":"/data/pricing/materials_pricing_400.json",...}`

---

## Phase 3: Cloudflare Worker Deployment

- [ ] Navigate to worker directory: `cd api-worker`

- [ ] Edit `index.js` and update backend URL:
  ```javascript
  const BACKEND_URL = "https://your-actual-backend-url";
  ```

- [ ] Test worker config:
  ```bash
  npx wrangler whoami
  ```

- [ ] Login if needed:
  ```bash
  npx wrangler login
  ```

- [ ] Deploy worker:
  ```bash
  npx wrangler deploy
  ```

- [ ] Note worker URL from deployment output

- [ ] Test worker health:
  ```bash
  curl https://your-worker-url/api/health
  ```
  Should return backend health response

- [ ] Test CORS:
  ```bash
  curl -H "Origin: https://quotegenie.pages.dev" \
       https://your-worker-url/api/health
  ```
  Check for `Access-Control-Allow-Origin` header

**Worker URL:** _______________________________________________

---

## Phase 4: Frontend Deployment

### Option A: Automated (Recommended)

- [ ] Run deployment script:
  ```powershell
  .\deploy_cloudflare.ps1
  ```

- [ ] Follow interactive prompts
- [ ] Note the deployed Pages URL

### Option B: Manual

- [ ] Navigate to project root: `cd c:\Users\user\quoteGenie`

- [ ] Update HTML files with worker URL:
  - [ ] `test-upload-v2.html`
  - [ ] `index.html` (if applicable)
  - [ ] `dashboard.html` (if applicable)
  
  Replace `http://localhost:8001` with worker URL

- [ ] Deploy to Cloudflare Pages:
  ```bash
  npx wrangler pages deploy . --project-name quotegenie
  ```

- [ ] Note Pages URL: `https://quotegenie.pages.dev`

- [ ] Update worker CORS if needed:
  Edit `api-worker/index.js` ALLOW_ORIGINS to include Pages URL

**Pages URL:** _______________________________________________

---

## Phase 5: End-to-End Testing

- [ ] Open frontend: `https://quotegenie.pages.dev/test-upload-v2.html`

- [ ] Verify backend status badges are green

- [ ] Upload test construction image (from `backend/test_images/` or create one)

- [ ] Verify quote generation:
  - [ ] Materials detected (8+ items)
  - [ ] Labor hours calculated (10-20 hrs)
  - [ ] Total cost displayed ($10,000-$20,000 range)
  - [ ] Timeline shows phases
  - [ ] Cost breakdown visible

- [ ] Test pricing system:
  - [ ] Materials have prices
  - [ ] Prices match external list
  - [ ] Labor costs calculated

- [ ] Test hot-reload (advanced):
  - [ ] Modify pricing file on backend
  - [ ] Trigger reload: `curl -X POST backend-url/v1/pricing/reload`
  - [ ] Upload new quote and verify price changes

---

## Phase 6: Production Configuration

- [ ] Update CORS origins in backend:
  - Render: Dashboard → Environment → Edit `ALLOW_ORIGINS`
  - Railway: `railway variables set ALLOW_ORIGINS=https://quotegenie.pages.dev`
  - Fly.io: `flyctl secrets set ALLOW_ORIGINS=https://quotegenie.pages.dev`

- [ ] Configure custom domain (optional):
  - [ ] Add domain to Cloudflare Pages
  - [ ] Update DNS records
  - [ ] Update ALLOW_ORIGINS with custom domain
  - [ ] Redeploy worker with new domain

- [ ] Set up monitoring:
  - [ ] Render: Dashboard → Metrics
  - [ ] Railway: Dashboard → Metrics
  - [ ] Fly.io: `flyctl dashboard metrics`
  - [ ] Cloudflare: Pages → Analytics

- [ ] Configure alerts (optional):
  - [ ] Backend downtime alerts
  - [ ] Error rate thresholds
  - [ ] Usage limit warnings

---

## Phase 7: Documentation

- [ ] Document deployed URLs:
  - Backend: _______________________________________________
  - Worker: _______________________________________________
  - Frontend: _______________________________________________

- [ ] Save environment variables securely

- [ ] Document pricing file upload procedure

- [ ] Create runbook for common issues

- [ ] Share access with team (if applicable)

---

## Troubleshooting Reference

### Backend Issues

**Problem:** Health check fails
- [ ] Check logs: `railway logs` / `flyctl logs` / Render dashboard
- [ ] Verify GOOGLE_API_KEY is set
- [ ] Check Python version (3.11+)
- [ ] Verify requirements.txt installed

**Problem:** Pricing not loading
- [ ] Check file exists: `railway run ls /data/pricing/`
- [ ] Verify PRICE_LIST_FILE path in environment
- [ ] Check file format (valid JSON)
- [ ] Review backend logs for load errors

### Worker Issues

**Problem:** CORS errors
- [ ] Verify ALLOW_ORIGINS includes frontend URL
- [ ] Check worker CORS headers in response
- [ ] Test with curl: `curl -H "Origin: ..." worker-url/api/health`

**Problem:** Worker can't reach backend
- [ ] Verify BACKEND_URL is correct in index.js
- [ ] Test backend directly: `curl backend-url/health`
- [ ] Check worker logs: `npx wrangler tail`

### Frontend Issues

**Problem:** API calls fail
- [ ] Check browser console for errors
- [ ] Verify worker URL is correct in HTML
- [ ] Test worker: `curl worker-url/api/health`
- [ ] Check CORS headers

**Problem:** Upload fails
- [ ] Check file size (<10MB)
- [ ] Verify image format (PNG/JPG)
- [ ] Check backend logs for errors
- [ ] Test with smaller image

---

## Success Criteria ✅

Your deployment is successful when:

- [ ] Backend health check returns `"status":"healthy"`
- [ ] Pricing status shows `"external_price_keys":134`
- [ ] Worker proxies requests correctly
- [ ] Frontend loads and connects to backend
- [ ] Test quote upload completes successfully
- [ ] Materials, labor, and cost breakdown display correctly
- [ ] Hot-reload triggers on pricing file update
- [ ] All documentation URLs updated with production values

---

## Post-Deployment

- [ ] Monitor backend performance first 24 hours
- [ ] Check error rates in Cloudflare dashboard
- [ ] Verify pricing updates propagate correctly
- [ ] Test from different devices/locations
- [ ] Collect user feedback
- [ ] Plan scaling strategy if needed

---

## Notes & Issues

Use this space to track issues during deployment:

_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________

---

## Quick Reference Commands

```bash
# Backend health
curl https://backend-url/health

# Pricing status
curl https://backend-url/v1/pricing/status

# Force reload
curl -X POST https://backend-url/v1/pricing/reload

# Price lookup
curl https://backend-url/v1/pricing/lookup?key=lumber_2x4

# Worker health (via proxy)
curl https://worker-url/api/health

# Deploy worker
npx wrangler deploy --config api-worker/wrangler.toml

# Deploy frontend
npx wrangler pages deploy . --project-name quotegenie

# View logs
railway logs        # Railway
flyctl logs         # Fly.io
# Render: Dashboard → Logs

# Worker logs
npx wrangler tail
```

---

**Ready to deploy? Start with Phase 1! 🚀**
