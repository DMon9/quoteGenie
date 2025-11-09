# Cloudflare Pages Deployment Setup

This repository is configured to automatically deploy the frontend to Cloudflare Pages on every push to the `main` branch.

## Prerequisites

Before the deployment can work, you need to set up the following GitHub secrets:

### Required Secrets

1. **CLOUDFLARE_API_TOKEN**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
   - Click "Create Token"
   - Use the "Edit Cloudflare Workers" template or create a custom token with:
     - Permissions:
       - Account - Cloudflare Pages - Edit
     - Account Resources:
       - Include - Your Account
   - Copy the token and add it to GitHub repository secrets

2. **CLOUDFLARE_ACCOUNT_ID**
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Select your account
   - The Account ID is shown in the right sidebar under "Account ID"
   - Copy this ID and add it to GitHub repository secrets

### How to Add Secrets to GitHub

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add `CLOUDFLARE_API_TOKEN` with the value from Cloudflare
5. Click **New repository secret** again
6. Add `CLOUDFLARE_ACCOUNT_ID` with your account ID from Cloudflare

## Project Configuration

The deployment is configured to use:
- **Project Name**: `estimategenie`
- **Directory**: `.` (root directory)
- **Branch**: `main`

Make sure the Cloudflare Pages project `estimategenie` exists in your Cloudflare account. If it doesn't exist yet, the first deployment will create it automatically.

## Deployment Workflow

The workflow is triggered:
- Automatically on every push to the `main` branch
- Manually via the Actions tab (workflow_dispatch)

## Files Deployed

The deployment includes:
- All HTML files (`index.html`, `features.html`, `about.html`, etc.)
- Assets directory (`assets/css/`, `assets/js/`)
- Static files (`robots.txt`, `sitemaps.xml`, `_redirects`)
- Configuration files are excluded via `.wranglerignore`

## Verifying Deployment

After pushing to `main`:
1. Go to the **Actions** tab in GitHub
2. Check the "Deploy to Cloudflare Pages" workflow
3. Once complete, visit your Cloudflare Pages URL: `https://estimategenie.pages.dev`

## Custom Domain

To add a custom domain:
1. Go to [Cloudflare Pages Dashboard](https://dash.cloudflare.com)
2. Select your project
3. Go to **Custom domains**
4. Add your domain (e.g., `estimategenie.net`)
5. Cloudflare will automatically configure DNS

## Troubleshooting

### Deployment fails with authentication error
- Verify `CLOUDFLARE_API_TOKEN` is set correctly
- Ensure the token has the correct permissions (Cloudflare Pages - Edit)
- Check if the token has expired and regenerate if needed

### Deployment fails with "project not found"
- Ensure `CLOUDFLARE_ACCOUNT_ID` is correct
- The project will be created automatically on first deployment
- Check that your account has Pages enabled

### Files not deploying
- Check `.wranglerignore` to ensure files aren't excluded
- Verify files are committed to the repository
- Check the deployment logs in GitHub Actions

## Manual Deployment

You can also deploy manually using the Wrangler CLI:

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
wrangler pages deploy . --project-name estimategenie
```

## Additional Resources

- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [Cloudflare Pages GitHub Action](https://github.com/cloudflare/pages-action)
- [Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)
