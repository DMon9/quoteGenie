param(
    [string]$ProjectName = "estimategenie",
    [switch]$CommitDirty
)

Write-Host "[deploy_pages_clean] Preparing clean frontend deployment..." -ForegroundColor Cyan

# Create deploy directory
$deployDir = "deploy-frontend"
if (Test-Path $deployDir) {
    Remove-Item -Path $deployDir -Recurse -Force
}
New-Item -ItemType Directory -Path $deployDir -Force | Out-Null

# Copy only frontend files (HTML, CSS, JS, assets, _redirects, robots.txt, sitemap)
Write-Host "[deploy_pages_clean] Copying frontend files..." -ForegroundColor Cyan

$frontendFiles = @(
    "*.html",
    "robots.txt",
    "sitemaps.xml",
    "_redirects",
    "_headers",
    "wrangler.toml"
)

foreach ($pattern in $frontendFiles) {
    Get-ChildItem -Path . -Filter $pattern -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $deployDir -Force
        Write-Host "  Copied: $($_.Name)" -ForegroundColor Gray
    }
}

# Copy assets directory
if (Test-Path "assets") {
    Copy-Item -Path "assets" -Destination $deployDir -Recurse -Force
    Write-Host "  Copied: assets/" -ForegroundColor Gray
}

# Count files in deploy dir
$fileCount = (Get-ChildItem -Path $deployDir -Recurse -File | Measure-Object).Count
Write-Host "[deploy_pages_clean] Prepared $fileCount files for deployment" -ForegroundColor Cyan

if ($fileCount -gt 20000) {
    Write-Error "Too many files ($fileCount). Pages limit is 20,000."
    exit 1
}

# Preflight: wrangler
if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Error "Wrangler CLI not found. Install from https://developers.cloudflare.com/pages/wrangler/"
    exit 1
}

$commitDirtyArg = if ($CommitDirty) { "--commit-dirty=true" } else { "" }

$cmd = @(
    "pages", "deploy",
    $deployDir,
    "--project-name=$ProjectName",
    $commitDirtyArg
) | Where-Object { $_ -ne "" }

Write-Host "[deploy_pages_clean] Running: wrangler $($cmd -join ' ')" -ForegroundColor Cyan

try {
    wrangler @cmd
    if ($LASTEXITCODE -ne 0) { throw "Wrangler exited with code $LASTEXITCODE" }
    Write-Host "[deploy_pages_clean] ✅ Deploy completed" -ForegroundColor Green
    
    # Cleanup deploy dir
    Write-Host "[deploy_pages_clean] Cleaning up $deployDir..." -ForegroundColor Gray
    Remove-Item -Path $deployDir -Recurse -Force -ErrorAction SilentlyContinue
}
catch {
    Write-Error "[deploy_pages_clean] ❌ Deploy failed: $_"
    Remove-Item -Path $deployDir -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}
