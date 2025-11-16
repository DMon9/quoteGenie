# DNS Automation Guide

This guide explains how to automatically align Cloudflare DNS records with your Cloudflare Pages production deployment so the custom domain always serves the latest build.

## Goal

Prevent pinning the custom domain (`estimategenie.net`, `www.estimategenie.net`) to an old hashed Pages deployment by ensuring both CNAMEs target the stable project domain `estimategenie.pages.dev`.

## Why This Matters

Cloudflare Pages creates immutable deployment subdomains (e.g. `8ae3d487.estimategenie.pages.dev`). If your DNS CNAME points at a specific hashed deployment, your site will never update when new productions ship. Pointing to `estimategenie.pages.dev` allows automatic promotion of the latest production build.

## Script Overview

`scripts/update_dns_records.ps1` performs:

1. Fetch zone ID.
2. Ensure apex and `www` CNAMEs point to `estimategenie.pages.dev` (proxied, flattened).
3. Bind apex + www as Pages custom domains if missing.
4. Purge the entire Cloudflare cache.
5. Repeated verification of page titles until the desktop version appears.

## Requirements

- Environment variable `CLOUDFLARE_API_TOKEN` with permissions:
  - Zone:DNS:Edit, Zone:Read, Zone:Cache Purge
  - Pages:Read, Pages:Edit
- PowerShell (Windows or Core)

## Usage

```powershell
# 1. Set token (never commit this value)
$env:CLOUDFLARE_API_TOKEN = "YOUR_TOKEN_HERE"

# 2. Dry run first (no changes)
./scripts/update_dns_records.ps1 -DryRun

# 3. Run with defaults (apply changes)
./scripts/update_dns_records.ps1

# Optional: force update even if records already match
./scripts/update_dns_records.ps1 -Force

# Skip apex binding if already handled manually
./scripts/update_dns_records.ps1 -SkipPagesApexBind
```

## Expected Output (High-Level)

- Confirms zone ID.
- Creates/updates apex CNAME.
- Creates/updates www CNAME.
- Binds domains to Pages project (skips if present).
- Purges cache.
- Runs 6 verification attempts (every ~20s) showing title transitions.

## Success Criteria

Both `https://estimategenie.net/` and `https://www.estimategenie.net/` report a title containing:

```text
Estimation Wizard
```

If still showing the mobile title after all attempts, wait a few minutes and re-run verification or manual `Invoke-WebRequest` checks.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 403 on Pages domain bind | Token missing Pages:Edit | Recreate token with proper perms |
| CNAME not changing | Existing record locked | Use -Force or delete manually in dashboard |
| Title stays mobile | Browser/DNS cache | Force refresh, test from another network, re-purge cache |
| Apex bind fails | Already exists but not returned in list | Verify via Pages UI; use -SkipPagesApexBind |

## Manual Verification

```powershell
(Invoke-WebRequest https://estimategenie.net -UseBasicParsing).Content | Select-String -Pattern '<title>'
(Invoke-WebRequest https://www.estimategenie.net -UseBasicParsing).Content | Select-String -Pattern '<title>'
```

## Next Steps

- Integrate this script into CI (run post successful production deployment).
- Add a lightweight health check script that fails CI if titles don't update within a time window.
- Extend to update additional subdomains (e.g., `beta.estimategenie.net`).

---
Maintainer: Automation subsystem
Version: 1.0
