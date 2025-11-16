# Cloudflare Pages Domain Binding Automation

## Quick Start

### Option 1: Using the API Script (Recommended)

1. **Get a Cloudflare API Token**
   - Go to: <https://dash.cloudflare.com/profile/api-tokens>
   - Click "Create Token"
   - Use the "Edit Cloudflare Workers" template and add:
     - Account:Cloudflare Pages:Edit
     - Zone:DNS:Edit  
     - Zone:Cache Purge:Purge
   - Click "Continue to summary" → "Create Token"
   - Copy the token

2. **Set the environment variable**

   ```powershell
   $env:CLOUDFLARE_API_TOKEN = "YOUR_TOKEN_HERE"
   ```

3. **Run the binding script**

   ```powershell
   .\bind_domain_quick.ps1
   ```

### Option 2: Manual Dashboard Steps

1. Go to: <https://dash.cloudflare.com/585ba51d553760ece834d6450c4c158f/pages/view/estimategenie>
2. Click "Custom domains" tab
3. Click "Set up a custom domain"
4. Enter: `www.estimategenie.net`
5. Follow the prompts to complete setup
6. Purge cache: <https://dash.cloudflare.com> → Caching → Configuration → Purge Everything

## What the Scripts Do

### `bind_domain.ps1` (Full-featured)

- Comprehensive error handling and validation
- Detailed status reporting
- Works with or without API token
- Provides manual fallback instructions

### `bind_domain_quick.ps1` (Streamlined)

- Fast execution
- Requires API token
- Minimal output
- Best for automation/CI

## Files Created

- `bind_domain.ps1` - Full automation script with fallbacks
- `bind_domain_quick.ps1` - Quick API-based binding
- `DOMAIN_BINDING_GUIDE.md` - This file

## Verification Steps

After binding, verify the domain:

```powershell
# Check title tag
(Invoke-WebRequest -UseBasicParsing https://www.estimategenie.net).Content | Select-String '<title>'

# Expected: EstimateGenie - AI-Powered Estimation Wizard
# (Not: EstimateGenie Mobile - AI-Powered Quotes)
```

## Troubleshooting

### "Domain already exists" error

This is OK - it means the domain is already bound to the project.

### DNS not resolving

Wait 1-2 minutes for DNS propagation, then try again.

### Wrong page still showing

1. Purge cache: `.\bind_domain_quick.ps1`
2. Hard refresh browser: Ctrl+Shift+R
3. Check in incognito/private window

## Production URLs

- Custom domain: <https://www.estimategenie.net>
- Root domain: <https://estimategenie.net> (add this separately if needed)
- Pages default: <https://estimategenie.pages.dev>
- Backend API: <https://quotegenie-api.fly.dev>

## API Token Permissions Required

Minimum permissions for automation:

- Account → Cloudflare Pages → Edit
- Zone → DNS → Edit
- Zone → Cache Purge → Purge

Optional (for enhanced features):

- Zone → Zone → Read
- Account → Analytics → Read
