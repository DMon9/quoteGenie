# Switch to Minimalist Landing Page
# Run this from the quoteGenie root directory

Write-Host "======================================"
Write-Host "EstimateGenie - Switch to Minimalist Design"
Write-Host "======================================"
Write-Host ""

# Check if we're in the right directory
if (!(Test-Path "index.html")) {
    Write-Host "Error: index.html not found. Please run from quoteGenie root directory." -ForegroundColor Red
    exit 1
}

# Backup current index.html
Write-Host "1. Backing up current landing page..." -ForegroundColor Cyan
Copy-Item -Path "index.html" -Destination "index-original-backup.html" -Force
Write-Host "   ✓ Backed up to index-original-backup.html" -ForegroundColor Green

# Copy minimalist version to index.html
Write-Host ""
Write-Host "2. Switching to minimalist design..." -ForegroundColor Cyan
Copy-Item -Path "index-minimalist.html" -Destination "index.html" -Force
Write-Host "   ✓ Minimalist design is now active!" -ForegroundColor Green

Write-Host ""
Write-Host "======================================"
Write-Host "Success! Landing page updated" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Test locally:" -ForegroundColor White
Write-Host "   - Open index.html in your browser" -ForegroundColor Gray
Write-Host "   - Try the quote builder demo" -ForegroundColor Gray
Write-Host "   - Test on mobile (browser DevTools)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Deploy to production:" -ForegroundColor White
Write-Host "   - Run: .\deploy.ps1" -ForegroundColor Gray
Write-Host "   - Or: wrangler pages deploy . --project-name estimategenie" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Revert if needed:" -ForegroundColor White
Write-Host "   - Run: Copy-Item index-original-backup.html index.html -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation: See MINIMALIST_DESIGN.md for details" -ForegroundColor Cyan
