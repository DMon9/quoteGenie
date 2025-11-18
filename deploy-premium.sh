#!/bin/bash
# Deploy Premium Landing Page and Site
# Run from EstimateGenie root directory

echo "🚀 EstimateGenie - Deploying Premium Site"
echo "=========================================="
echo ""

# Step 1: Copy premium theme to index.html
echo "1️⃣  Activating premium landing page..."
cp index-premium.html index.html
echo "   ✅ index.html updated with premium design"
echo ""

# Step 2: Deploy to Cloudflare Pages
echo "2️⃣  Deploying to Cloudflare Pages..."
wrangler pages deploy . --project-name estimategenie --branch main

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "🌐 Your site is live at:"
    echo "   https://estimategenie.pages.dev"
    echo "   https://estimategenie.net (if domain configured)"
    echo ""
    echo "📋 What was deployed:"
    echo "   • Premium dark theme landing page"
    echo "   • Updated pricing page"
    echo "   • Updated features page"
    echo "   • All documentation"
    echo ""
    echo "🎉 Your professional site is now live!"
else
    echo ""
    echo "❌ Deployment failed. Please check the error above."
    exit 1
fi
