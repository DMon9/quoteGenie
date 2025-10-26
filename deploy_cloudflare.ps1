# Quick deployment script for Cloudflare
# Run from project root

$ErrorActionPreference = "Continue"

Write-Host "EstimateGenie Cloudflare Deployment" -ForegroundColor Cyan
Write-Host ""

# Check if wrangler is installed
if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Host "Wrangler CLI not found. Installing..." -ForegroundColor Red
    npm install -g wrangler
}

# Login check
Write-Host "Checking Cloudflare authentication..." -ForegroundColor Yellow
try {
    $null = wrangler whoami 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Please login to Cloudflare:" -ForegroundColor Yellow
        wrangler login
    }
}
catch {
    Write-Host "Please login to Cloudflare:" -ForegroundColor Yellow
    wrangler login
}

Write-Host ""
Write-Host "Step 1: Deploy Frontend to Cloudflare Pages" -ForegroundColor Green
Write-Host "Choose deployment method:"
Write-Host "  1. Deploy via Wrangler CLI (Quick)"
Write-Host "  2. Setup GitHub deployment (Recommended)"
Write-Host "  3. Skip frontend deployment"
$choice = Read-Host "Enter choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "Deploying frontend via Wrangler..." -ForegroundColor Yellow
        $projectName = Read-Host "Enter project name (default: estimategenie)"
        if ([string]::IsNullOrWhiteSpace($projectName)) { $projectName = "estimategenie" }
        
        try {
            wrangler pages deploy . --project-name $projectName
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Frontend deployed successfully!" -ForegroundColor Green
                Write-Host "URL: https://$projectName.pages.dev" -ForegroundColor Cyan
            }
            else {
                Write-Host "Frontend deployment failed" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Error deploying frontend: $_" -ForegroundColor Red
        }
    }
    "2" {
        Write-Host ""
        Write-Host "GitHub Deployment Setup:" -ForegroundColor Yellow
        Write-Host "1. Push your code to GitHub"
        Write-Host "2. Go to https://dash.cloudflare.com"
        Write-Host "3. Pages -> Create a project -> Connect to GitHub"
        Write-Host "4. Select your repo and configure:"
        Write-Host "   - Framework: None"
        Write-Host "   - Build command: (empty)"
        Write-Host "   - Build output: /"
        Write-Host ""
        Read-Host "Press Enter when done"
    }
    "3" {
        Write-Host "Skipping frontend deployment" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Step 2: Deploy API Worker" -ForegroundColor Green
Write-Host "First, we need your backend URL..."
$backendUrl = Read-Host "Enter backend URL (e.g., https://estimategenie-api.onrender.com)"

if (-not [string]::IsNullOrWhiteSpace($backendUrl)) {
    # Update worker configuration
    $workerPath = ".\api-worker\index.js"
    if (Test-Path $workerPath) {
        try {
            $content = Get-Content $workerPath -Raw
            $content = $content -replace "const BACKEND_URL = '[^']*'", "const BACKEND_URL = '$backendUrl'"
            Set-Content $workerPath $content
            
            Write-Host "Updated worker with backend URL: $backendUrl" -ForegroundColor Yellow
            
            # Deploy worker
            Push-Location api-worker
            Write-Host "Deploying Cloudflare Worker..." -ForegroundColor Yellow
            wrangler deploy
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "API Worker deployed successfully!" -ForegroundColor Green
            }
            else {
                Write-Host "Worker deployment failed" -ForegroundColor Red
            }
            Pop-Location
        }
        catch {
            Write-Host "Error deploying worker: $_" -ForegroundColor Red
            Pop-Location
        }
    }
    else {
        Write-Host "Worker file not found at $workerPath" -ForegroundColor Red
    }
}
else {
    Write-Host "Skipping worker deployment - backend URL required" -ForegroundColor Yellow
    Write-Host "Deploy backend first, then run this script again" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Deploy Backend:" -ForegroundColor White
Write-Host "   Choose: Render (https://render.com) OR Railway (https://railway.app) OR Fly.io" -ForegroundColor Gray
Write-Host "   See DEPLOY_CLOUDFLARE.md for detailed instructions" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Update Frontend API URL:" -ForegroundColor White
Write-Host "   Edit test-upload-v2.html and other pages" -ForegroundColor Gray
Write-Host "   Change API_BASE to your worker URL" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test Deployment:" -ForegroundColor White
Write-Host "   curl https://your-worker.workers.dev/api/health" -ForegroundColor Gray
Write-Host "   Open https://your-project.pages.dev" -ForegroundColor Gray
Write-Host ""
Write-Host "Deployment script complete!" -ForegroundColor Green
