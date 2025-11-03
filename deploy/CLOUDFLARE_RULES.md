# Cloudflare Rules for EstimateGenie

This file captures the exact steps to resolve the 522 on the apex domain and set a clean, canonical routing setup.

---

## Goal
- Make `https://estimategenie.net` always redirect to `https://www.estimategenie.net` (canonical)
- Keep the site hosted on Cloudflare Pages
- Serve API on `https://api.estimategenie.net`

---

## 1) Redirect apex → www (instant fix)
Use a Redirect Rule so Cloudflare handles it before contacting any origin.

Steps:
1. Cloudflare Dashboard → Rules → Redirect Rules → Create rule
2. Expression (simple):
   - If Hostname equals `estimategenie.net`
3. Then: Static redirect
   - URL: `https://www.estimategenie.net/$1`
   - Status: `301` (Permanent)
4. Save and enable.

Verify (PowerShell):
```powershell
curl.exe -I https://estimategenie.net
# Expect: HTTP/1.1 301 ... Location: https://www.estimategenie.net/
```

---

## 2) Optional: Map apex directly to Pages
Only if you want the apex to serve the site without redirect.

Steps:
1. Pages → Your project → Custom domains → Add domain → `estimategenie.net`
2. DNS → Remove any A/AAAA records for `@` (root) that point elsewhere
3. Ensure a proxied CNAME (flattened) is created to your `<project>.pages.dev` target
4. Wait a few minutes and verify:
```powershell
curl.exe -I https://estimategenie.net
# Expect: HTTP/1.1 200 OK
```

Note: Use either apex or www as canonical; keep the other redirecting to it.

---

## 3) Ensure Workers do not intercept the root
If you use a Worker as an API proxy, bind it only to the API subdomain.

Steps:
- Workers → Your worker → Triggers → Routes
- Remove any `estimategenie.net/*` route unless intentionally intercepting the whole site
- Add route: `api.estimategenie.net/*`

---

## 4) API subdomain (`api.estimategenie.net`)
Point to your backend host (Fly.io, Render, or Worker proxy).

Option A: Direct to Fly app
- DNS → Add CNAME
  - Name: `api`
  - Target: `quotegenie-api.fly.dev`
  - Proxy status: Proxied (orange cloud)

Option B: Via Worker proxy
- Workers → Bind route `api.estimategenie.net/*`
- Set `BACKEND_URL` to your backend base URL (e.g., `https://quotegenie-api.fly.dev`)

Update backend CORS (ALLOW_ORIGINS) to include:
```
https://www.estimategenie.net,https://estimategenie.net,https://api.estimategenie.net,https://estimategenie.pages.dev
```

---

## 5) Validation checklist
- `https://estimategenie.net` → 301 to `https://www.estimategenie.net`
- `https://www.estimategenie.net` → 200 OK (Pages)
- `https://api.estimategenie.net/health` → 200 OK (backend)
- Frontend calls use `https://api.estimategenie.net`

---

## 6) Rollback
- Disable the Redirect Rule to temporarily test apex
- Restore old DNS records if needed (not recommended)

