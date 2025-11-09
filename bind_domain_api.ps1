# Cloudflare Pages Domain Binding Script
# Requires: CLOUDFLARE_API_TOKEN environment variable

param(
    [string]$ProjectName = "estimategenie",
    [string]$Domain = "www.estimategenie.net",
    [string]$AccountId = "585ba51d553760ece834d6450c4c158f"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Cloudflare Pages Domain Binding" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check for API token
$apiToken = $env:CLOUDFLARE_API_TOKEN
if (-not $apiToken) {
    Write-Host "ERROR: No CLOUDFLARE_API_TOKEN found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Set it first:" -ForegroundColor Yellow
    Write-Host '  $env:CLOUDFLARE_API_TOKEN = "your-token"' -ForegroundColor White
    Write-Host ""
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $apiToken"
    "Content-Type"  = "application/json"
}

# Step 1: Add domain to Pages project
Write-Host "Adding domain: $Domain" -ForegroundColor Cyan
$addDomainUrl = "https://api.cloudflare.com/client/v4/accounts/$AccountId/pages/projects/$ProjectName/domains"
$domainBody = @{ name = $Domain } | ConvertTo-Json

try {
    $addResponse = Invoke-RestMethod -Uri $addDomainUrl -Method POST -Headers $headers -Body $domainBody -ErrorAction Stop
    Write-Host "  SUCCESS: Domain added!" -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 409) {
        Write-Host "  OK: Domain already exists" -ForegroundColor Yellow
    }
    else {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $details = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($details.errors) {
                Write-Host "  Details: $($details.errors[0].message)" -ForegroundColor Red
            }
        }
    }
}

# Step 2: Purge cache
$BaseDomain = if ($Domain -match "^www\.(.+)$") { $matches[1] } else { $Domain }
Write-Host ""
Write-Host "Purging cache for: $BaseDomain" -ForegroundColor Cyan

try {
    # Get zone ID
    $zonesUrl = "https://api.cloudflare.com/client/v4/zones?name=$BaseDomain"
    $zonesResponse = Invoke-RestMethod -Uri $zonesUrl -Method GET -Headers $headers -ErrorAction Stop

    if ($zonesResponse.success -and $zonesResponse.result.Count -gt 0) {
        $zoneId = $zonesResponse.result[0].id

        # Purge cache
        $purgeUrl = "https://api.cloudflare.com/client/v4/zones/$zoneId/purge_cache"
        $purgeBody = @{ purge_everything = $true } | ConvertTo-Json

        $purgeResponse = Invoke-RestMethod -Uri $purgeUrl -Method POST -Headers $headers -Body $purgeBody -ErrorAction Stop
        if ($purgeResponse.success) {
            Write-Host "  SUCCESS: Cache purged!" -ForegroundColor Green
        }
    }
    else {
        Write-Host "  WARNING: Could not find zone" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Verify
Write-Host ""
Write-Host "Verifying domain..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

try {
    $response = Invoke-WebRequest -Uri "https://$Domain" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    
    # Extract title using IndexOf/Substring to avoid regex issues
    $content = $response.Content
    $titleStart = $content.IndexOf('<title>')
    $titleEnd = $content.IndexOf('</title>')
    
    if ($titleStart -ge 0 -and $titleEnd -gt $titleStart) {
        $title = $content.Substring($titleStart + 7, $titleEnd - $titleStart - 7)
    }
    else {
        $title = "Unknown"
    }
    
    Write-Host "  SUCCESS: Domain accessible" -ForegroundColor Green
    Write-Host "  Title: $title" -ForegroundColor Gray
}
catch {
    Write-Host "  WARNING: Domain not yet accessible" -ForegroundColor Yellow
    Write-Host "  (DNS may need time to propagate)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "DONE! Test at: https://$Domain" -ForegroundColor Green
Write-Host ""
