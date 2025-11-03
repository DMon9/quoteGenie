# Quick Start Script for Local Testing
# Run this from the backend directory

Write-Host "EstimateGenie Backend - Quick Start" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    
    # Copy template
    Copy-Item ".env.template" ".env"
    
    Write-Host "`n⚠️  IMPORTANT: Edit .env file and add your keys:" -ForegroundColor Red
    Write-Host "   1. Generate JWT_SECRET_KEY: openssl rand -hex 32" -ForegroundColor Yellow
    Write-Host "   2. Add your STRIPE_SECRET_KEY from Stripe Dashboard" -ForegroundColor Yellow
    Write-Host "   3. Add your GOOGLE_API_KEY for Gemini" -ForegroundColor Yellow
    Write-Host "   4. Configure Stripe Price IDs" -ForegroundColor Yellow
    Write-Host "   5. Add STRIPE_WEBHOOK_SECRET from Stripe webhook setup`n" -ForegroundColor Yellow
    
    # Open .env in default editor
    Start-Process ".env"
    
    Write-Host "Press any key after configuring .env file..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if database exists
if (-not (Test-Path "estimategenie.db")) {
    Write-Host "`nDatabase will be created on first run..." -ForegroundColor Green
}

# Display instructions
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "`nTo start the server:" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor White
Write-Host "`nOr with auto-reload:" -ForegroundColor Yellow
Write-Host "  uvicorn app:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "`nAPI will be available at:" -ForegroundColor Yellow
Write-Host "  - Local: http://localhost:8000" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor White
Write-Host "`nTest authentication:" -ForegroundColor Yellow
Write-Host '  Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/register" -ContentType "application/json" -Body ''{"email":"test@example.com","name":"Test User","password":"Test123!","plan":"free"}''' -ForegroundColor White
Write-Host "`n"
