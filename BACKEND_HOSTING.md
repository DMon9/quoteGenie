# Backend Hosting Comparison for QuoteGenie

## Quick Decision Matrix

| Provider | Best For | Free Tier | Pricing Disk | Setup Time | Difficulty |
|----------|----------|-----------|--------------|------------|------------|
| **Render** | Simplicity | ✅ 750hrs/mo | ✅ 1GB free | 5 min | ⭐ Easy |
| **Railway** | Flexibility | ✅ $5 credit/mo | ✅ Volume support | 3 min | ⭐⭐ Medium |
| **Fly.io** | Scalability | ✅ 3 VMs free | ✅ 3GB free | 10 min | ⭐⭐⭐ Hard |

## Detailed Comparison

### 1. Render (Recommended for Beginners)

**Pros:**
- ✅ Zero configuration needed - auto-detects `render.yaml`
- ✅ GitHub integration - auto-deploys on push
- ✅ Free persistent disk (1GB) for pricing files
- ✅ Built-in health checks and auto-restart
- ✅ Environment variable management via dashboard
- ✅ Free SSL certificates
- ✅ 750 hours/month free tier (always-on for 1 service)

**Cons:**
- ❌ Slower cold starts on free tier (~30 seconds)
- ❌ Services spin down after 15 minutes inactivity
- ❌ Limited to Oregon region on free tier

**Setup:**
1. Connect GitHub repo to Render
2. Select `backend/render-updated.yaml` blueprint
3. Add `GOOGLE_API_KEY` secret in dashboard
4. Upload `materials_pricing_400.json` to `/data/pricing/` via SSH
5. Deploy automatically starts

**Config File:** `backend/render-updated.yaml` ✅ Ready

**Best For:** 
- First deployment
- Quick proof-of-concept
- Personal projects
- Low traffic sites (<100 requests/day)

---

### 2. Railway (Recommended for Production)

**Pros:**
- ✅ Fast deployment (~2 minutes)
- ✅ No cold starts - always warm
- ✅ Volume support with pricing file persistence
- ✅ $5 free credit per month (~500 hours runtime)
- ✅ GitHub integration with auto-deploy
- ✅ PostgreSQL addon available (if needed later)
- ✅ Better performance than Render free tier

**Cons:**
- ❌ Requires credit card for free tier
- ❌ No persistent disk in free tier - use volumes ($0.25/GB)
- ❌ Configuration via Railway CLI or dashboard (no YAML)

**Setup:**
1. Install Railway CLI: `npm install -g railway`
2. Login: `railway login`
3. Link project: `railway link`
4. Set environment variables:
   ```bash
   railway variables set PYTHON_VERSION=3.11
   railway variables set LLM_PROVIDER=gemini
   railway variables set GEMINI_MODEL=gemini-2.5-flash
   railway variables set GOOGLE_API_KEY=your_key_here
   railway variables set PRICE_LIST_FILE=/data/pricing/materials_pricing_400.json
   railway variables set PRICE_LIST_RELOAD_SEC=10
   railway variables set ALLOW_ORIGINS=https://quotegenie.pages.dev
   ```
5. Create volume: `railway volume create pricing-data /data/pricing 1`
6. Deploy: `railway up`
7. Upload pricing file: `railway run bash` then copy file

**Config File:** `backend/railway.json` ✅ Ready

**Best For:**
- Production deployments
- Sites with moderate traffic
- Projects needing consistent performance
- Teams with budget for hosting

---

### 3. Fly.io (Recommended for Scale)

**Pros:**
- ✅ Generous free tier (3 VMs, 3GB persistent storage)
- ✅ Global edge deployment (160+ regions)
- ✅ Auto-scaling and load balancing
- ✅ No cold starts with always-on machines
- ✅ Built-in metrics and logging
- ✅ PostgreSQL support (if needed)
- ✅ Best performance of all three

**Cons:**
- ❌ Steeper learning curve (Fly CLI required)
- ❌ More complex configuration
- ❌ Requires credit card
- ❌ Longer initial setup

**Setup:**
1. Install Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Login: `flyctl auth login`
3. Launch app: `flyctl launch` (use existing `fly.toml`)
4. Set secrets: `flyctl secrets set GOOGLE_API_KEY=your_key_here`
5. Create volume: `flyctl volumes create pricing_data --size 1`
6. Deploy: `flyctl deploy`
7. Upload pricing file: `flyctl ssh console` then copy file

**Config File:** `backend/fly.toml` ✅ Ready

**Best For:**
- High-traffic production sites
- Global user base
- Advanced scaling requirements
- Long-term projects

---

## Feature Comparison

### Persistent Storage for Pricing Files

| Provider | Method | Free Tier | Upload Method |
|----------|--------|-----------|---------------|
| Render | Persistent Disk | 1GB | SSH/SFTP |
| Railway | Volume | ❌ ($0.25/GB) | Railway CLI |
| Fly.io | Volume | 3GB | Fly SSH |

### Environment Variables

| Provider | Method | Secrets Support |
|----------|--------|-----------------|
| Render | Dashboard UI | ✅ Encrypted |
| Railway | CLI/Dashboard | ✅ Encrypted |
| Fly.io | CLI | ✅ Encrypted |

### Auto-Deploy from GitHub

| Provider | Support | Config |
|----------|---------|--------|
| Render | ✅ Native | render.yaml |
| Railway | ✅ Native | Auto-detect |
| Fly.io | ✅ GitHub Actions | .github/workflows |

### Performance (Response Time)

| Provider | Cold Start | Warm Response | Uptime |
|----------|------------|---------------|--------|
| Render | ~30s | 200-500ms | 99.9% |
| Railway | None | 100-300ms | 99.95% |
| Fly.io | <1s | 50-150ms | 99.99% |

---

## Cost Breakdown (Monthly)

### Free Tier Usage
| Provider | Cost | Limitations |
|----------|------|-------------|
| Render | $0 | 750 hrs, spins down after 15min |
| Railway | $0 | $5 credit (~500 hrs) |
| Fly.io | $0 | 3 VMs, 160GB bandwidth |

### Paid Tier (After Free)
| Provider | Starter Plan | Includes |
|----------|--------------|----------|
| Render | $7/mo | Always-on, 512MB RAM |
| Railway | ~$10/mo | Pay-as-you-go, volume extra |
| Fly.io | ~$5/mo | Shared CPU, 256MB RAM |

---

## Recommendations by Use Case

### 🎯 **First Time Deploying?**
→ **Use Render** with `render-updated.yaml`
- Easiest setup
- No CLI required
- Visual dashboard
- Auto-deploy from GitHub

### 🎯 **Building a Real Product?**
→ **Use Railway** with `railway.json`
- No cold starts
- Better performance
- Reasonable pricing
- Easy scaling

### 🎯 **Expecting High Traffic?**
→ **Use Fly.io** with `fly.toml`
- Best performance
- Global CDN
- Auto-scaling
- Professional infrastructure

### 🎯 **Just Testing Locally?**
→ **Skip deployment**, use Docker Compose
- `docker-compose up -d`
- Test at http://localhost:8001
- No hosting costs

---

## Required Environment Variables (All Providers)

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash

# Pricing Configuration
PRICE_LIST_FILE=/data/pricing/materials_pricing_400.json
PRICE_LIST_RELOAD_SEC=10

# CORS Configuration
ALLOW_ORIGINS=https://quotegenie.pages.dev,https://quotegenie.net

# Optional
PYTHON_VERSION=3.11
PORT=8000  # Render/Railway use $PORT automatically
```

---

## Post-Deployment Steps (All Providers)

1. **Verify Backend Health**
   ```bash
   curl https://your-backend-url/health
   # Expected: {"status":"healthy","version":"1.0.0","services":{"vision":true,"llm":true,"database":true}}
   ```

2. **Upload Pricing File**
   - Render: Use SSH or SFTP to `/data/pricing/materials_pricing_400.json`
   - Railway: `railway run bash` then `scp` or `wget`
   - Fly.io: `flyctl ssh console` then `curl -o /data/pricing/materials_pricing_400.json`

3. **Verify Pricing Loaded**
   ```bash
   curl https://your-backend-url/v1/pricing/status
   # Expected: {"external_price_keys":134,"total_materials":143,...}
   ```

4. **Update Cloudflare Worker**
   - Edit `api-worker/index.js`
   - Replace `BACKEND_URL` with your deployed backend URL
   - Redeploy worker: `wrangler deploy`

5. **Update Frontend**
   - Edit HTML files (test-upload-v2.html, etc.)
   - Replace API endpoints with worker URL
   - Redeploy to Cloudflare Pages

6. **Test End-to-End**
   - Open https://quotegenie.pages.dev/test-upload-v2.html
   - Upload test construction image
   - Verify quote generation with pricing

---

## Troubleshooting

### Pricing File Not Loading
```bash
# Check file exists
railway run ls -la /data/pricing/
# or
flyctl ssh console -C "ls -la /data/pricing/"

# Check logs
railway logs
# or
flyctl logs
```

### LLM Timeout Errors
- Increase timeout in `services/llm_service.py`: `timeout=120`
- Upgrade to paid tier for better performance
- Use shorter/smaller images for testing

### CORS Errors
- Verify `ALLOW_ORIGINS` includes your frontend domain
- Check worker proxy CORS headers
- Test with curl: `curl -H "Origin: https://quotegenie.pages.dev" https://backend-url/health`

---

## Next Steps

1. **Choose your provider** based on the recommendations above
2. **Deploy backend** using the provided config file
3. **Note the deployed URL** (e.g., `https://quotegenie-api.onrender.com`)
4. **Update worker** with backend URL in `api-worker/index.js`
5. **Deploy frontend** to Cloudflare Pages
6. **Test the full system** end-to-end

All configuration files are ready in the `backend/` directory:
- ✅ `render-updated.yaml` - For Render deployment
- ✅ `railway.json` - For Railway deployment  
- ✅ `fly.toml` - For Fly.io deployment

Choose one and follow the setup instructions above!
