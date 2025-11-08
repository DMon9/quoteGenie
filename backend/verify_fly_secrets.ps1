<#
.SYNOPSIS
  Verifies required and optional Fly.io secrets for the quotegenie-api app.

.DESCRIPTION
  Checks presence (not values) of secrets via `flyctl secrets list` and compares
  against required & optional groups for core functionality, payments, and multi-model AI.
  Outputs a color-coded report and exit code (0 if all required are present, 1 otherwise).

.PREREQUISITES
  - flyctl installed and authenticated (`flyctl auth whoami`)
  - PowerShell 5+ (Windows) or pwsh (Core)

.USAGE
  ./verify_fly_secrets.ps1             # default app name 'quotegenie-api'
  ./verify_fly_secrets.ps1 -AppName my-other-app
  ./verify_fly_secrets.ps1 -Json       # machine readable output

.PARAMETER AppName
  Fly.io application name (defaults to quotegenie-api)

.PARAMETER Json
  Emit JSON only (no color/table formatting) for CI usage

.EXAMPLES
  PS> ./verify_fly_secrets.ps1
  PS> ./verify_fly_secrets.ps1 -AppName quotegenie-staging -Json | jq
#>
[CmdletBinding()]
param(
    [string]$AppName = 'quotegenie-api',
    [switch]$Json
)

function Get-SecretNames($App) {
    $raw = flyctl secrets list -a $App 2>$null
    if (-not $raw) { return @() }
    $lines = $raw -split "`n" | Where-Object { $_ -match '\S' -and $_ -notmatch 'NAME' }
    $names = @()
    foreach ($l in $lines) {
        $tok = ($l -split '\s+')[0]
        if ($tok -and $tok -notmatch '^[=-]+$') { $names += $tok }
    }
    return $names | Sort-Object -Unique
}

$requiredCore = @(
    'JWT_SECRET_KEY',      # auth
    'GOOGLE_API_KEY'       # Gemini model
)
$optionalAI = @(
    'OPENAI_API_KEY',      # GPT-4 Vision
    'ANTHROPIC_API_KEY',   # Claude 3
    'OPENROUTER_API_KEY'   # OpenRouter models (e.g., gpt-oss-20b)
)
$optionalPayments = @(
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'PRICE_ID_PRO_MONTHLY',
    'PRICE_ID_PRO_ANNUAL'
)
$otherUseful = @(
    'ALLOW_ORIGINS',
    'PREFERRED_MODEL',
    'GEMINI_MODEL',
    'GPT4V_MODEL',
    'CLAUDE_MODEL',
    'OPENROUTER_MODEL'
)

$allSecrets = Get-SecretNames -App $AppName
if (-not $allSecrets) {
    Write-Host "Failed to fetch secrets (app: $AppName). Are you logged in?" -ForegroundColor Red
    exit 1
}

function Build-Status($list, $category, $required = $false) {
    $out = @()
    foreach ($name in $list) {
        $present = $allSecrets -contains $name
        $out += [pscustomobject]@{
            category = $category
            name     = $name
            present  = $present
            required = $required
        }
    }
    return $out
}

$report = @()
$report += Build-Status $requiredCore 'core' $true
$report += Build-Status $optionalAI 'ai'
$report += Build-Status $optionalPayments 'payments'
$report += Build-Status $otherUseful 'config'

$missingRequired = $report | Where-Object { $_.required -and -not $_.present }

if ($Json) {
    $report | ConvertTo-Json -Depth 4
    if ($missingRequired) { exit 1 } else { exit 0 }
}

Write-Host "Fly.io Secret Verification for app: $AppName" -ForegroundColor Cyan
Write-Host "Detected $(($allSecrets).Count) secrets on platform." -ForegroundColor DarkCyan
Write-Host "" 

function Show-Section($title, $items) {
    if (-not $items) { return }
    Write-Host "== $title ==" -ForegroundColor Yellow
    foreach ($i in $items) {
        if ($i.present) {
            Write-Host ("  [+] {0}" -f $i.name) -ForegroundColor Green
        }
        else {
            if ($i.required) { $mark = ' (REQUIRED)'; $color = 'Red' } else { $mark = ''; $color = 'DarkYellow' }
            Write-Host ("  [ ] {0}{1}" -f $i.name, $mark) -ForegroundColor $color
        }
    }
    Write-Host ""
}

Show-Section 'Core (Required)' ($report | Where-Object { $_.category -eq 'core' })
Show-Section 'AI (Optional)' ($report | Where-Object { $_.category -eq 'ai' })
Show-Section 'Payments (Optional)' ($report | Where-Object { $_.category -eq 'payments' })
Show-Section 'Additional Config (Optional)' ($report | Where-Object { $_.category -eq 'config' })

if ($missingRequired) {
    Write-Host "Missing REQUIRED secrets: $((($missingRequired).name) -join ', ')" -ForegroundColor Red
    Write-Host "Add them with:" -ForegroundColor Red
    foreach ($m in $missingRequired) {
        Write-Host ("  flyctl secrets set {0}=<value> -a {1}" -f $m.name, $AppName) -ForegroundColor DarkGray
    }
    exit 1
}
else {
    Write-Host "All required secrets present ✅" -ForegroundColor Green
}

Write-Host "Done." -ForegroundColor Cyan
exit 0
