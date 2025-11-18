# Quick Deploy Commands for EstimateGenie
# Copy and paste these commands based on your platform

Write-Host "======================================"
Write-Host "EstimateGenie Quick Deploy Commands"
Write-Host "======================================"
Write-Host ""

Write-Host "BACKEND DEPLOYMENT (Fly.io):" -ForegroundColor Cyan
Write-Host "------------------------------"
Write-Host ""
Write-Host "cd backend" -ForegroundColor Yellow
Write-Host "fly deploy --config fly.toml --app quotegenie-api --remote-only" -ForegroundColor Yellow
Write-Host "fly status -a quotegenie-api" -ForegroundColor Yellow
Write-Host "cd .." -ForegroundColor Yellow
Write-Host ""

Write-Host "FRONTEND DEPLOYMENT (Cloudflare Pages):" -ForegroundColor Cyan
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "wrangler pages deploy . --project-name estimategenie --branch main --commit-dirty=true" -ForegroundColor Yellow
Write-Host ""

Write-Host "VERIFICATION:" -ForegroundColor Cyan
Write-Host "-------------"
Write-Host ""
Write-Host "# Test backend health" -ForegroundColor Green
Write-Host "curl https://quotegenie-api.fly.dev/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Test demo quote" -ForegroundColor Green
Write-Host 'curl -X POST https://quotegenie-api.fly.dev/v1/quotes/demo -H "Content-Type: application/json" -d "{\"project_type\":\"kitchen\"}"' -ForegroundColor Yellow
Write-Host ""
Write-Host "# Visit frontend" -ForegroundColor Green
Write-Host "https://estimategenie.pages.dev" -ForegroundColor Yellow
Write-Host ""

Write-Host "======================================"
Write-Host ""
Write-Host "Choose your deployment method:" -ForegroundColor White
Write-Host ""
Write-Host "1. Run automated script:   .\deploy.ps1" -ForegroundColor Green
Write-Host "2. Copy commands above manually" -ForegroundColor Green
Write-Host "3. Deploy individually (backend first, then frontend)" -ForegroundColor Green
Write-Host ""

$choice = Read-Host "Enter choice (1-3) or press Enter to exit"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running automated deployment..." -ForegroundColor Cyan
        .\deploy.ps1
    }
    "2" {
        Write-Host ""
        Write-Host "Manual deployment selected. Copy the commands above." -ForegroundColor Yellow
    }
    "3" {
        Write-Host ""
        Write-Host "Individual deployment selected." -ForegroundColor Yellow
        Write-Host ""
        $deployChoice = Read-Host "Deploy backend now? (y/n)"
        if ($deployChoice -eq "y") {
            Push-Location backend
            fly deploy --config fly.toml --app quotegenie-api --remote-only
            Pop-Location
            Write-Host ""
            Write-Host "Backend deployed!" -ForegroundColor Green
            Write-Host ""
        }
        
        $deployFrontend = Read-Host "Deploy frontend now? (y/n)"
        if ($deployFrontend -eq "y") {
            wrangler pages deploy . --project-name estimategenie --branch main --commit-dirty=true
            Write-Host ""
            Write-Host "Frontend deployed!" -ForegroundColor Green
        }
    }
    default {
        Write-Host "Exiting. See DEPLOY_NOW.md for full instructions." -ForegroundColor Gray
    }
}
