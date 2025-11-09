# Manual Domain Binding Steps

Your API token has **Read** permissions but needs **Edit** permissions for full automation.

## Quick Manual Setup (2 minutes)

### Step 1: Bind the Domain

1. Open: <https://dash.cloudflare.com/585ba51d553760ece834d6450c4c158f/pages/view/estimategenie>
2. Click the **"Custom domains"** tab
3. Click **"Set up a custom domain"** button
4. Enter: `www.estimategenie.net`
5. Click **"Continue"** and follow the prompts
6. Cloudflare will automatically configure DNS (you should see a checkmark when done)

### Step 2: Purge Cache

1. Go to: <https://dash.cloudflare.com> (main dashboard)
2. Click on your **"estimategenie.net"** domain
3. In the left sidebar, click **"Caching"** → **"Configuration"**
4. Click **"Purge Everything"**
5. Confirm the purge

### Step 3: Verify

Wait 30-60 seconds, then test:

```powershell
# Check the title
(Invoke-WebRequest -UseBasicParsing https://www.estimategenie.net).Content.Substring(0, 500)
```

Expected title: `EstimateGenie - AI-Powered Estimation Wizard`
(Not: `EstimateGenie Mobile - AI-Powered Quotes`)

## Alternative: Upgrade API Token

If you want full automation later:

1. Go to: <https://dash.cloudflare.com/profile/api-tokens>
2. Find your token or create a new one
3. Required permissions:
   - **Account → Cloudflare Pages → Edit** (currently you have Read)
   - **Zone → DNS → Edit**
   - **Zone → Cache Purge → Purge**
4. Save the new token
5. Run: `$env:CLOUDFLARE_API_TOKEN = "new-token"; .\bind_domain_api.ps1`

## Current Status

✅ Backend deployed: <https://quotegenie-api.fly.dev>
✅ Frontend deployed: <https://estimategenie.pages.dev> (correct desktop site)
⏳ Custom domain: <www.estimategenie.net> (still showing mobile - needs binding)

Once you complete the manual binding above, the production site will be live!
