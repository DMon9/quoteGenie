# Quick Frontend Redeploy to Cloudflare Pages
# This will commit current changes and push to git, triggering Cloudflare Pages rebuild

Write-Host "EstimateGenie Frontend Redeploy" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check git status
if (!(Test-Path ".git")) {
    Write-Host "ERROR: Not a git repository" -ForegroundColor Red
    exit 1
}

Write-Host "Current git status:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Stage all changes
Write-Host "Staging changes..." -ForegroundColor Cyan
git add -A

# Check if there are changes to commit
$status = git status --porcelain
if (-not $status) {
    Write-Host "No changes to commit" -ForegroundColor Yellow
    exit 0
}

# Commit with a message
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$commitMsg = "Frontend redeploy - Updated API configuration - $timestamp"

Write-Host "Committing changes..." -ForegroundColor Cyan
git commit -m "$commitMsg"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Commit failed" -ForegroundColor Red
    exit 1
}

# Push to git (will trigger Cloudflare Pages rebuild)
Write-Host "Pushing to git (this will trigger Cloudflare Pages rebuild)..." -ForegroundColor Cyan
git push

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Frontend redeployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The Cloudflare Pages build is now in progress." -ForegroundColor Cyan
    Write-Host "Your frontend changes will be live in 1-2 minutes." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Check deployment status:" -ForegroundColor Yellow
    Write-Host "https://dash.cloudflare.com/" -ForegroundColor White
} else {
    Write-Host "Push failed - check your git configuration" -ForegroundColor Red
    exit 1
}
