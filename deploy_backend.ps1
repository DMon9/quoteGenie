# EstimateGenie Backend - Quick Deploy Script
# This script helps you deploy the backend to Render.com

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  EstimateGenie Backend Deployment Helper" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Deployment Summary:" -ForegroundColor White
Write-Host ""
Write-Host "1. ✅ Static Site:    https://22585f31.estimategenie.pages.dev" -ForegroundColor Green
Write-Host "2. ✅ API Worker:     https://estimategenie-api.thesportsdugout.workers.dev" -ForegroundColor Green
Write-Host "3. ⏳ Backend:        Needs deployment" -ForegroundColor Yellow
Write-Host "4. ⏳ Orchestrator:   Needs deployment" -ForegroundColor Yellow
Write-Host ""

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Recommended: Deploy to Render.com" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Steps:" -ForegroundColor White
Write-Host ""
Write-Host "1. Go to https://render.com/dashboard" -ForegroundColor Gray
Write-Host "2. Click 'New +' → 'Web Service'" -ForegroundColor Gray
Write-Host "3. Connect your GitHub repository" -ForegroundColor Gray
Write-Host ""
Write-Host "Backend Configuration:" -ForegroundColor Yellow
Write-Host "  Name:           estimategenie-backend" -ForegroundColor Gray
Write-Host "  Root Directory: backend" -ForegroundColor Gray
Write-Host "  Build Command:  pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "  Start Command:  uvicorn app:app --host 0.0.0.0 --port `$PORT" -ForegroundColor Gray
Write-Host ""
Write-Host "Orchestrator Configuration:" -ForegroundColor Yellow
Write-Host "  Name:           estimategenie-orchestrator" -ForegroundColor Gray
Write-Host "  Root Directory: orchestrator" -ForegroundColor Gray
Write-Host "  Build Command:  pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "  Start Command:  uvicorn main:app --host 0.0.0.0 --port `$PORT" -ForegroundColor Gray
Write-Host ""

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  After Deployment" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Copy your backend URL (e.g., https://estimategenie-backend.onrender.com)" -ForegroundColor Gray
Write-Host "2. Update api-worker/index.js:" -ForegroundColor Gray
Write-Host "   const BACKEND_URL = YOUR_BACKEND_URL" -ForegroundColor DarkGray
Write-Host "3. Redeploy API worker:" -ForegroundColor Gray
Write-Host "   cd api-worker; wrangler deploy" -ForegroundColor DarkGray
Write-Host ""

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Current Status" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend directory exists
if (Test-Path "backend/app.py") {
    Write-Host "✅ Backend code ready" -ForegroundColor Green
}
else {
    Write-Host "❌ Backend code not found" -ForegroundColor Red
}

# Check if orchestrator exists
if (Test-Path "orchestrator/main.py") {
    Write-Host "✅ Orchestrator code ready" -ForegroundColor Green
}
else {
    Write-Host "❌ Orchestrator code not found" -ForegroundColor Red
}

# Check if requirements exist
if (Test-Path "backend/requirements.txt") {
    Write-Host "✅ Backend requirements.txt found" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Backend requirements.txt missing" -ForegroundColor Yellow
}

if (Test-Path "orchestrator/requirements.txt") {
    Write-Host "✅ Orchestrator requirements.txt found" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Orchestrator requirements.txt missing" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Quick Links" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Render Dashboard:    https://dashboard.render.com" -ForegroundColor Gray
Write-Host "Railway Dashboard:   https://railway.app/dashboard" -ForegroundColor Gray
Write-Host "Fly.io Dashboard:    https://fly.io/dashboard" -ForegroundColor Gray
Write-Host "Cloudflare Pages:    https://dash.cloudflare.com/pages" -ForegroundColor Gray
Write-Host "Cloudflare Workers:  https://dash.cloudflare.com/workers" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:       BACKEND_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host ""

Write-Host "Press any key to open Render dashboard in browser..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "https://dashboard.render.com"

Write-Host ""
Write-Host "Good luck with deployment! 🚀" -ForegroundColor Green
Write-Host ""
