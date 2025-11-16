# Cloudflare API Token Creation Guide

## Quick Setup (Follow these exact steps)

### 1. Create Custom Token

On the API Tokens page that just opened:

1. Click **"Create Token"** (blue button)
2. Scroll down and click **"Create Custom Token"** → **"Get started"**

### 2. Set Token Name

- **Token name**: `EstimateGenie Pages Automation`

### 3. Add Permissions (CRITICAL - Add all 3)

Click **"+ Add more"** to add each permission:

**Permission 1:**

- Resource: **Account**
- Permission: **Cloudflare Pages**
- Access: **Edit** ⬅️ IMPORTANT: Must be Edit, not Read

**Permission 2:**

- Resource: **Zone**
- Permission: **DNS**
- Access: **Edit**

**Permission 3:**

- Resource: **Zone**
- Permission: **Cache Purge**
- Access: **Purge**

### 4. Set Account/Zone Resources

**Account Resources:**

- Include: **Specific account** → Select **SportsDugout** (585ba51d...)

**Zone Resources:**

- Include: **Specific zone** → Select **estimategenie.net**

### 5. Additional Settings

- **Client IP Address Filtering**: Leave blank (all IPs)
- **TTL**: Leave default (or set to 1 year for convenience)

### 6. Create & Copy Token

1. Click **"Continue to summary"**
2. Review the permissions (should show 3 permissions)
3. Click **"Create Token"**
4. **COPY THE TOKEN** (you'll only see it once!)

### 7. Test the Token

Paste the token in PowerShell and run automation:

```powershell
# Set the new token
$env:CLOUDFLARE_API_TOKEN = "PASTE_YOUR_NEW_TOKEN_HERE"

# Test it
.\bind_domain_api.ps1
```

## What You Should See

✅ **Adding domain: <www.estimategenie.net>**

- "SUCCESS: Domain added!" OR "OK: Domain already exists"

✅ **Purging cache for: estimategenie.net**

- "SUCCESS: Cache purged!"

✅ **Verifying domain...**

- Title: EstimateGenie - AI-Powered Estimation Wizard

## Troubleshooting

**If you see 400/403 errors:**

- Go back and verify you selected **Edit** (not Read) for Cloudflare Pages
- Make sure you selected the correct account (SportsDugout)
- Recreate the token with correct permissions

**If domain still shows mobile:**

- Wait 30-60 seconds after cache purge
- Hard refresh: Ctrl+Shift+R
- Check in incognito/private window
