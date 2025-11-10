# Fix Custom Domain Routing for Cloudflare Pages
# This script ensures proper routing for the custom domain estimategenie.net

param(
    [string]$ProjectName = "estimategenie",
    [switch]$Force
)

Write-Host "`n=== Cloudflare Pages Custom Domain Routing Fix ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Yellow
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

# Check if wrangler is installed
Write-Host "[1/6] Checking Wrangler CLI..." -ForegroundColor Cyan
$wranglerVersion = wrangler --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Wrangler CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "Run: npm install -g wrangler" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Wrangler installed: $wranglerVersion" -ForegroundColor Green

# Verify configuration files exist
Write-Host "`n[2/6] Verifying configuration files..." -ForegroundColor Cyan
$configFiles = @(
    "_redirects",
    "_headers",
    "wrangler.toml",
    "404.html"
)

$missingFiles = @()
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file missing" -ForegroundColor Red
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "`n❌ Missing configuration files. Please ensure all files are created." -ForegroundColor Red
    exit 1
}

# Deploy to Cloudflare Pages
Write-Host "`n[3/6] Deploying to Cloudflare Pages..." -ForegroundColor Cyan
Write-Host "Running deployment with updated routing configuration..." -ForegroundColor Gray

$deployCmd = if ($Force) {
    "wrangler pages deploy . --project-name=$ProjectName --commit-dirty=true"
} else {
    "wrangler pages deploy . --project-name=$ProjectName"
}

Write-Host "Command: $deployCmd" -ForegroundColor Gray
Invoke-Expression $deployCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Deployment successful!" -ForegroundColor Green

# Get deployment info
Write-Host "`n[4/6] Getting deployment information..." -ForegroundColor Cyan
$deploymentInfo = wrangler pages deployment list --project-name=$ProjectName 2>&1 | Select-Object -First 10
Write-Host $deploymentInfo -ForegroundColor Gray

# Check custom domain configuration
Write-Host "`n[5/6] Checking custom domain configuration..." -ForegroundColor Cyan
Write-Host "Listing custom domains for project..." -ForegroundColor Gray

# Note: This command may require Cloudflare API token
try {
    $domains = wrangler pages project list 2>&1 | Select-String -Pattern $ProjectName
    Write-Host $domains -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Could not automatically fetch domain info. Please check manually in Cloudflare dashboard." -ForegroundColor Yellow
}

# Provide manual verification steps
Write-Host "`n[6/6] Verification Steps" -ForegroundColor Cyan
Write-Host @"
Please verify the following in your Cloudflare Dashboard:

1. Navigate to: https://dash.cloudflare.com/
2. Go to: Workers & Pages > estimategenie > Settings > Domains & Custom Domains
3. Ensure 'estimategenie.net' and 'www.estimategenie.net' are listed
4. Check DNS records in your domain registrar:
   - Type: CNAME
   - Name: @ (or estimategenie.net)
   - Target: estimategenie.pages.dev
   - Type: CNAME
   - Name: www
   - Target: estimategenie.pages.dev

5. Test the deployment URLs:
   - Latest deployment: Check output above
   - Custom domain: https://estimategenie.net/pricing.html
   - Verify each page serves unique content (not all showing homepage)

6. If pages still show homepage content:
   - Clear Cloudflare cache: Cloudflare Dashboard > Caching > Purge Everything
   - Wait 2-5 minutes for propagation
   - Test again in incognito/private browsing mode

"@ -ForegroundColor Yellow

# Test URLs
Write-Host "`n🧪 Testing deployment URLs..." -ForegroundColor Cyan
$testUrls = @(
    "https://estimategenie.pages.dev/",
    "https://estimategenie.pages.dev/pricing.html",
    "https://estimategenie.pages.dev/login.html"
)

Write-Host "Test these URLs to verify different content is served:" -ForegroundColor Gray
foreach ($url in $testUrls) {
    Write-Host "  - $url" -ForegroundColor White
}

Write-Host "`n✅ Routing fix deployment complete!" -ForegroundColor Green
Write-Host @"

Next Steps:
1. Wait 2-5 minutes for CDN propagation
2. Test custom domain: https://estimategenie.net
3. If issues persist, purge Cloudflare cache
4. Verify DNS settings in domain registrar
5. Check custom domain is added in Cloudflare Pages settings

"@ -ForegroundColor Cyan

Write-Host "Documentation: https://developers.cloudflare.com/pages/configuration/serving-pages/" -ForegroundColor Gray
Write-Host "`n=== Fix Complete ===" -ForegroundColor Cyan
