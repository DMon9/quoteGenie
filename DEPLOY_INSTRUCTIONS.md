# 🚀 DEPLOYMENT SCRIPT - PREMIUM SITE

## Running deployment...

This will:
1. Copy index-premium.html → index.html
2. Deploy entire site to Cloudflare Pages
3. Make your premium design live

---

**Note**: Due to PowerShell environment limitations, please run deployment manually:

### Option 1: Quick Deploy (Recommended)

```bash
# From EstimateGenie root directory

# Windows CMD:
copy index-premium.html index.html && wrangler pages deploy . --project-name estimategenie --branch main

# PowerShell:
Copy-Item index-premium.html index.html -Force; wrangler pages deploy . --project-name estimategenie --branch main

# Linux/Mac:
cp index-premium.html index.html && wrangler pages deploy . --project-name estimategenie --branch main
```

### Option 2: Step by Step

```bash
# Step 1: Activate premium theme
copy index-premium.html index.html   # Windows
cp index-premium.html index.html     # Linux/Mac

# Step 2: Deploy
wrangler pages deploy . --project-name estimategenie --branch main
```

### Option 3: Use deployment script

```bash
# Run the deployment script
.\deploy-premium.ps1   # PowerShell
./deploy-premium.sh    # Linux/Mac
```

---

## What Gets Deployed

✅ Premium dark theme landing page (index.html)
✅ All site assets (CSS, JS, images)
✅ Backend API (if configured)
✅ All HTML pages (pricing, features, docs, etc.)

---

## After Deployment

Your site will be live at:
- https://estimategenie.pages.dev
- https://estimategenie.net (if domain is configured)

---

Ready to deploy? Copy the command above and run it in your terminal!
