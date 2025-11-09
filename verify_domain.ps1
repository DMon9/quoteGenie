# Domain Verification Script
# Run this after a few minutes to verify the domain is serving the correct page

param(
    [string]$Domain = "www.estimategenie.net",
    [int]$MaxAttempts = 10
)

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "Domain Verification Tool" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host "Attempt $i/$MaxAttempts - Checking $Domain..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "https://$Domain/" -UseBasicParsing -Headers @{
            "Cache-Control" = "no-cache, no-store, must-revalidate"
            "Pragma"        = "no-cache"
        } -TimeoutSec 10
        
        $content = $response.Content
        $titleStart = $content.IndexOf('<title>')
        $titleEnd = $content.IndexOf('</title>')
        
        if ($titleStart -ge 0 -and $titleEnd -gt $titleStart) {
            $title = $content.Substring($titleStart + 7, $titleEnd - $titleStart - 7)
            
            Write-Host "  Title: $title" -ForegroundColor White
            Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Gray
            Write-Host "  Server: $($response.Headers['Server'])" -ForegroundColor Gray
            
            if ($title -like "*Estimation Wizard*") {
                Write-Host "`n🎉 SUCCESS!" -ForegroundColor Green
                Write-Host "✓ www.estimategenie.net is serving the correct desktop page!" -ForegroundColor Green
                Write-Host "`nYou can now test the production site:" -ForegroundColor Cyan
                Write-Host "  1. Signup: https://www.estimategenie.net/signup.html" -ForegroundColor White
                Write-Host "  2. Login: https://www.estimategenie.net/login.html" -ForegroundColor White
                Write-Host "  3. Generate Quote: Upload a photo and test AI generation" -ForegroundColor White
                Write-Host ""
                exit 0
            }
            elseif ($title -like "*Mobile*") {
                Write-Host "  ⚠ Still serving mobile page..." -ForegroundColor Yellow
            }
            else {
                Write-Host "  ℹ Unexpected title" -ForegroundColor Gray
            }
        }
    }
    catch {
        Write-Host "  ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($i -lt $MaxAttempts) {
        Write-Host "  Waiting 30 seconds before retry..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
    }
}

Write-Host "`n⚠ Domain still not serving correct page after $MaxAttempts attempts" -ForegroundColor Yellow
Write-Host "`nPossible solutions:" -ForegroundColor Cyan
Write-Host "1. Wait another 5-10 minutes for full DNS propagation" -ForegroundColor White
Write-Host "2. Check Cloudflare dashboard: https://dash.cloudflare.com" -ForegroundColor White
Write-Host "3. Verify domain is active: wrangler pages deployment list --project-name=estimategenie" -ForegroundColor White
Write-Host "4. Hard refresh browser: Ctrl+Shift+R" -ForegroundColor White
Write-Host ""
