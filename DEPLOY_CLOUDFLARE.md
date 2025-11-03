# Deploy EstimateGenie to Cloudflare

This guide covers deploying EstimateGenie with:

- **Frontend**: Cloudflare Pages (static site)
- **API Worker**: Cloudflare Workers (API proxy)
- **Backend**: Render/Railway/Fly.io (FastAPI + Python)

---

## Architecture

```
User Browser
    ↓
Cloudflare Pages (Frontend - HTML/CSS/JS)
    ↓
Cloudflare Worker (API Proxy)
    ↓
Backend Service (FastAPI on Render/Railway/Fly.io)
    ↓
Gemini API
```

---

## Prerequisites

1. **Cloudflare Account** - Free tier works
2. **Wrangler CLI** - Cloudflare's deployment tool
3. **GitHub Account** - For Cloudflare Pages auto-deploy
4. **Google API Key** - For Gemini LLM (already have)
5. **Backend hosting account** - Render/Railway/Fly.io

### Install Wrangler

```powershell
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

---

## Part 1: Deploy Frontend to Cloudflare Pages

### Option A: Via Wrangler CLI (Quick)

```powershell
# From project root
cd C:\Users\user\quoteGenie

# Deploy frontend files
wrangler pages deploy . --project-name estimategenie

# When prompted, select:
# - Production branch: main
# - Include: index.html, *.html, assets/*, robots.txt, sitemaps.xml
```

### Option B: Via GitHub + Cloudflare Dashboard (Recommended)

1. **Push to GitHub:**

   ```powershell
   git add .
   git commit -m "Prepare for Cloudflare deployment"
   git push origin main
   ```

2. **Create Cloudflare Pages project:**
   - Go to <https://dash.cloudflare.com>
   - Pages → Create a project
   - Connect to GitHub → Select your repo
   - Configure build:
     - Framework preset: **None**
     - Build command: *(leave empty)*
     - Build output directory: `/`
     - Root directory: `/`
   - Click **Save and Deploy**

3. **Configure custom domain (optional):**
   - Pages → Your project → Custom domains
   - Add `estimategenie.net` or subdomain
   - Cloudflare will auto-configure DNS

### What gets deployed

- `index.html` - Home page
- `test-upload-v2.html` - Quote upload page
- `about.html`, `features.html`, etc. - Marketing pages
- `assets/` - CSS, images, JS
- `robots.txt`, `sitemaps.xml` - SEO

---

## Part 2: Deploy Backend API

Choose one platform:

### Option A: Deploy to Render

1. **Create account:** <https://render.com>

2. **Create new Web Service:**
   - Connect GitHub repo
   - Name: `estimategenie-api`
   - Region: Oregon (US West) or closest to you
   - Branch: `main`
   - Root Directory: `backend`
   - Runtime: **Python 3**
   - Build Command:

     ```bash
     pip install -r requirements.txt
     ```

   - Start Command:

     ```bash
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```

3. **Environment Variables:**

   ```
   PYTHON_VERSION=3.11.0
   LLM_PROVIDER=gemini
   GEMINI_MODEL=gemini-2.5-flash
   GOOGLE_API_KEY=<your-key>
   PRICE_LIST_FILE=./pricing/materials_pricing_400.json
   ALLOW_ORIGINS=https://estimategenie.pages.dev,https://estimategenie.net
   ```

4. **Add Disk for pricing file:**
   - Disks → Add Disk
   - Name: `pricing-data`
   - Mount Path: `/app/pricing`
   - Size: 1 GB

5. **Upload pricing file:**

   ```powershell
   # Via Render CLI or dashboard file upload
   render disk upload pricing-data ./backend/pricing/materials_pricing_400.json
   ```

6. **Deploy** - Note the URL: `https://estimategenie-api.onrender.com`

### Option B: Deploy to Railway

1. **Create account:** <https://railway.app>

2. **New Project:**

   ```powershell
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # Deploy from backend directory
   cd backend
   railway init
   railway up
   ```

3. **Configure via railway.toml:**

   ```toml
   [build]
   builder = "NIXPACKS"
   
   [deploy]
   startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
   healthcheckPath = "/health"
   
   [[mounts]]
   source = "pricing-data"
   destination = "/app/pricing"
   ```

4. **Set variables:**

   ```powershell
   railway variables set GOOGLE_API_KEY=<your-key>
   railway variables set LLM_PROVIDER=gemini
   railway variables set GEMINI_MODEL=gemini-2.5-flash
   railway variables set ALLOW_ORIGINS=https://estimategenie.pages.dev
   ```

5. **Note the URL:** `https://estimategenie-api-production.up.railway.app`

### Option C: Deploy to Fly.io

1. **Install flyctl:**

   ```powershell
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Deploy:**

   ```powershell
   cd backend
   fly launch --name estimategenie-api
   
   # When prompted:
   # - Region: Choose closest
   # - Postgres: No
   # - Redis: No
   ```

3. **Set secrets:**

   ```powershell
   fly secrets set GOOGLE_API_KEY=<your-key>
   fly secrets set LLM_PROVIDER=gemini
   fly secrets set GEMINI_MODEL=gemini-2.5-flash
   fly secrets set ALLOW_ORIGINS=https://estimategenie.pages.dev
   ```

4. **Add volume for pricing:**

   ```powershell
   fly volumes create pricing_data --size 1
   ```

5. **Update fly.toml:**

   ```toml
   [[mounts]]
   source = "pricing_data"
   destination = "/app/pricing"
   ```

6. **Deploy:**

   ```powershell
   fly deploy
   ```

7. **Note the URL:** `https://quotegenie-api.fly.dev`

---

## Part 3: Deploy API Worker

1. **Update Worker with backend URL:**

   Edit `api-worker/index.js`:

   ```javascript
   // Your backend URL (origin). Prefer the public domain in the frontend (https://api.estimategenie.net)
   const BACKEND_URL = 'https://quotegenie-api.fly.dev';
   ```

2. **Update wrangler.toml:**

   Edit `api-worker/wrangler.toml`:

   ```toml
   name = "estimategenie-api"
   main = "index.js"
   compatibility_date = "2024-01-01"
   
   [vars]
   # Backend origin URL (can also be set via secrets)
   BACKEND_URL = "https://quotegenie-api.fly.dev"
   ENVIRONMENT = "production"
   ```

3. **Deploy Worker:**

   ```powershell
   cd api-worker
   wrangler deploy
   ```

4. **Note the Worker URL:** `https://estimategenie-api.<your-subdomain>.workers.dev`

---

## Part 4: Connect Frontend to Worker

1. **Update frontend API endpoint:**

   Edit `test-upload-v2.html` (line 219):

   ```javascript
   const API_BASE = "https://estimategenie-api.<your-subdomain>.workers.dev/api";
   ```

2. **Update all HTML files** that call the API:
   - `index.html` (if it has quote forms)
   - `dashboard.html`
   - Any other pages with API calls

3. **Redeploy frontend:**

   ```powershell
   wrangler pages deploy . --project-name estimategenie
   ```

   Or push to GitHub if using auto-deploy.

---

## Part 5: Test Deployment

### 1. Test Backend Directly

```powershell
# Prefer the public domain if DNS is set up
curl https://api.estimategenie.net/health

# Or test the origin directly (Fly.io)
curl https://quotegenie-api.fly.dev/health
```

**Expected:**

```json
{
  "status": "healthy",
  "services": { "vision": true, "llm": true, "database": true }
}
```

### 2. Test Worker Proxy

```powershell
curl https://estimategenie-api.<subdomain>.workers.dev/api/health
```

### 3. Test Frontend

1. Open `https://estimategenie.pages.dev`
2. Navigate to upload page
3. Check backend status badges (should be green)
4. Upload test image
5. Verify quote generation works

### 4. Test Pricing

```powershell
curl https://estimategenie-api.<subdomain>.workers.dev/api/v1/pricing/status
```

**Expected:**

```json
{
  "external_files": ["/app/pricing/materials_pricing_400.json"],
  "external_keys_count": 134
}
```

---

## Environment Variables Summary

### Cloudflare Pages (Frontend)

- Usually none needed (static site)

### Cloudflare Worker (API Proxy)

```
BACKEND_URL=https://quotegenie-api.fly.dev
ENVIRONMENT=production
```

### Backend (Render/Railway/Fly.io)

```
GOOGLE_API_KEY=AIzaSyBan9TR_G6naHIEWmu_ABvEMR0JNBRFMi4
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
PRICE_LIST_FILE=./pricing/materials_pricing_400.json
PRICE_LIST_RELOAD_SEC=10
ALLOW_ORIGINS=https://estimategenie.pages.dev,https://estimategenie.net
PORT=8000
```

---

## Pricing File Management

### Upload pricing list to backend

**Render:**

- Dashboard → Disk → Upload files

**Railway:**

```powershell
railway run --mount pricing-data:/app/pricing
# Then copy file into mounted volume
```

**Fly.io:**

```powershell
fly ssh console
# Inside VM:
cd /app/pricing
cat > materials_pricing_400.json
# Paste content, Ctrl+D
```

### Update pricing without redeployment

1. Upload new JSON file to disk/volume
2. Trigger reload:

   ```powershell
   # Via public domain through Worker routing
   curl -X POST https://api.estimategenie.net/api/v1/pricing/reload

   # Or directly against the backend origin (Fly.io)
   curl -X POST https://quotegenie-api.fly.dev/v1/pricing/reload
   ```

---

## Custom Domain Setup

### Frontend (Cloudflare Pages)

1. Pages → Custom domains → Add domain
2. Enter `estimategenie.net`
3. Cloudflare auto-configures DNS
4. SSL certificate auto-issued

### Worker (Optional custom subdomain)

1. Workers → Your worker → Triggers → Add Custom Domain
2. Enter `api.estimategenie.net`
3. Update frontend to use this URL

---

## Monitoring & Logs

### Cloudflare Pages

- Dashboard → Pages → Deployments
- View build logs
- Analytics tab for traffic

### Cloudflare Worker

- Dashboard → Workers → Your worker → Logs
- Real-time request logs
- Metrics tab for performance

### Backend

**Render:**

```powershell
# View logs
render logs estimategenie-api

# Or via dashboard → Logs tab
```

**Railway:**

```powershell
railway logs
```

**Fly.io:**

```powershell
fly logs
```

---

## Scaling & Performance

### Cloudflare Pages

- **Global CDN** - Automatic
- **Unlimited bandwidth** - Free tier
- **DDoS protection** - Automatic

### Cloudflare Worker

- **100,000 requests/day** - Free tier
- **CPU time: 10ms/request** - Free tier
- Upgrade to Paid for unlimited

### Backend

**Render Free Tier:**

- Spins down after 15 min inactivity
- Cold start: 30-60 seconds
- Upgrade to Starter ($7/month) for always-on

**Railway:**

- $5 free credit/month
- Pay-as-you-go after

**Fly.io:**

- Free tier: 3 shared CPUs, 256MB RAM
- Scales automatically

---

## Cost Estimate

### Free Tier Setup

- Cloudflare Pages: **$0/month**
- Cloudflare Worker: **$0/month** (up to 100k req/day)
- Backend (Render free): **$0/month** (with cold starts)
- **Total: $0/month**

### Production Setup

- Cloudflare Pages: **$0/month**
- Cloudflare Worker: **$5/month** (unlimited requests)
- Backend (Render Starter): **$7/month** (always-on)
- **Total: $12/month**

---

## Troubleshooting

### Frontend can't reach backend

- Check Worker BACKEND_URL is correct
- Verify CORS headers in backend ALLOW_ORIGINS
- Check Worker logs for proxy errors

### Root domain shows 522 (but www works)

When `https://estimategenie.net` returns Cloudflare 522 while `https://www.estimategenie.net` or `https://estimategenie.pages.dev` work, the apex DNS is pointing to the wrong origin or a Worker route is misconfigured.

Quick fixes:

1) Use a redirect rule (fastest)

- Cloudflare Dashboard → Rules → Redirect Rules → Create Rule
- If Hostname equals `estimategenie.net` → 301 redirect to `https://www.estimategenie.net`.
- This takes effect immediately and avoids any origin lookup.

2) Point apex to Pages (canonical)

- Pages → Your project → Custom domains → Add domain → `estimategenie.net`
- Cloudflare will add a proxied CNAME (flattened) to your Pages hostname.
- DNS → Remove any existing A/AAAA records for `@` (root) that point to other IPs.
- Wait a few minutes and re-test: `curl -I https://estimategenie.net` should be 200.

3) Check Workers/Routes

- Workers → Your worker → Triggers → Routes. Remove any route bound to `estimategenie.net/*` unless you intend to intercept the root. If you want a Worker only for the API, bind it to `api.estimategenie.net/*` instead.

Verification commands (PowerShell):

```powershell
nslookup estimategenie.net
curl.exe -I https://estimategenie.net
curl.exe -I https://www.estimategenie.net
```

### Pricing file not found

- Verify disk/volume is mounted
- Check file path in PRICE_LIST_FILE env var
- SSH into backend and verify file exists

### Cold start delays

- Upgrade backend to paid tier
- Use Worker health check to keep backend warm
- Add cron job to ping backend every 10 minutes

### SSL/HTTPS errors

- Cloudflare auto-issues SSL for Pages
- Ensure backend uses HTTPS URL in Worker
- Check firewall allows outbound HTTPS

---

## Quick Deploy Commands

```powershell
# 1. Deploy Frontend
wrangler pages deploy . --project-name estimategenie

# 2. Deploy Worker
cd api-worker
wrangler deploy

# 3. Deploy Backend (Railway example)
cd backend
railway up

# 4. Test
curl https://estimategenie.pages.dev
curl https://estimategenie-api.<subdomain>.workers.dev/api/health
```

---

## Next Steps

1. ✅ Deploy all three components
2. ✅ Configure custom domain
3. ✅ Test quote generation end-to-end
4. ✅ Set up pricing file volume
5. ✅ Configure monitoring/alerts
6. ☐ Add rate limiting (Cloudflare)
7. ☐ Set up CI/CD (GitHub Actions)
8. ☐ Add error tracking (Sentry)

---

**Status:** Ready to deploy  
**Estimated Time:** 30-45 minutes  
**Difficulty:** Intermediate
