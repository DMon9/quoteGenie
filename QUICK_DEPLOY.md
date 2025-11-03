# 🚀 QuoteGenie Quick Deploy

## One-Command Deploy (Recommended)

```powershell
# Run the automated deployment script
.\deploy_cloudflare.ps1
```

---

## Manual 3-Step Deploy

### Step 1: Deploy Backend (Choose One)

**Render (Easiest):**
1. https://dashboard.render.com → New Blueprint
2. Select `backend/render-updated.yaml`
3. Add secret: `GOOGLE_API_KEY`
4. Deploy → Upload `materials_pricing_400.json` to `/data/pricing/`

**Railway (Fastest):**
```bash
railway login
railway up
railway variables set GOOGLE_API_KEY=your_key
```

**Fly.io (Scalable):**
```bash
flyctl launch
flyctl secrets set GOOGLE_API_KEY=your_key
flyctl deploy
```

### Step 2: Update Worker

```bash
cd api-worker
# Edit index.js: BACKEND_URL = "https://your-backend-url"
npx wrangler deploy
```

### Step 3: Deploy Frontend

```bash
npx wrangler pages deploy . --project-name quotegenie
```

---

## Verify Deployment

```bash
# Backend health
curl https://your-backend-url/health

# Pricing loaded
curl https://your-backend-url/v1/pricing/status

# Worker proxy
curl https://your-worker-url/api/health

# Frontend (open in browser)
https://estimategenie.pages.dev/test-upload-v2.html
```

---

## Config Files Ready

- ✅ `backend/render-updated.yaml` - Render config
- ✅ `backend/railway.json` - Railway config
- ✅ `backend/fly.toml` - Fly.io config
- ✅ `api-worker/wrangler.toml` - Worker config
- ✅ `_redirects` - Pages config
- ✅ `deploy_cloudflare.ps1` - Automation script

---

## Required Secrets

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Set via provider dashboard or CLI

---

## Documentation

- 📋 **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist
- 📖 **DEPLOY_CLOUDFLARE.md** - Complete deployment guide
- 🏢 **BACKEND_HOSTING.md** - Provider comparison
- 📝 **DEPLOYMENT_SUMMARY.md** - Overview and architecture

---

## Cost

**Free Tier:** $0/month
- Cloudflare Pages: Free
- Cloudflare Workers: Free (100k req/day)
- Render Backend: Free (750 hrs/month)

**Paid Tier:** ~$10/month
- Railway/Fly.io always-on backend

---

## Support

Issues? Check:
1. Backend logs (provider dashboard)
2. Worker logs (`npx wrangler tail`)
3. Browser console (F12)
4. DEPLOYMENT_CHECKLIST.md troubleshooting section

---

**Ready? Run:** `.\deploy_cloudflare.ps1` 🚀
