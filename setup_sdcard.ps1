# SD Card Storage Setup for QuoteGenie Models
# This script helps configure model storage on SD card (D:)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  QuoteGenie - SD Card Storage Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if D: drive exists
if (-not (Test-Path "D:\")) {
    Write-Host "❌ ERROR: Drive D: not found!" -ForegroundColor Red
    Write-Host "   Please ensure your SD card is properly mounted." -ForegroundColor Yellow
    exit 1
}

# Get SD card info
$volume = Get-Volume -DriveLetter D
$freeSpaceGB = [math]::Round($volume.SizeRemaining / 1GB, 2)
$totalSpaceGB = [math]::Round($volume.Size / 1GB, 2)

Write-Host "✅ SD Card detected: D:\" -ForegroundColor Green
Write-Host "   Total Space: $totalSpaceGB GB" -ForegroundColor Gray
Write-Host "   Free Space:  $freeSpaceGB GB" -ForegroundColor Gray
Write-Host ""

# Check if we have enough space (recommend at least 20GB)
if ($freeSpaceGB -lt 20) {
    Write-Host "⚠️  WARNING: Low disk space!" -ForegroundColor Yellow
    Write-Host "   Recommended: 20+ GB free" -ForegroundColor Yellow
    Write-Host "   Available:   $freeSpaceGB GB" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Create models directory on SD card
$modelsPath = "D:\quoteGenie_models"
Write-Host "📂 Creating models directory: $modelsPath" -ForegroundColor Cyan

if (-not (Test-Path $modelsPath)) {
    New-Item -ItemType Directory -Path $modelsPath -Force | Out-Null
    Write-Host "✅ Directory created successfully" -ForegroundColor Green
}
else {
    Write-Host "✅ Directory already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variable for current session
$env:MODELS_DIR = $modelsPath
Write-Host "✅ Environment variable set for current session:" -ForegroundColor Green
Write-Host "   `$env:MODELS_DIR = `"$modelsPath`"" -ForegroundColor Gray
Write-Host ""

# Create .env file if it doesn't exist
$envFile = ".env"
$envContent = ""
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
}

if ($envContent -notmatch "MODELS_DIR") {
    Write-Host "📝 Adding MODELS_DIR to .env file..." -ForegroundColor Cyan
    Add-Content -Path $envFile -Value "`nMODELS_DIR=$modelsPath"
    Write-Host "✅ Added to .env file" -ForegroundColor Green
}
else {
    Write-Host "✅ MODELS_DIR already in .env file" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Download models to SD card:" -ForegroundColor White
Write-Host "   python download_models.py --model mistral" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run with Docker Compose:" -ForegroundColor White
Write-Host "   docker-compose --profile models up mistral" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Models will be stored in:" -ForegroundColor White
Write-Host "   $modelsPath" -ForegroundColor Gray
Write-Host ""
Write-Host "TIP: To always use SD card storage, add to your PowerShell profile:" -ForegroundColor Yellow
Write-Host "   `$env:MODELS_DIR = `"$modelsPath`"" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Storage Estimates" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Model Sizes (approximate):" -ForegroundColor White
Write-Host "  • mistral    ~14 GB" -ForegroundColor Gray
Write-Host "  • qwen2      ~15 GB" -ForegroundColor Gray
Write-Host "  • moondream2 ~4 GB" -ForegroundColor Gray
Write-Host "  • llama3     ~16 GB (requires auth)" -ForegroundColor Gray
Write-Host "  • deepseek   ~13 GB" -ForegroundColor Gray
Write-Host "  • granite    ~16 GB" -ForegroundColor Gray
Write-Host "  • phi4       ~28 GB" -ForegroundColor Gray
Write-Host ""
Write-Host "With $freeSpaceGB GB free, you can store:" -ForegroundColor White
$numModels = [math]::Floor($freeSpaceGB / 15)
Write-Host "  Approximately $numModels medium-sized models" -ForegroundColor Gray
Write-Host ""
Write-Host "Setup complete! SD card storage is ready." -ForegroundColor Green
Write-Host ""
