# EstimateGenie - Complete Setup Guide

This repository contains the static website and documentation for EstimateGenie, the AI-powered estimation platform.

---

## 🚀 Quick Start

### Prerequisites

- Node.js v16+ (for Wrangler CLI deployment)
- Cloudflare account
- estimategenie.net domain (configured on Cloudflare)

### Local Development

Open `index.html` in your browser, or use a simple HTTP server:

```powershell
# Python 3
python -m http.server 8000

# Node.js
npx http-server -p 8000
```

Visit: <http://localhost:8000>

---

## 📦 Project Structure

```
quoteGenie/
├── index.html              # Landing page
├── features.html           # Features overview
├── about.html             # Company info
├── blog.html              # Blog/updates
├── case-studies.html      # Customer success stories
├── contact.html           # Contact form
├── dashboard.html         # User dashboard mockup
├── docs.html              # Developer API documentation
├── robots.txt             # SEO robots file
├── sitemaps.xml           # Sitemap for search engines
├── assets/
│   └── css/
│       └── main.css       # Centralized styles
├── AI_STACK.md            # Backend AI architecture guide
└── DEPLOY_CLOUDFLARE.md   # Deployment instructions
```

---

## 🌐 Deploy to Cloudflare Pages

### Option 1: Dashboard Upload

1. Go to Cloudflare Dashboard → Pages → Create Project
2. Upload the entire project folder
3. Name: `estimategenie`
4. No build settings needed (static site)
5. Attach custom domain: `estimategenie.net`

### Option 2: Wrangler CLI (Recommended)

```powershell
# Install Wrangler
npm install -g wrangler

# Authenticate
wrangler login

# Deploy
wrangler pages deploy . --project-name=estimategenie
```

See [DEPLOY_CLOUDFLARE.md](DEPLOY_CLOUDFLARE.md) for detailed instructions.

---

## 🔧 DNS Configuration

### Cloudflare DNS Records

| Name | Type | Value | Proxy |
|------|------|-------|-------|
| @ | CNAME | estimategenie.pages.dev | Proxied (orange) |
| www | CNAME | estimategenie.pages.dev | Proxied (orange) |

### SSL/TLS Settings

- Mode: Full (strict)
- Always Use HTTPS: On
- HSTS: Enabled
- Redirect: www → apex (301)

---

## 📧 Email Configuration

### Receiving (Cloudflare Email Routing)

1. Cloudflare Dashboard → Email → Email Routing
2. Add rule: `hello@estimategenie.net` → forward to your inbox

### Sending (Microsoft 365/Outlook)

Add these DNS records:

| Name | Type | Value |
|------|------|-------|
| @ | TXT | `v=spf1 include:spf.protection.outlook.com -all` |
| selector1._domainkey | CNAME | `selector1-<initialDomain>._domainkey.estimategenie.net.` |
| selector2._domainkey | CNAME | `selector2-<initialDomain>._domainkey.estimategenie.net.` |
| _dmarc | TXT | `v=DMARC1; p=quarantine; rua=mailto:postmaster@estimategenie.net` |
| @ | MX | `estimategenie-net.mail.protection.outlook.com` |

---

## 🧪 Verification

### DNS

```powershell
Resolve-DnsName estimategenie.net
Resolve-DnsName www.estimategenie.net
```

### HTTP/HTTPS

```powershell
curl -I http://estimategenie.net
curl -I https://estimategenie.net
curl -I https://www.estimategenie.net
```

Expected:

- HTTP → 301 redirect to HTTPS
- HTTPS → 200 OK with Cloudflare certificate
- www → 301 redirect to apex

---

## 🤖 AI Backend Stack

The AI estimation engine uses:

- **Vision**: GroundingDINO, SAM, YOLO, Depth Anything
- **Reasoning**: LLaVA, Llama 3, LangChain
- **Infrastructure**: FastAPI, Ollama, PostgreSQL
- **Model Storage**: HuggingFace models with SD card support

### Quick Links

- [AI_STACK.md](AI_STACK.md) – Complete AI architecture and implementation
- [MODELS_GUIDE.md](MODELS_GUIDE.md) – Model download, SD card setup, and Docker deployment

### Quick Model Setup

```powershell
# 1. Configure SD card storage (Windows)
.\setup_sdcard.ps1

# 2. Download a lightweight model
D:/sd/Scripts/python.exe download_models.py --model tinyllama

# 3. Start model server
docker-compose --profile models up tinyllama

# 4. Verify
D:/sd/Scripts/python.exe scripts/healthcheck_models.py
```

See [MODELS_GUIDE.md](MODELS_GUIDE.md) for the complete guide.

---

## 🎨 Branding

- **Product Name**: EstimateGenie
- **Domain**: estimategenie.net
- **API Base**: <https://api.estimategenie.net>
- **Support Email**: <hello@estimategenie.net>
- **SDK Package**: estimategenie-js

---

## 📝 Pages & Content

- **index.html**: Landing page with hero, features, pricing, testimonials
- **features.html**: Detailed feature breakdown and pricing tables
- **about.html**: Company mission, values, team, investors
- **blog.html**: Content hub with articles and updates
- **case-studies.html**: Customer success stories with ROI metrics
- **docs.html**: Developer documentation with API endpoints, SDKs, best practices, AI building blocks
- **contact.html**: Contact form, FAQ, partnership info
- **dashboard.html**: Authenticated user dashboard mockup with Chart.js
- **mobile-index.html**: Mobile-optimized quote generation with advanced options (quality, contingency, profit, region)

### Advanced Quote Options

The mobile quote flow now supports customization via advanced options:

- **Material Quality**: Standard (1.0x), Premium (1.3x), Luxury (1.8x) pricing
- **Contingency**: 0-30% buffer for unexpected costs
- **Profit Margin**: 0-50% contractor markup
- **Region**: Labor rate adjustments (South 0.85x, Midwest 1.0x, Northeast 1.25x, West 1.35x)

See [docs/ADVANCED_OPTIONS.md](docs/ADVANCED_OPTIONS.md) for detailed API reference.

---

## 🔒 Security & Performance

- **SSL/TLS**: Full (strict) mode with HSTS
- **CDN**: Cloudflare global edge network
- **Caching**: Static assets cached at edge
- **DDoS Protection**: Cloudflare automatic mitigation
- **Bot Protection**: Optional Bot Fight Mode

---

## 🐛 Troubleshooting

### DNS_PROBE_FINISHED_NXDOMAIN

- Check nameservers at registrar point to Cloudflare
- Verify DNS records in Cloudflare dashboard
- Wait up to 24 hours for propagation

### SSL Certificate Errors

- Set SSL/TLS mode to "Full (strict)"
- Enable "Always Use HTTPS"
- Clear browser cache

### Email Not Working

- Verify MX, SPF, DKIM, DMARC records
- Enable DKIM signing in Microsoft 365 portal
- Test with <https://www.mail-tester.com/>

---

## 📚 Additional Resources

- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [Wrangler CLI Guide](https://developers.cloudflare.com/workers/wrangler/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Feather Icons](https://feathericons.com/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)

---

## 🤝 Contributing

This is a private project. For questions or issues, contact: <hello@estimategenie.net>

---

## 📄 License

© 2025 EstimateGenie, Inc. All rights reserved.

---

**Last Updated**: October 20, 2025
