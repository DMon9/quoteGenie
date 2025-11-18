# EstimateGenie - Deployment Instructions

## Quick Deploy (Updated Version)

Your latest changes have been prepared for deployment. Follow these steps:

### Option 1: Automated Deployment (Recommended)

#### Windows:
```powershell
# Run the deployment script
.\deploy.ps1
```

#### Linux/Mac:
```bash
# Make executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Deploy Backend to Fly.io

```bash
# Navigate to backend
cd backend

# Login to Fly.io (if not already logged in)
fly auth login

# Deploy backend
fly deploy --config fly.toml --app quotegenie-api --remote-only

# Check status
fly status -a quotegenie-api

# Test health endpoint
curl https://quotegenie-api.fly.dev/health
```

#### Step 2: Deploy Frontend to Cloudflare Pages

```bash
# Return to project root
cd ..

# Login to Cloudflare (if not already logged in)
wrangler login

# Deploy to Cloudflare Pages
wrangler pages deploy . --project-name estimategenie --branch main

# Or deploy with commit tracking
wrangler pages deploy . --project-name estimategenie --branch main --commit-dirty=true
```

## What's Being Deployed

### Frontend Changes:
- ✅ Fixed script loading order (Three.js before Vanta.js)
- ✅ Added mobile menu functionality
- ✅ Implemented file upload with drag-and-drop
- ✅ Connected demo quote generation to API
- ✅ Fixed Feather icons initialization
- ✅ Added error handling throughout
- ✅ Updated API configuration integration

### Backend (No changes needed):
- Already deployed and working
- All endpoints functional
- Demo quote endpoint ready

## Verification Steps

After deployment, test these URLs:

### Backend Tests:
```bash
# Health check
curl https://quotegenie-api.fly.dev/health

# Demo quote
curl -X POST https://quotegenie-api.fly.dev/v1/quotes/demo \
  -H "Content-Type: application/json" \
  -d '{"project_type":"kitchen"}'
```

### Frontend Tests:
1. Visit: https://estimategenie.pages.dev
2. Test mobile menu (resize browser)
3. Try file upload (drag-and-drop an image)
4. Generate a demo quote
5. Verify all navigation links work

## Deployment URLs

- **Production Frontend**: https://estimategenie.pages.dev
- **Production API**: https://quotegenie-api.fly.dev
- **Custom Domain** (if configured): https://estimategenie.net

## Rollback (If Needed)

### Frontend Rollback:
```bash
# View deployments
wrangler pages deployment list --project-name estimategenie

# Rollback to previous deployment
wrangler pages deployment rollback <deployment-id> --project-name estimategenie
```

### Backend Rollback:
```bash
# View releases
fly releases -a quotegenie-api

# Rollback to previous version
fly releases rollback <version> -a quotegenie-api
```

## Monitoring

### Check Logs:

#### Backend Logs:
```bash
fly logs -a quotegenie-api
```

#### Frontend Logs:
- Visit: https://dash.cloudflare.com
- Navigate to: Workers & Pages → estimategenie → Logs

### Check Status:

#### Backend Status:
```bash
fly status -a quotegenie-api
```

#### Frontend Status:
- Cloudflare Dashboard → Pages → estimategenie

## Troubleshooting

### Backend Issues:
1. Check logs: `fly logs -a quotegenie-api`
2. Verify environment variables: `fly secrets list -a quotegenie-api`
3. Check machine status: `fly status -a quotegenie-api`

### Frontend Issues:
1. Check Cloudflare Pages dashboard for build errors
2. Verify all files were uploaded
3. Check browser console for JavaScript errors
4. Clear browser cache and reload

### Common Issues:

**Issue**: "Vanta.js not working"
- **Solution**: Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

**Issue**: "Demo quote fails"
- **Solution**: Check that backend is running: `curl https://quotegenie-api.fly.dev/health`

**Issue**: "Mobile menu not showing"
- **Solution**: Clear cache and verify JavaScript is enabled

## Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Mobile menu works
- [ ] File upload functions
- [ ] Demo quote generates successfully
- [ ] All navigation links work
- [ ] Icons render correctly
- [ ] Responsive design works on mobile
- [ ] No console errors in browser

## Custom Domain Setup (Optional)

### For Cloudflare Pages:
1. Go to: https://dash.cloudflare.com
2. Navigate to: Workers & Pages → estimategenie → Custom Domains
3. Add your domain: estimategenie.net
4. Follow DNS instructions

### For Fly.io Backend:
```bash
# Add custom domain
fly certs create api.estimategenie.net -a quotegenie-api

# Check certificate status
fly certs show api.estimategenie.net -a quotegenie-api
```

## Support

If you encounter issues:
1. Check the logs (see Monitoring section)
2. Review FIXES_APPLIED.md for what was changed
3. Test locally first using test-landing.html
4. Rollback if necessary

## Success!

Once deployed, your updated EstimateGenie site will be live with:
- Working mobile navigation
- Functional file upload
- Demo quote generation
- Professional UI/UX
- Full API integration

Visit your site and test all features to ensure everything works correctly!
