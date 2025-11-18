# EstimateGenie Full Deployment Script for Windows
# Deploys both backend (Fly.io) and frontend (Cloudflare Pages)

$ErrorActionPreference = "Continue"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "EstimateGenie Deployment" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check git status
Write-Host "Checking git status..." -ForegroundColor Cyan
if (Test-Path ".git") {
    git status --short
    Write-Host ""
    $commitChoice = Read-Host "Commit changes before deploying? (y/n)"
    if ($commitChoice -eq "y") {
        git add .
        $commitMsg = Read-Host "Enter commit message"
        git commit -m "$commitMsg" 2>&1 | Out-Null
        git push 2>&1 | Out-Null
        Write-Host "Changes committed and pushed" -ForegroundColor Green
    }
} else {
    Write-Host "Not a git repository" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 1: Deploy Backend to Fly.io" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
Push-Location backend

# Check if fly CLI is installed
if (!(Get-Command fly -ErrorAction SilentlyContinue)) {
    Write-Host "Fly CLI not found. Please install it from https://fly.io/docs/hands-on/install-flyctl/" -ForegroundColor Red
    Write-Host "Or run: iwr https://fly.io/install.ps1 -useb | iex" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to fly
Write-Host "Checking Fly.io authentication..." -ForegroundColor Cyan
try {
    fly auth whoami | Out-Null
} catch {
    Write-Host "Please login to Fly.io:" -ForegroundColor Yellow
    fly auth login
}

# Deploy backend
Write-Host "Deploying backend..." -ForegroundColor Green
fly deploy --config fly.toml --app quotegenie-api --remote-only

# Check deployment status
Write-Host "Checking backend health..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
try {
    $health = Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/health" -TimeoutSec 10
    Write-Host "Health check:" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "Health check failed (backend may still be starting)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Backend deployed successfully!" -ForegroundColor Green
Write-Host "URL: https://quotegenie-api.fly.dev" -ForegroundColor Cyan

# Return to root
Pop-Location

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Step 2: Deploy Frontend to Cloudflare Pages" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if wrangler is installed
if (!(Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Host "Wrangler not found. Installing..." -ForegroundColor Yellow
    npm install -g wrangler
}

# Check if logged in to Cloudflare
Write-Host "Checking Cloudflare authentication..." -ForegroundColor Cyan
try {
    wrangler whoami | Out-Null
} catch {
    Write-Host "Please login to Cloudflare:" -ForegroundColor Yellow
    wrangler login
}

# Deploy to Cloudflare Pages
Write-Host "Deploying frontend to Cloudflare Pages..." -ForegroundColor Green
wrangler pages deploy . --project-name estimategenie --branch main --commit-dirty=true

Write-Host ""
Write-Host "Frontend deployed successfully!" -ForegroundColor Green
Write-Host "Production URL: https://estimategenie.pages.dev" -ForegroundColor Cyan
Write-Host ""

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Backend:  https://quotegenie-api.fly.dev" -ForegroundColor Green
Write-Host "✓ Frontend: https://estimategenie.pages.dev" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the API: curl https://quotegenie-api.fly.dev/health"
Write-Host "2. Visit the site: https://estimategenie.pages.dev"
Write-Host "3. Check Cloudflare Pages dashboard for custom domain setup"
Write-Host "4. Monitor Fly.io dashboard for backend logs and metrics"
Write-Host ""
Write-Host "Deployment complete! 🚀" -ForegroundColor Green
