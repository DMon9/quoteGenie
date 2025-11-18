# Activate Premium Dark Theme Landing Page
# Run from project root directory

Write-Host "🎨 EstimateGenie - Activate Premium Dark Theme"
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verify we're in the right place
if (!(Test-Path "index.html")) {
    Write-Host "❌ Error: index.html not found" -ForegroundColor Red
    Write-Host "Please run from the EstimateGenie root directory" -ForegroundColor Red
    exit 1
}

# Backup current version
Write-Host "1️⃣  Backing up current landing page..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
Copy-Item "index.html" "index-backup-$timestamp.html" -Force
Write-Host "   ✓ Saved as: index-backup-$timestamp.html" -ForegroundColor Green
Write-Host ""

# Activate premium theme
Write-Host "2️⃣  Activating premium dark theme..." -ForegroundColor Yellow
Copy-Item "index-premium.html" "index.html" -Force
Write-Host "   ✓ Premium design is now LIVE!" -ForegroundColor Green
Write-Host ""

Write-Host "================================================"
Write-Host "✅ Premium Dark Theme Activated!" -ForegroundColor Green
Write-Host "================================================"
Write-Host ""

Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test locally:" -ForegroundColor White
Write-Host "   • Open index.html in your browser" -ForegroundColor Gray
Write-Host "   • Test on desktop, tablet, and mobile" -ForegroundColor Gray
Write-Host "   • Check all buttons and interactions" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Deploy to production:" -ForegroundColor White
Write-Host "   • Run: wrangler pages deploy . --project-name estimategenie" -ForegroundColor Gray
Write-Host "   • Or run: .\deploy.ps1 for full deployment" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Revert if needed:" -ForegroundColor White
Write-Host "   • Run: Copy-Item index-backup-*.html index.html -Force" -ForegroundColor Gray
Write-Host ""

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • See PREMIUM_DESIGN.md for full details" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 Your premium landing page is ready!" -ForegroundColor Green
