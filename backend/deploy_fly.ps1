param(
    [string]$AppName = "quotegenie-api",
    [switch]$SetSecrets
)

$ErrorActionPreference = "Stop"

function Ensure-FlyCtl {
    try {
        fly --version | Out-Null
        return
    }
    catch {
        Write-Host "Installing Flyctl..." -ForegroundColor Yellow
        iwr https://fly.io/install.ps1 -useb | iex
    }
}

function Ensure-FlyAuth {
    try {
        fly auth whoami | Out-Null
    }
    catch {
        Write-Host "Logging into Fly..." -ForegroundColor Yellow
        fly auth login
    }
}

function Set-AppSecrets {
    param([string]$App)
    $secrets = @{}
    if ($env:GOOGLE_API_KEY) { $secrets["GOOGLE_API_KEY"] = $env:GOOGLE_API_KEY }
    if ($env:STRIPE_SECRET_KEY) { $secrets["STRIPE_SECRET_KEY"] = $env:STRIPE_SECRET_KEY }
    if ($env:STRIPE_PUBLISHABLE_KEY) { $secrets["STRIPE_PUBLISHABLE_KEY"] = $env:STRIPE_PUBLISHABLE_KEY }
    if ($env:STRIPE_WEBHOOK_SECRET) { $secrets["STRIPE_WEBHOOK_SECRET"] = $env:STRIPE_WEBHOOK_SECRET }
    if ($env:AUTH0_DOMAIN) { $secrets["AUTH0_DOMAIN"] = $env:AUTH0_DOMAIN }
    if ($env:AUTH0_CLIENT_ID) { $secrets["AUTH0_CLIENT_ID"] = $env:AUTH0_CLIENT_ID }
    if ($env:AUTH0_CLIENT_SECRET) { $secrets["AUTH0_CLIENT_SECRET"] = $env:AUTH0_CLIENT_SECRET }
    if ($env:AUTH0_AUDIENCE) { $secrets["AUTH0_AUDIENCE"] = $env:AUTH0_AUDIENCE }
    if ($env:SENTRY_DSN) { $secrets["SENTRY_DSN"] = $env:SENTRY_DSN }
    if ($env:ENV) { $secrets["ENV"] = $env:ENV } else { $secrets["ENV"] = "production" }

    if ($secrets.Count -gt 0) {
        $pairs = $secrets.GetEnumerator() | ForEach-Object { ("{0}={1}" -f $_.Key, ($_.Value -replace '"', '\"')) }
        Write-Host "Setting Fly secrets (" ($secrets.Keys -join ', ') ")..." -ForegroundColor Yellow
        fly secrets set $pairs -a $App | Out-Null
    }
    else {
        Write-Host "No env secrets found to set. Skipping." -ForegroundColor DarkYellow
    }
}

# Main
Push-Location $PSScriptRoot
try {
    Ensure-FlyCtl
    Ensure-FlyAuth

    if ($SetSecrets) {
        Set-AppSecrets -App $AppName
    }

    Write-Host "Deploying backend to Fly (app=$AppName)..." -ForegroundColor Cyan
    # Uses backend/fly.toml and Dockerfile.fly; release_command runs DB migration
    fly deploy --config fly.toml --app $AppName --remote-only

    Write-Host "Checking app status..." -ForegroundColor Cyan
    fly status -a $AppName

    $base = "https://$AppName.fly.dev"
    try {
        $root = Invoke-RestMethod -Uri "$base/" -TimeoutSec 20
        Write-Host "/ response:" ([string]$root | Select-Object -First 1) -ForegroundColor Gray
    }
    catch { Write-Host "Root check failed (may be fine if cold start)" -ForegroundColor DarkYellow }

    try {
        $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 20
        if ($health.status -eq "healthy") {
            Write-Host "/health: healthy" -ForegroundColor Green
        }
        else {
            Write-Host "/health: " ($health | ConvertTo-Json -Compress) -ForegroundColor Yellow
        }
    }
    catch { Write-Host "Health check failed; check logs" -ForegroundColor Yellow }

    Write-Host "Recent logs:" -ForegroundColor Cyan
    fly logs -a $AppName --max-lines 50

    Write-Host "Done. Base URL: $base" -ForegroundColor Green
}
finally {
    Pop-Location
}
