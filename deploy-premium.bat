@echo off
REM Deploy Premium EstimateGenie Site
REM Run from EstimateGenie root directory

echo.
echo ========================================
echo   EstimateGenie - Premium Deployment
echo ========================================
echo.

echo [1/2] Activating premium landing page...
copy /Y index-premium.html index.html >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   ✓ index.html updated with premium design
) else (
    echo   ✗ Failed to copy index-premium.html
    exit /b 1
)

echo.
echo [2/2] Deploying to Cloudflare Pages...
wrangler pages deploy . --project-name estimategenie --branch main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   ✓ Deployment Complete!
    echo ========================================
    echo.
    echo Your site is live at:
    echo   https://estimategenie.pages.dev
    echo   https://estimategenie.net
    echo.
    echo What was deployed:
    echo   • Premium dark theme landing page
    echo   • All site assets and pages
    echo   • Backend API configuration
    echo.
    echo ✓ Your professional site is now live!
    echo.
) else (
    echo.
    echo ✗ Deployment failed
    echo Please check the error messages above
    exit /b 1
)
