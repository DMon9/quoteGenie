param(
    [string]$ProjectName = "estimategenie",
    [string]$Directory = ".",
    [switch]$CommitDirty = $true
)

Write-Host "[deploy_pages] Starting Cloudflare Pages deploy..." -ForegroundColor Cyan

# Preflight: wrangler
if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Error "Wrangler CLI not found. Install from https://developers.cloudflare.com/pages/wrangler/ or 'npm i -g wrangler' and try again."
    exit 1
}

# Preflight: Cloudflare creds (token recommended). API token must have Pages:Edit permissions.
if (-not $env:CF_API_TOKEN -and -not $env:CLOUDFLARE_API_TOKEN) {
    Write-Warning "CF_API_TOKEN or CLOUDFLARE_API_TOKEN env var not found. If you're already logged in via 'wrangler login', this can still work locally."
}
if (-not $env:CF_ACCOUNT_ID -and -not $env:CLOUDFLARE_ACCOUNT_ID) {
    Write-Warning "CF_ACCOUNT_ID or CLOUDFLARE_ACCOUNT_ID env var not set. Wrangler may infer from login; otherwise set it for CI."
}

# Ensure .cfignore exists with sane defaults (do not overwrite if present)
$cfIgnorePath = Join-Path -Path (Get-Location) -ChildPath ".cfignore"
if (-not (Test-Path $cfIgnorePath)) {
    @"
backend/
api-worker/
model_server/
models/
orchestrator/
scripts/
.venv*/
__pycache__/
*.pt
*.onnx
*.ckpt
*.safetensors
*.bin
*.tar*
*.zip
*.7z
*.log
"@ | Set-Content -NoNewline $cfIgnorePath -Encoding UTF8
    Write-Host "[deploy_pages] Created default .cfignore" -ForegroundColor Yellow
}

$commitDirtyArg = if ($CommitDirty) { "--commit-dirty=true" } else { "" }

$cmd = @(
    "pages", "deploy",
    $Directory,
    "--project-name=$ProjectName",
    $commitDirtyArg
) | Where-Object { $_ -ne "" }

Write-Host "[deploy_pages] Running: wrangler $($cmd -join ' ')" -ForegroundColor Cyan

try {
    wrangler @cmd
    if ($LASTEXITCODE -ne 0) { throw "Wrangler exited with code $LASTEXITCODE" }
    Write-Host "[deploy_pages] ✅ Deploy completed" -ForegroundColor Green
}
catch {
    Write-Error "[deploy_pages] ❌ Deploy failed: $_"
    exit 1
}
