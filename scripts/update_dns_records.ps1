<#
.SYNOPSIS
  Automate Cloudflare DNS (apex + www) CNAME updates for a Cloudflare Pages project, bind apex to Pages, purge cache, and verify site title.

.DESCRIPTION
  Ensures both the zone apex (estimategenie.net) and www subdomain point to the Pages project domain (estimategenie.pages.dev) instead of a pinned hashed deployment.
  Optionally binds the apex domain to the Pages project (required for production mapping), purges Cloudflare cache, and performs post-change verification.

.PREREQUISITES
  - Environment variable CLOUDFLARE_API_TOKEN must be set with permissions:
      * Zone:DNS:Edit, Zone:Cache Purge, Zone:Read
      * Pages:Edit (for domain binding)
  - PowerShell 5+ (Windows PowerShell) or PowerShell Core.

.PARAMETERS
  -ZoneName          The root domain (default: estimategenie.net)
  -PagesProject      Cloudflare Pages project name (default: estimategenie)
  -PagesAccountId    Cloudflare account ID
  -Target            The CNAME target (Cloudflare Pages project domain) (default: estimategenie.pages.dev)
  -VerifyWaitSeconds Seconds to wait before first verification attempt (default: 20)
  -SkipPagesApexBind Skip adding apex domain to Pages project (use if already bound)
  -Force             Force update even if records already match target

.EXAMPLE
  PS> $env:CLOUDFLARE_API_TOKEN = "******"
  PS> .\update_dns_records.ps1 -Verbose

.NOTES
  Idempotent: existing matching records will be left unchanged unless -Force is provided.
#>
[CmdletBinding()]
Param(
    [string]$ZoneName = "estimategenie.net",
    [string]$PagesProject = "estimategenie",
    [string]$PagesAccountId = "585ba51d553760ece834d6450c4c158f",
    [string]$Target = "estimategenie.pages.dev",
    [int]$VerifyWaitSeconds = 20,
    [switch]$SkipPagesApexBind,
    [switch]$Force,
    [switch]$DryRun
)

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red }

# Validate token
if (-not $env:CLOUDFLARE_API_TOKEN) { Write-Err "CLOUDFLARE_API_TOKEN not set."; exit 1 }

function Get-Headers([bool]$Json = $false) {
    $h = @{}
    $h['Authorization'] = "Bearer $env:CLOUDFLARE_API_TOKEN"
    if ($Json) { $h['Content-Type'] = 'application/json' }
    return $h
}

function Get-CloudflareZoneId($zoneName) {
    Write-Info "Fetching zone id for $zoneName"
    $resp = Invoke-RestMethod -Headers (Get-Headers) -Uri "https://api.cloudflare.com/client/v4/zones?name=$zoneName" -ErrorAction Stop
    if (-not $resp.success -or $resp.result.Count -eq 0) { throw "Zone $zoneName not found." }
    return $resp.result[0].id
}

function Get-DnsRecord($zoneId, $name) {
    $uri = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records?name=$name"
    $resp = Invoke-RestMethod -Headers (Get-Headers) -Uri $uri -ErrorAction Stop
    if ($resp.success -and $resp.result.Count -gt 0) { return $resp.result[0] }
    return $null
}

function Ensure-CNAME($zoneId, $recordName, $content, [bool]$proxied = $true) {
    $existing = Get-DnsRecord $zoneId $recordName
    if ($existing) {
        if ($existing.type -eq 'CNAME' -and $existing.content -eq $content -and -not $Force) {
            Write-Success "CNAME $recordName already points to $content"; return
        }
        if ($existing.type -ne 'CNAME') {
            Write-Info "Existing record $recordName is type $($existing.type). Replacing with CNAME."
            if ($DryRun) { Write-Warn "[DryRun] Would delete record $recordName ($($existing.type)) and create CNAME -> $content"; return }
            $delUri = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records/$($existing.id)"
            $del = Invoke-RestMethod -Headers (Get-Headers) -Uri $delUri -Method DELETE -ErrorAction Stop
            if (-not $del.success) { Write-Err "Failed to delete existing $recordName"; return }
        }
        else {
            Write-Info "Updating existing CNAME $recordName -> $content"
            $body = @{ type = 'CNAME'; name = $recordName; content = $content; proxied = $proxied; ttl = 1 } | ConvertTo-Json -Depth 4
            if ($DryRun) { Write-Warn "[DryRun] Would update $recordName to CNAME $content"; return }
            $updateUri = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records/$($existing.id)"
            $resp = Invoke-RestMethod -Headers (Get-Headers $true) -Uri $updateUri -Method PUT -Body $body -ErrorAction Stop
            if ($resp.success) { Write-Success "Updated $recordName" } else { Write-Err "Failed to update $recordName" }
            return
        }
    }
    Write-Info "Creating CNAME $recordName -> $content"
    $body = @{ type = 'CNAME'; name = $recordName; content = $content; proxied = $proxied; ttl = 1 } | ConvertTo-Json -Depth 4
    if ($DryRun) { Write-Warn "[DryRun] Would create CNAME $recordName -> $content"; return }
    $createUri = "https://api.cloudflare.com/client/v4/zones/$zoneId/dns_records"
    $resp = Invoke-RestMethod -Headers (Get-Headers $true) -Uri $createUri -Method POST -Body $body -ErrorAction Stop
    if ($resp.success) { Write-Success "Created $recordName" } else { Write-Err "Failed to create $recordName" }
}

function Add-PagesDomain($accountId, $project, $domain) {
    Write-Info "Ensuring Pages custom domain $domain bound to project $project"
    $domainsUri = "https://api.cloudflare.com/client/v4/accounts/$accountId/pages/projects/$project/domains"
    $resp = Invoke-RestMethod -Headers (Get-Headers) -Uri $domainsUri -ErrorAction Stop
    if ($resp.success) {
        if ($resp.result.name -eq $project) { $existingList = $resp.result.domains } else { $existingList = $resp.result }
        if ($existingList | Where-Object { $_.name -eq $domain }) { Write-Success "Domain $domain already bound to project."; return }
    }
    Write-Info "Binding domain $domain to Pages project"
    $body = @{ name = $domain } | ConvertTo-Json
    if ($DryRun) { Write-Warn "[DryRun] Would bind $domain to Pages project $project"; return }
    $addResp = Invoke-RestMethod -Headers (Get-Headers $true) -Uri $domainsUri -Method POST -Body $body -ErrorAction Stop
    if ($addResp.success) { Write-Success "Added $domain (status: $($addResp.result.status))" } else { Write-Err "Failed to bind $domain" }
}

function Purge-Cache($zoneId) {
    Write-Info "Purging entire Cloudflare cache"
    $body = @{ purge_everything = $true } | ConvertTo-Json
    $uri = "https://api.cloudflare.com/client/v4/zones/$zoneId/purge_cache"
    if ($DryRun) { Write-Warn "[DryRun] Would purge entire cache for zone $zoneId"; return }
    $resp = Invoke-RestMethod -Headers (Get-Headers $true) -Uri $uri -Method POST -Body $body -ErrorAction Stop
    if ($resp.success) { Write-Success "Cache purge requested" } else { Write-Err "Cache purge failed" }
}

function Get-Title($url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -Headers @{ 'Cache-Control' = 'no-cache, no-store' } -TimeoutSec 30
        $html = $resp.Content
        $start = $html.IndexOf('<title>')
        $end = $html.IndexOf('</title>')
        if ($start -ge 0 -and $end -gt $start) { return $html.Substring($start + 7, $end - $start - 7) }
        return "(no-title)"
    }
    catch { return "(error) $_" }
}

function Verify-Sites($expectedFragment, [int]$retries = 6, [int]$delay = 15) {
    $urls = @("https://$ZoneName/", "https://www.$ZoneName/")
    foreach ($r in 1..$retries) {
        Write-Info "Verification attempt $r/$retries (expect fragment: '$expectedFragment')"
        foreach ($u in $urls) {
            $t = Get-Title $u
            if ($t -like "*$expectedFragment*") { Write-Success "Verified $u => $t" } else { Write-Warn "Title mismatch for $u => $t" }
        }
        if ($r -lt $retries) { Start-Sleep -Seconds $delay }
    }
}

# --- Execution Flow ---
Write-Host "\n=== DNS & Pages Automation Start ===" -ForegroundColor Magenta
try {
    $zoneId = Get-CloudflareZoneId $ZoneName
    Write-Info "Zone ID: $zoneId"

    # Ensure CNAME at apex and www
    Ensure-CNAME $zoneId $ZoneName $Target $true
    Ensure-CNAME $zoneId "www.$ZoneName" $Target $true

    # Bind apex to Pages (optional skip)
    if (-not $SkipPagesApexBind) { Add-PagesDomain -accountId $PagesAccountId -project $PagesProject -domain $ZoneName }
    Add-PagesDomain -accountId $PagesAccountId -project $PagesProject -domain "www.$ZoneName"  # ensure www mapping exists too

    Purge-Cache $zoneId

    Write-Info "Waiting $VerifyWaitSeconds seconds before first verification..."
    if (-not $DryRun) { Start-Sleep -Seconds $VerifyWaitSeconds } else { Write-Warn "[DryRun] Skipping initial wait before verification" }

    # Expected fragment taken from desktop page title
    $expected = "Estimation Wizard"
    Verify-Sites -expectedFragment $expected -retries 6 -delay 20

    Write-Host "\n=== Completed DNS & Pages Automation ===" -ForegroundColor Magenta
}
catch {
    Write-Err "Unhandled error: $_"
    exit 1
}
