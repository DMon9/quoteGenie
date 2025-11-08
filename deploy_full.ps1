# Deploy EstimateGenie Backend and Frontend
# This script deploys the full application

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "EstimateGenie Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if we're in the right directory
if (!(Test-Path "backend") -or !(Test-Path "assets")) {
    Write-Host "Error: Please run this script from the quoteGenie root directory" -ForegroundColor Red
    exit 1
}

# Step 2: Deploy Backend to Fly.io
Write-Host "Step 1: Deploying Backend to Fly.io..." -ForegroundColor Green
Write-Host ""

Set-Location backend

Write-Host "Checking Fly.io authentication..." -ForegroundColor Yellow
fly auth whoami
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please login to Fly.io first: fly auth login" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "Deploying to Fly.io (this may take 3-5 minutes)..." -ForegroundColor Yellow
fly deploy -a quotegenie-api

if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "✓ Backend deployed successfully!" -ForegroundColor Green

# Step 3: Verify Backend
Write-Host ""
Write-Host "Step 2: Verifying Backend..." -ForegroundColor Green
Start-Sleep -Seconds 5

try {
    $health = Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/health" -Method GET
    Write-Host "✓ Backend is healthy!" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Cyan
    Write-Host "  Services: Vision=$($health.services.vision), LLM=$($health.services.llm), DB=$($health.services.database)" -ForegroundColor Cyan
    
    # Check available models
    $models = Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/api/v1/models/available" -Method GET
    Write-Host "  Available AI Models: $($models.models.Count)" -ForegroundColor Cyan
    foreach ($model in $models.models) {
        Write-Host "    - $($model.name) ($($model.id))" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "Warning: Backend verification failed. Check logs with: fly logs -a quotegenie-api" -ForegroundColor Yellow
}

Set-Location ..

# Step 4: Frontend Deployment Instructions
Write-Host ""
Write-Host "Step 3: Frontend Deployment" -ForegroundColor Green
Write-Host ""
Write-Host "Choose your deployment method:" -ForegroundColor Yellow
Write-Host "  A) Deploy to Cloudflare Pages via Git (Recommended)"
Write-Host "  B) Deploy to Cloudflare Pages via Wrangler CLI"
Write-Host "  C) Skip frontend deployment (testing only)"
Write-Host ""

$choice = Read-Host "Enter your choice (A/B/C)"

switch ($choice.ToUpper()) {
    "A" {
        Write-Host ""
        Write-Host "Git Deployment Steps:" -ForegroundColor Cyan
        Write-Host "1. Push your code to GitHub:" -ForegroundColor Yellow
        Write-Host "   git add ."
        Write-Host "   git commit -m 'Add multi-model AI support'"
        Write-Host "   git push origin main"
        Write-Host ""
        Write-Host "2. Go to Cloudflare Pages:" -ForegroundColor Yellow
        Write-Host "   https://dash.cloudflare.com/ → Pages → Create a project"
        Write-Host ""
        Write-Host "3. Connect your GitHub repository and deploy" -ForegroundColor Yellow
        Write-Host ""
        
        $git = Read-Host "Do you want to commit and push now? (Y/N)"
        if ($git.ToUpper() -eq "Y") {
            git add .
            $message = Read-Host "Enter commit message (or press Enter for default)"
            if ([string]::IsNullOrWhiteSpace($message)) {
                $message = "Add multi-model AI support and deployment updates"
            }
            git commit -m $message
            git push origin main
            Write-Host "✓ Code pushed to GitHub!" -ForegroundColor Green
        }
    }
    "B" {
        Write-Host ""
        Write-Host "Checking for Wrangler..." -ForegroundColor Yellow
        
        try {
            wrangler --version | Out-Null
            Write-Host "✓ Wrangler found" -ForegroundColor Green
        }
        catch {
            Write-Host "Wrangler not found. Installing..." -ForegroundColor Yellow
            npm install -g wrangler
        }
        
        Write-Host ""
        Write-Host "Logging in to Cloudflare..." -ForegroundColor Yellow
        wrangler login
        
        Write-Host ""
        $projectName = Read-Host "Enter Cloudflare Pages project name (default: estimategenie)"
        if ([string]::IsNullOrWhiteSpace($projectName)) {
            $projectName = "estimategenie"
        }
        
        Write-Host "Deploying to Cloudflare Pages..." -ForegroundColor Yellow
        wrangler pages deploy . --project-name=$projectName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Frontend deployed successfully!" -ForegroundColor Green
        }
        else {
            Write-Host "Frontend deployment failed. Check error messages above." -ForegroundColor Red
        }
    }
    "C" {
        Write-Host ""
        Write-Host "Skipping frontend deployment." -ForegroundColor Yellow
        Write-Host "You can test locally with: python -m http.server 8080" -ForegroundColor Cyan
    }
    default {
        Write-Host "Invalid choice. Skipping frontend deployment." -ForegroundColor Yellow
    }
}

# Step 5: Final Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend URL: https://quotegenie-api.fly.dev" -ForegroundColor Green
Write-Host "Health Check: https://quotegenie-api.fly.dev/health" -ForegroundColor Green
Write-Host "Models API: https://quotegenie-api.fly.dev/api/v1/models/available" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test the signup flow: http://localhost:8080/signup.html" -ForegroundColor Cyan
Write-Host "2. Test quote generation in the dashboard" -ForegroundColor Cyan
Write-Host "3. Check available AI models" -ForegroundColor Cyan
Write-Host "4. (Optional) Set additional API keys for GPT-4V and Claude:" -ForegroundColor Cyan
Write-Host "   fly secrets set OPENAI_API_KEY=your-key -a quotegenie-api" -ForegroundColor Gray
Write-Host "   fly secrets set ANTHROPIC_API_KEY=your-key -a quotegenie-api" -ForegroundColor Gray
Write-Host ""
Write-Host "Deployment complete! 🎉" -ForegroundColor Green
