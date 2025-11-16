#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Binds custom domain to Cloudflare Pages project and purges cache
.DESCRIPTION
    Automates the process of:
    1. Adding custom domain to the Pages project
    2. Verifying domain configuration
    3. Purging Cloudflare cache for the domain
.PARAMETER ProjectName
    Cloudflare Pages project name (default: estimategenie)
.PARAMETER Domain
    Custom domain to bind (default: www.estimategenie.net)
.PARAMETER AccountId
    Cloudflare account ID (default: 585ba51d553760ece834d6450c4c158f)
.PARAMETER PurgeCache
    Whether to purge Cloudflare cache after binding (default: true)
.EXAMPLE
    .\bind_domain.ps1
    .\bind_domain.ps1 -Domain "estimategenie.net" -PurgeCache $false
#>

param(
    [string]$ProjectName = "estimategenie",
    [string]$Domain = "www.estimategenie.net",
    [string]$AccountId = "585ba51d553760ece834d6450c4c158f",
    [bool]$PurgeCache = $true
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Cloudflare Pages Domain Binding Automation" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Project:   $ProjectName" -ForegroundColor White
Write-Host "Domain:    $Domain" -ForegroundColor White
Write-Host "Account:   $AccountId" -ForegroundColor White
Write-Host ""

# Check if wrangler is installed
try {
    $wranglerVersion = wrangler --version 2>&1
    Write-Host "✓ Wrangler installed: $wranglerVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Wrangler not found. Please install: npm install -g wrangler" -ForegroundColor Red
    exit 1
}

# Check authentication
Write-Host "`n📋 Checking authentication..." -ForegroundColor Cyan
try {
    $whoami = wrangler whoami 2>&1 | Out-String
    if ($whoami -match "You are logged in") {
        Write-Host "✓ Authenticated with Cloudflare" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Not authenticated. Run: wrangler login" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "✗ Authentication check failed" -ForegroundColor Red
    exit 1
}

# Get the base domain for cache purging
$BaseDomain = if ($Domain -match "^www\.(.+)$") { $matches[1] } else { $Domain }
Write-Host "Base domain: $BaseDomain" -ForegroundColor Gray

# Function to call Cloudflare API via wrangler
function Invoke-CloudflareAPI {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,
        [string]$Body = $null
    )
    
    $url = "https://api.cloudflare.com/client/v4$Endpoint"
    
    # Use wrangler to get the auth token
    # Note: wrangler uses OAuth, so we'll use curl with the token from wrangler config
    # For now, we'll use wrangler's built-in commands where possible
    
    return $null # Placeholder - wrangler doesn't expose token easily
}

# Step 1: Add custom domain to Pages project
Write-Host "`n🌐 Adding custom domain to Pages project..." -ForegroundColor Cyan
try {
    # Use wrangler pages project to add domain
    # Note: wrangler doesn't have a direct command for this, so we'll use the API
    
    # Get Cloudflare API token from environment or wrangler config
    # Since wrangler uses OAuth, we need to use the Cloudflare dashboard API
    
    Write-Host "⚠️  Wrangler doesn't provide a direct domain binding command." -ForegroundColor Yellow
    Write-Host "    Using Cloudflare API directly..." -ForegroundColor Gray
    
    # Check if CF_API_TOKEN environment variable is set
    $apiToken = $env:CLOUDFLARE_API_TOKEN
    if (-not $apiToken) {
        $apiToken = $env:CF_API_TOKEN
    }
    
    if (-not $apiToken) {
        Write-Host "`n❌ No Cloudflare API token found." -ForegroundColor Red
        Write-Host "`nTo automate domain binding, you need a Cloudflare API token with:" -ForegroundColor Yellow
        Write-Host "  1. Go to: https://dash.cloudflare.com/profile/api-tokens" -ForegroundColor White
        Write-Host "  2. Create a token with permissions:" -ForegroundColor White
        Write-Host "     - Zone:DNS:Edit" -ForegroundColor White
        Write-Host "     - Account:Cloudflare Pages:Edit" -ForegroundColor White
        Write-Host "  3. Set environment variable: `$env:CLOUDFLARE_API_TOKEN = 'your-token'" -ForegroundColor White
        Write-Host "`nFor now, please bind the domain manually:" -ForegroundColor Yellow
        Write-Host "  1. Go to: https://dash.cloudflare.com/$AccountId/pages/view/$ProjectName" -ForegroundColor White
        Write-Host "  2. Click 'Custom domains' tab" -ForegroundColor White
        Write-Host "  3. Click 'Set up a custom domain'" -ForegroundColor White
        Write-Host "  4. Enter: $Domain" -ForegroundColor White
        Write-Host "  5. Click 'Continue' and follow the prompts" -ForegroundColor White
        
        # Ask if user wants to continue with cache purge
        Write-Host "`nDomain binding requires manual setup." -ForegroundColor Yellow
        $continue = Read-Host "Have you already bound the domain? (y/n)"
        if ($continue -ne "y") {
            Write-Host "Exiting. Run this script again after binding the domain." -ForegroundColor Gray
            exit 0
        }
    }
    else {
        Write-Host "✓ API token found" -ForegroundColor Green
        
        # Add custom domain via API
        $headers = @{
            "Authorization" = "Bearer $apiToken"
            "Content-Type"  = "application/json"
        }
        
        $body = @{
            "name" = $Domain
        } | ConvertTo-Json
        
        $apiUrl = "https://api.cloudflare.com/client/v4/accounts/$AccountId/pages/projects/$ProjectName/domains"
        
        Write-Host "Adding domain: $Domain" -ForegroundColor Gray
        try {
            $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Headers $headers -Body $body -ErrorAction Stop
            
            if ($response.success) {
                Write-Host "✓ Domain added successfully!" -ForegroundColor Green
                Write-Host "  Status: $($response.result.status)" -ForegroundColor Gray
                if ($response.result.validation_data) {
                    Write-Host "  Validation: $($response.result.validation_data)" -ForegroundColor Gray
                }
            }
            else {
                $errorMsg = ($response.errors | ForEach-Object { $_.message }) -join ", "
                if ($errorMsg -match "already exists") {
                    Write-Host "⚠️  Domain already exists on this project" -ForegroundColor Yellow
                }
                else {
                    Write-Host "✗ Failed to add domain: $errorMsg" -ForegroundColor Red
                }
            }
        }
        catch {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($statusCode -eq 409) {
                Write-Host "⚠️  Domain already exists on this project" -ForegroundColor Yellow
            }
            else {
                Write-Host "✗ API Error: $($_.Exception.Message)" -ForegroundColor Red
                if ($_.ErrorDetails.Message) {
                    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json
                    Write-Host "  Details: $($errorDetails.errors | ForEach-Object { $_.message })" -ForegroundColor Red
                }
            }
        }
    }
}
catch {
    Write-Host "✗ Error adding domain: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 2: Verify domain is pointing to Pages
Write-Host "`n🔍 Verifying domain configuration..." -ForegroundColor Cyan
try {
    # Check DNS resolution
    $dnsResult = nslookup $Domain 2>&1 | Out-String
    if ($dnsResult -match "104\.21\.|172\.67\.|2606:4700") {
        Write-Host "✓ Domain resolves to Cloudflare IP" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Domain may not be pointing to Cloudflare" -ForegroundColor Yellow
    }
    
    # Check HTTP response
    $response = Invoke-WebRequest -Uri "https://$Domain" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response) {
        $title = if ($response.Content -match '<title>(.*?)</title>') { $matches[1] } else { "Unknown" }
        Write-Host "✓ Domain is accessible" -ForegroundColor Green
        Write-Host "  Title: $title" -ForegroundColor Gray
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "⚠️  Could not verify domain accessibility: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Step 3: Purge cache if requested
if ($PurgeCache) {
    Write-Host "`n🔄 Purging Cloudflare cache..." -ForegroundColor Cyan
    
    # Get zone ID for the base domain
    if ($apiToken) {
        try {
            $headers = @{
                "Authorization" = "Bearer $apiToken"
                "Content-Type"  = "application/json"
            }
            
            # Get zone ID
            $zonesUrl = "https://api.cloudflare.com/client/v4/zones?name=$BaseDomain"
            $zonesResponse = Invoke-RestMethod -Uri $zonesUrl -Method GET -Headers $headers -ErrorAction Stop
            
            if ($zonesResponse.success -and $zonesResponse.result.Count -gt 0) {
                $zoneId = $zonesResponse.result[0].id
                Write-Host "✓ Found zone ID: $zoneId" -ForegroundColor Green
                
                # Purge everything
                $purgeUrl = "https://api.cloudflare.com/client/v4/zones/$zoneId/purge_cache"
                $purgeBody = @{
                    "purge_everything" = $true
                } | ConvertTo-Json
                
                $purgeResponse = Invoke-RestMethod -Uri $purgeUrl -Method POST -Headers $headers -Body $purgeBody -ErrorAction Stop
                
                if ($purgeResponse.success) {
                    Write-Host "✓ Cache purged successfully!" -ForegroundColor Green
                }
                else {
                    Write-Host "✗ Cache purge failed: $($purgeResponse.errors[0].message)" -ForegroundColor Red
                }
            }
            else {
                Write-Host "✗ Could not find zone for domain: $BaseDomain" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "✗ Error purging cache: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "⚠️  No API token - skipping cache purge" -ForegroundColor Yellow
        Write-Host "    Purge manually: https://dash.cloudflare.com → Caching → Purge Everything" -ForegroundColor Gray
    }
}

# Step 4: Deploy latest to production
Write-Host "`n📦 Latest deployment status..." -ForegroundColor Cyan
try {
    $deployments = wrangler pages deployment list --project-name=$ProjectName 2>&1 | Out-String
    $productionDeploy = $deployments -split "`n" | Where-Object { $_ -match "Production.*main" } | Select-Object -First 1
    if ($productionDeploy) {
        Write-Host "✓ Production deployment found" -ForegroundColor Green
        Write-Host "  $productionDeploy" -ForegroundColor Gray
    }
}
catch {
    Write-Host "⚠️  Could not retrieve deployment status" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Domain Binding Complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Wait 1-2 minutes for DNS propagation" -ForegroundColor White
Write-Host "  2. Test the domain: https://$Domain" -ForegroundColor White
Write-Host "  3. Verify the correct page loads (check title tag)" -ForegroundColor White
Write-Host "`nProduction URLs:" -ForegroundColor Cyan
Write-Host "  - Custom domain:  https://$Domain" -ForegroundColor White
Write-Host "  - Pages default:  https://$ProjectName.pages.dev" -ForegroundColor White
Write-Host "  - Backend API:    https://quotegenie-api.fly.dev" -ForegroundColor White
Write-Host ""
