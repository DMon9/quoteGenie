@echo off
cd C:\Users\user\quoteGenie

echo ========================================
echo   Activating Premium Theme
echo ========================================
echo.

REM Backup current index.html
if exist index.html (
    copy /Y index.html index-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%.html >nul 2>&1
    echo [OK] Backup created
)

REM Copy premium theme
copy /Y index-premium.html index.html >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Premium theme activated
) else (
    echo [ERROR] Failed to copy premium theme
    exit /b 1
)

echo.
echo ========================================
echo   Deploying to Cloudflare Pages
echo ========================================
echo.

wrangler pages deploy . --project-name estimategenie --branch main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your site is live at:
    echo   https://estimategenie.pages.dev
    echo   https://estimategenie.net
    echo.
) else (
    echo.
    echo [ERROR] Deployment failed
    exit /b 1
)
