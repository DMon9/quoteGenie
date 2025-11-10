# Custom Domain Routing Fix Guide

**Issue:** Custom domain (estimategenie.net) serving homepage content for all URLs  
**Root Cause:** Cloudflare Pages SPA (Single Page Application) fallback behavior  
**Fix Applied:** Explicit routing rules and configuration

## What Was Changed

### 1. Updated `_redirects` File

Added explicit routing rules to prevent SPA fallback:

```
/*.html 200
/pricing.html /pricing.html 200
/login.html /login.html 200
# ... all other HTML pages
/* /404.html 404  # Disable SPA fallback
```

**Why:** Cloudflare Pages was treating the site as an SPA, serving `index.html` for all routes. Explicit rules ensure each HTML file is served correctly.

### 2. Created `404.html` Page

Custom 404 error page with helpful navigation links.

**Why:** The fallback route `/* /404.html 404` requires this page to exist.

### 3. Created `wrangler.toml` Configuration

Pages project configuration to control build behavior.

**Why:** Ensures Cloudflare Pages processes HTML files correctly and doesn't skip them.

### 4. Updated `_headers` File

Already exists with proper security headers.

**Why:** Provides security headers and cache control for all resources.

### 5. Created Automation Script

`scripts/fix_custom_domain_routing.ps1` - Automated deployment and verification.

**Why:** Streamlines the fix deployment and provides verification steps.

## How to Deploy the Fix

### Option 1: Use Automated Script (Recommended)

```powershell
.\scripts\fix_custom_domain_routing.ps1 -Force
```

### Option 2: Manual Deployment

```powershell
.\scripts\deploy_pages_clean.ps1 -CommitDirty
```

## Verification Steps

### 1. Test Deployment URL First

```bash
# Each URL should show DIFFERENT content:
https://[deployment-id].estimategenie.pages.dev/
https://[deployment-id].estimategenie.pages.dev/pricing.html
https://[deployment-id].estimategenie.pages.dev/login.html
```

### 2. Check Custom Domain Configuration

1. Go to: <https://dash.cloudflare.com/>
2. Navigate to: **Workers & Pages** > **estimategenie** > **Settings** > **Custom domains**
3. Verify these domains are listed:
   - `estimategenie.net`
   - `www.estimategenie.net`

### 3. Verify DNS Records

Check your domain registrar's DNS settings:

```
Type: CNAME
Name: @ (or estimategenie.net)
Target: estimategenie.pages.dev
TTL: Auto

Type: CNAME
Name: www
Target: estimategenie.pages.dev
TTL: Auto
```

**Alternative (if CNAME at root not supported):**

```
Type: ALIAS or ANAME
Name: @
Target: estimategenie.pages.dev

Type: CNAME
Name: www
Target: estimategenie.pages.dev
```

### 4. Clear Cloudflare Cache (If Needed)

1. Go to Cloudflare Dashboard
2. Select your domain
3. Navigate to: **Caching** > **Configuration**
4. Click: **Purge Everything**
5. Wait 2-5 minutes for propagation

### 5. Test Custom Domain

```bash
# Test in incognito/private mode to avoid browser cache
https://estimategenie.net/
https://estimategenie.net/pricing.html
https://estimategenie.net/login.html
https://estimategenie.net/features.html
```

**Expected Result:** Each URL should show DIFFERENT content specific to that page.

## Troubleshooting

### Issue: Still Showing Homepage for All Routes

**Solution 1: Wait for Propagation**

- CDN changes can take 2-5 minutes
- DNS changes can take up to 24 hours (but usually minutes)

**Solution 2: Purge Cloudflare Cache**

```powershell
# Via Dashboard (easier):
# Cloudflare Dashboard > Caching > Purge Everything

# Via API:
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

**Solution 3: Check Custom Domain Setup**

1. Ensure custom domain is properly added to Pages project
2. Verify SSL/TLS certificate is active
3. Check DNS records are correct (no typos)

**Solution 4: Verify Latest Deployment is Active**

1. Go to: Cloudflare Dashboard > Workers & Pages > estimategenie
2. Check **Deployments** tab
3. Ensure latest deployment is marked as "Production"
4. If not, click "..." > "Rollback to this deployment"

### Issue: 404 Errors for Valid Pages

**Cause:** `_redirects` file may have incorrect syntax

**Solution:**

1. Check `_redirects` file formatting (no extra spaces)
2. Ensure all HTML files listed exist in deployment
3. Redeploy with `.\scripts\deploy_pages_clean.ps1 -CommitDirty`

### Issue: Custom Domain Not Listed

**Solution:**

1. Add custom domain manually in Cloudflare Pages:
   - Dashboard > Workers & Pages > estimategenie > Custom domains
   - Click "Set up a custom domain"
   - Enter: `estimategenie.net`
   - Follow prompts to verify
2. Repeat for `www.estimategenie.net`

## Testing Checklist

- [ ] Deployment URL serves different content per page
- [ ] Custom domain DNS records configured correctly
- [ ] Custom domain listed in Cloudflare Pages settings
- [ ] SSL/TLS certificate is active
- [ ] Cloudflare cache purged
- [ ] Waited 5 minutes for propagation
- [ ] Tested in incognito/private browsing mode
- [ ] Homepage shows homepage content
- [ ] Pricing page shows pricing content (not homepage)
- [ ] Login page shows login form (not homepage)
- [ ] 404 page shows for non-existent routes

## Files Modified

1. `_redirects` - Explicit routing rules to prevent SPA fallback
2. `404.html` - Custom error page (NEW)
3. `wrangler.toml` - Pages configuration (NEW)
4. `scripts/fix_custom_domain_routing.ps1` - Automation script (NEW)
5. `scripts/deploy_pages_clean.ps1` - Updated to include new files

## Technical Details

### How Cloudflare Pages Routing Works

By default, Cloudflare Pages assumes sites are SPAs and serves `index.html` for all routes. This is controlled by:

1. **Asset routing:** Static files (HTML, CSS, JS) are served directly
2. **SPA fallback:** Unknown routes fallback to `/index.html`
3. **`_redirects` rules:** Override default behavior with explicit rules

Our fix disables SPA fallback by:

- Explicitly listing all HTML routes with `200` status
- Using `/* /404.html 404` as final fallback instead of `index.html`
- Ensuring each `.html` file is served as-is without SPA logic

### Configuration Priority

Cloudflare Pages processes in this order:

1. `_redirects` - Highest priority
2. `_headers` - Applied after routing
3. `wrangler.toml` - Build configuration
4. Default SPA behavior - Only if no rules match

## Additional Resources

- [Cloudflare Pages Redirects](https://developers.cloudflare.com/pages/configuration/redirects/)
- [Cloudflare Pages Custom Domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Cloudflare Pages Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/)

## Support

If issues persist after following all steps:

1. Check Cloudflare Pages status: <https://www.cloudflarestatus.com/>
2. Review deployment logs in Cloudflare Dashboard
3. Contact Cloudflare Support with deployment ID
4. Check `DEPLOYMENT_STATUS.md` for latest deployment information
