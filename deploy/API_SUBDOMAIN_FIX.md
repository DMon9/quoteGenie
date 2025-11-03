# API Subdomain Setup - Quick Fix

## Issue

`api.estimategenie.net` returns **DNS_PROBE_FINISHED_NXDOMAIN** because the DNS record doesn't exist yet.

## Solution

You need to create a DNS record in Cloudflare pointing `api` to your Fly.io backend.

---

## Step-by-Step Fix (5 minutes)

### Option 1: Direct CNAME to Fly.io (Recommended)

1. **Go to Cloudflare Dashboard**
   - Navigate to: <https://dash.cloudflare.com>
   - Select your domain: `estimategenie.net`

2. **Add DNS Record**
   - Click **DNS** in the left sidebar
   - Click **Add record**

3. **Configure CNAME**

   ```
   Type:    CNAME
   Name:    api
   Target:  quotegenie-api.fly.dev
   Proxy:   ❌ DNS only (grey cloud OFF) — temporarily while issuing origin TLS cert
   TTL:     Auto
   ```

4. **Save**
   - DNS propagates in ~1 minute (Cloudflare is fast)

5. **Issue TLS certificate at origin (Fly.io)**

   The origin (Fly.io) must present a certificate for `api.estimategenie.net`.

   ```powershell
   # Install and login to Fly CLI if not already
   flyctl auth login

   # From your backend project (or any directory)
   # Create a certificate for the custom domain
   flyctl certs add api.estimategenie.net

   # Verify status until it's "Ready" (may take a few minutes)
   flyctl certs show api.estimategenie.net
   flyctl certs list
   ```

   Notes:
   - Keep Cloudflare proxy OFF (grey) during issuance so ACME validation reaches the origin.
   - Your CNAME to `quotegenie-api.fly.dev` is fine for a subdomain; no static IP needed.

6. **Re-enable Cloudflare proxy (optional, after cert is Ready)**
   - Switch the `api` record back to Proxied (orange cloud) if you want Cloudflare in front.
   - Cloudflare will now be able to complete SSL to your origin without 525.

7. **Test**

   ```powershell
   # Wait 60 seconds, then:
   curl.exe -I https://api.estimategenie.net/health
   ```

   Expected: `HTTP/1.1 200 OK` or `HTTP/1.1 405 Method Not Allowed`

   If you need to confirm backend health while certs are issuing:

   ```powershell
   # Direct origin health (bypasses custom domain cert mismatch)
   curl.exe -I https://quotegenie-api.fly.dev/health

   # Temporarily ignore certificate errors to validate connectivity (use only for debugging)
   curl.exe -vkI https://api.estimategenie.net/health
   ```

---

### Option 2: Via Cloudflare Worker Proxy (Alternative)

If you want the Worker to handle API routing:

1. **Deploy the Worker**

   ```powershell
   cd api-worker
   wrangler deploy
   ```

2. **Add Custom Domain to Worker**
   - Cloudflare Dashboard → Workers & Pages
   - Select your worker
   - Click **Triggers** tab
   - Under **Custom Domains**, click **Add Custom Domain**
   - Enter: `api.estimategenie.net`
   - Save

3. **Bind Custom Domain instead of DNS CNAME**
   - When you add a custom domain to a Worker, Cloudflare terminates TLS at the edge.
   - You do NOT need a Fly.io certificate for `api.estimategenie.net` in this mode.

4. **Test**

   ```powershell
   curl.exe -I https://api.estimategenie.net/health
   ```

---

## Quick Verification

After adding the DNS record, run these checks:

```powershell
# 1. DNS resolution
nslookup api.estimategenie.net

# 2. HTTP health check
curl.exe -I https://api.estimategenie.net/health

# 3. Full health response
curl.exe https://api.estimategenie.net/health

# 4. Test CORS (from browser console on estimategenie.net)
fetch('https://api.estimategenie.net/health').then(r => r.json()).then(console.log)
```

---

## Temporary Workaround (While DNS Propagates)

If you want to test the frontend now before DNS is ready:

### Use the Fly.io hostname directly

Update `assets/js/api-config.js` temporarily:

```javascript
// Line 13: Change default
const DEFAULT_API_BASE = 'https://quotegenie-api.fly.dev';
```

Or override in browser console:

```javascript
localStorage.setItem('API_BASE_URL', 'https://quotegenie-api.fly.dev');
location.reload();
```

Or use URL parameter:

```
https://www.estimategenie.net/login.html?api=https://quotegenie-api.fly.dev
```

---

## Why This Happened

The frontend code was updated to use `https://api.estimategenie.net`, but the DNS infrastructure wasn't updated yet. This is normal—code changes are instant, DNS changes require manual setup in Cloudflare.

---

## Expected Timeline

- **DNS Record Creation**: 2 minutes (manual)
- **DNS Propagation**: 1-5 minutes (Cloudflare is fast)
- **SSL Certificate**: Automatic (Cloudflare)
- **Total**: ~5-10 minutes

---

## After DNS is Working

Once `api.estimategenie.net` resolves:

1. ✅ Test all auth endpoints (login, register, me)
2. ✅ Test quote generation
3. ✅ Update Stripe webhook to `https://api.estimategenie.net/api/v1/webhooks/stripe`
4. ✅ Deploy backend with updated CORS (if not already done)

---

## Need Help?

If Cloudflare DNS setup is unclear, I can provide:

- Screenshots walkthrough
- Alternative DNS providers (if not using Cloudflare)
- Direct backend URL override for immediate testing

---

**Next Action**: Add the CNAME record in Cloudflare DNS (see Option 1 above)
