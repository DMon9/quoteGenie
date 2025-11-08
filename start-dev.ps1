# EstimateGenie Development Environment Startup Script

Write-Host "Starting EstimateGenie Development Environment..." -ForegroundColor Cyan
Write-Host ""

# Check if backend .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "Creating backend/.env from .env.example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Please edit backend/.env and set your configuration (JWT_SECRET_KEY, etc.)" -ForegroundColor Yellow
    Write-Host ""
}

# Start backend API in a new PowerShell window
Write-Host "Starting Backend API on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; ..\. venv-3\Scripts\Activate.ps1; uvicorn app:app --reload --host 0.0.0.0 --port 8000"

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start frontend server in a new PowerShell window
Write-Host "Starting Frontend on http://localhost:8080..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m http.server 8080"

Write-Host ""
Write-Host "Development environment started!" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:8080" -ForegroundColor White
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Yellow
