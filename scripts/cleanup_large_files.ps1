param(
    [switch]$DryRun = $false,
    [int64]$SizeLimitMB = 25
)

Write-Host "[cleanup_large_files] Scanning for files larger than ${SizeLimitMB}MB..." -ForegroundColor Cyan

$repoRoot = Split-Path -Parent $PSScriptRoot
$sizeLimitBytes = $SizeLimitMB * 1MB

$scanDirs = @(
    "models",
    "model_server", 
    "orchestrator",
    "backend/uploads",
    "backend/__pycache__",
    ".venv-3",
    ".venv-4"
)

$largeFiles = @()

foreach ($dir in $scanDirs) {
    $fullPath = Join-Path $repoRoot $dir
    if (Test-Path $fullPath) {
        Get-ChildItem -Path $fullPath -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
            $_.Length -gt $sizeLimitBytes
        } | ForEach-Object {
            $largeFiles += [PSCustomObject]@{
                Path   = $_.FullName
                SizeMB = [math]::Round($_.Length / 1MB, 2)
            }
        }
    }
}

if ($largeFiles.Count -eq 0) {
    Write-Host "[cleanup_large_files] No files larger than ${SizeLimitMB}MB found" -ForegroundColor Green
    exit 0
}

Write-Host "`nFound $($largeFiles.Count) files larger than ${SizeLimitMB}MB:" -ForegroundColor Yellow
$largeFiles | Sort-Object -Property SizeMB -Descending | ForEach-Object {
    Write-Host "  $($_.SizeMB)MB - $($_.Path)" -ForegroundColor Yellow
}

if ($DryRun) {
    Write-Host "`n[DRY RUN] No files deleted. Re-run without -DryRun to delete." -ForegroundColor Cyan
    exit 0
}

Write-Host "`nDeleting large files..." -ForegroundColor Red
$deleted = 0
foreach ($file in $largeFiles) {
    try {
        Remove-Item -Path $file.Path -Force -ErrorAction Stop
        Write-Host "  Deleted: $($file.Path)" -ForegroundColor Green
        $deleted++
    }
    catch {
        Write-Warning "  Failed to delete: $($file.Path) - $_"
    }
}

Write-Host "`nDeleted $deleted/$($largeFiles.Count) files" -ForegroundColor Green
Write-Host "[cleanup_large_files] Cleanup complete" -ForegroundColor Green
