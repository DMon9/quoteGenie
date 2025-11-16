#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick script to bind Cloudflare Pages domain using API token
.DESCRIPTION
    Sets up custom domain binding and cache purging for Cloudflare Pages.
    Requires CLOUDFLARE_API_TOKEN environment variable.
.EXAMPLE
    # Set your API token first (get from https://dash.cloudflare.com/profile/api-tokens)
    $env:CLOUDFLARE_API_TOKEN = "your-token-here"
    .\bind_domain_quick.ps1
#>

param(
    [string]$ProjectName = "estimategenie",
    [string]$Domain = "www.estimategenie.net",
    [string]$AccountId = "585ba51d553760ece834d6450c4c158f"
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔧 Cloudflare Pages Domain Binding" -ForegroundColor Cyan
Write-Host "=" * 60

# Check for API token
$apiToken = $env:CLOUDFLARE_API_TOKEN
if (-not $apiToken) {
    $apiToken = $env:CF_API_TOKEN
}

if (-not $apiToken) {
    Write-Host "`n❌ No Cloudflare API token found!" -ForegroundColor Red
    Write-Host "`nQuick setup:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://dash.cloudflare.com/profile/api-tokens" -ForegroundColor White
    Write-Host "2. Click 'Create Token' → 'Edit Cloudflare Workers' template" -ForegroundColor White
    Write-Host "3. Add these permissions:" -ForegroundColor White
    Write-Host "   - Account:Cloudflare Pages:Edit" -ForegroundColor White
    Write-Host "   - Zone:DNS:Edit" -ForegroundColor White
    Write-Host "   - Zone:Cache Purge:Purge" -ForegroundColor White
    Write-Host "4. Copy the token and run:" -ForegroundColor White
    Write-Host "   `$env:CLOUDFLARE_API_TOKEN = 'YOUR_TOKEN_HERE'" -ForegroundColor Cyan
    Write-Host "   .\bind_domain_quick.ps1" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $apiToken"
    "Content-Type"  = "application/json"
}

# Step 1: Add domain to Pages project
Write-Host "`n📌 Adding domain: $Domain" -ForegroundColor Cyan
$addDomainUrl = "https://api.cloudflare.com/client/v4/accounts/$AccountId/pages/projects/$ProjectName/domains"
$domainBody = @{ name = $Domain } | ConvertTo-Json

try {
    $addResponse = Invoke-RestMethod -Uri $addDomainUrl -Method POST -Headers $headers -Body $domainBody
    if ($addResponse.success) {
        Write-Host "✓ Domain added successfully!" -ForegroundColor Green
    }
}
catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 409) {
        Write-Host "⚠️  Domain already exists (OK)" -ForegroundColor Yellow
    }
    else {
        Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $details = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "  $($details.errors[0].message)" -ForegroundColor Red
        }
    }
}

# Step 2: Get zone ID and purge cache
$BaseDomain = if ($Domain -match "^www\.(.+)$") { $matches[1] } else { $Domain }
Write-Host "`n🔄 Purging cache for: $BaseDomain" -ForegroundColor Cyan

try {
    # Get zone ID
    $zonesUrl = "https://api.cloudflare.com/client/v4/zones?name=$BaseDomain"
    $zonesResponse = Invoke-RestMethod -Uri $zonesUrl -Method GET -Headers $headers
    
    if ($zonesResponse.success -and $zonesResponse.result.Count -gt 0) {
        $zoneId = $zonesResponse.result[0].id
        
        # Purge cache
        $purgeUrl = "https://api.cloudflare.com/client/v4/zones/$zoneId/purge_cache"
        $purgeBody = @{ purge_everything = $true } | ConvertTo-Json
        
        $purgeResponse = Invoke-RestMethod -Uri $purgeUrl -Method POST -Headers $headers -Body $purgeBody
        if ($purgeResponse.success) {
            Write-Host "✓ Cache purged!" -ForegroundColor Green
        }
    }
}
catch {
    Write-Host "✗ Cache purge failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Verify
Write-Host "`n🔍 Verifying domain..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

try {
    $response = Invoke-WebRequest -Uri "https://$Domain" -UseBasicParsing -TimeoutSec 10
    $pattern = [regex]'<title>(.*?)</title>'
    $titleMatch = $pattern.Match($response.Content)
    if ($titleMatch.Success) {
        $title = $titleMatch.Groups[1].Value
    }
    else {
        $title = "Unknown"
    }
    Write-Host "✓ Domain accessible" -ForegroundColor Green
    Write-Host "  Title: $title" -ForegroundColor Gray
}
catch {
    Write-Host "⚠️  Domain not yet accessible (may need DNS propagation)" -ForegroundColor Yellow
}

Write-Host "`n✅ Done! Test at: https://$Domain" -ForegroundColor Green
Write-Host ""
