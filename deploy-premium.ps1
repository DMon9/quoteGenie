# Deploy Premium Landing Page and Site
# Run from EstimateGenie root directory

Write-Host "🚀 EstimateGenie - Deploying Premium Site" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy premium theme to index.html
Write-Host "1️⃣  Activating premium landing page..." -ForegroundColor Yellow
Copy-Item "index-premium.html" "index.html" -Force
Write-Host "   ✅ index.html updated with premium design" -ForegroundColor Green
Write-Host ""

# Step 2: Deploy to Cloudflare Pages
Write-Host "2️⃣  Deploying to Cloudflare Pages..." -ForegroundColor Yellow
wrangler pages deploy . --project-name estimategenie --branch main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✅ Deployment Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Your site is live at:" -ForegroundColor Cyan
    Write-Host "   https://estimategenie.pages.dev" -ForegroundColor White
    Write-Host "   https://estimategenie.net (if domain configured)" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 What was deployed:" -ForegroundColor Cyan
    Write-Host "   • Premium dark theme landing page" -ForegroundColor White
    Write-Host "   • Updated pricing page" -ForegroundColor White
    Write-Host "   • Updated features page" -ForegroundColor White
    Write-Host "   • All documentation" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 Your professional site is now live!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed. Please check the error above." -ForegroundColor Red
    exit 1
}
