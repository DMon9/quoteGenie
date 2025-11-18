#!/bin/bash
# EstimateGenie Full Deployment Script
# Deploys both backend (Fly.io) and frontend (Cloudflare Pages)

set -e

echo "======================================"
echo "EstimateGenie Deployment"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check git status
echo -e "${CYAN}Checking git status...${NC}"
if [ -d ".git" ]; then
    git status --short
    echo ""
    read -p "Commit changes before deploying? (y/n): " commit_choice
    if [ "$commit_choice" = "y" ]; then
        git add .
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg" || true
        git push || echo -e "${YELLOW}Push failed or not configured${NC}"
    fi
else
    echo -e "${YELLOW}Not a git repository${NC}"
fi

echo ""
echo "======================================"
echo "Step 1: Deploy Backend to Fly.io"
echo "======================================"
echo ""

# Navigate to backend directory
cd backend

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo -e "${YELLOW}Fly CLI not found. Installing...${NC}"
    curl -L https://fly.io/install.sh | sh
    export FLYCTL_INSTALL="/home/$USER/.fly"
    export PATH="$FLYCTL_INSTALL/bin:$PATH"
fi

# Check if logged in to fly
echo -e "${CYAN}Checking Fly.io authentication...${NC}"
if ! fly auth whoami &> /dev/null; then
    echo -e "${YELLOW}Please login to Fly.io:${NC}"
    fly auth login
fi

# Deploy backend
echo -e "${GREEN}Deploying backend...${NC}"
fly deploy --config fly.toml --app quotegenie-api --remote-only

# Check deployment status
echo -e "${CYAN}Checking backend health...${NC}"
sleep 5
curl -s https://quotegenie-api.fly.dev/health | jq . || echo -e "${RED}Health check failed${NC}"

echo ""
echo -e "${GREEN}Backend deployed successfully!${NC}"
echo "URL: https://quotegenie-api.fly.dev"

# Return to root
cd ..

echo ""
echo "======================================"
echo "Step 2: Deploy Frontend to Cloudflare Pages"
echo "======================================"
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo -e "${YELLOW}Wrangler not found. Installing...${NC}"
    npm install -g wrangler
fi

# Check if logged in to Cloudflare
echo -e "${CYAN}Checking Cloudflare authentication...${NC}"
if ! wrangler whoami &> /dev/null; then
    echo -e "${YELLOW}Please login to Cloudflare:${NC}"
    wrangler login
fi

# Deploy to Cloudflare Pages
echo -e "${GREEN}Deploying frontend to Cloudflare Pages...${NC}"
wrangler pages deploy . \
    --project-name estimategenie \
    --branch main \
    --commit-dirty=true

echo ""
echo -e "${GREEN}Frontend deployed successfully!${NC}"
echo "Production URL: https://estimategenie.pages.dev"
echo ""

echo "======================================"
echo "Deployment Summary"
echo "======================================"
echo ""
echo -e "${GREEN}✓ Backend:${NC}  https://quotegenie-api.fly.dev"
echo -e "${GREEN}✓ Frontend:${NC} https://estimategenie.pages.dev"
echo ""
echo "Next steps:"
echo "1. Test the API: curl https://quotegenie-api.fly.dev/health"
echo "2. Visit the site: https://estimategenie.pages.dev"
echo "3. Check Cloudflare Pages dashboard for custom domain setup"
echo "4. Monitor Fly.io dashboard for backend logs and metrics"
echo ""
echo -e "${GREEN}Deployment complete! 🚀${NC}"
