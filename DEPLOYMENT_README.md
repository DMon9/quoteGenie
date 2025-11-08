# EstimateGenie Deployment (Production)

This guide is a concise checklist to deploy the full site and API reliably.

## 1) Frontend (Cloudflare Pages)

- Repo root is a static site (no build). Deploy the entire repo or the `deploy/` folder to Pages.
- Recommended: deploy the root; `_redirects` is present.
- Set custom domains: `estimategenie.net` and `www.estimategenie.net`.

## 2) Backend API (Docker)

- Location: `backend/`
- Base image: Python 3.11 (slim)
- Health endpoints:
  - `/` root service info
  - `/health` general health
  - `/api/v1/ping` connectivity check

### Environment variables

Copy `backend/.env.example` to `.env` and set:

- API_HOST=0.0.0.0
- API_PORT=8000
- DEBUG=false
- DATABASE_PATH=estimategenie.db
- ALLOW_ORIGINS=<https://estimategenie.net,https://www.estimategenie.net>
- JWT_SECRET_KEY=<long-random-secret>
- STRIPE_SECRET_KEY=<from Stripe>
- STRIPE_WEBHOOK_SECRET=<from Stripe>
- STRIPE_PRICE_ID_PRO_MONTHLY=<from Stripe>
- STRIPE_PRICE_ID_PRO_ANNUAL=<from Stripe>

Optional:

- GOOGLE_API_KEY, LLM_PROVIDER, GEMINI_MODEL
- PRICE_LIST_FILE or PRICE_LIST_FILES

### Run with Docker

```bash
cd backend
cp .env.example .env
# edit .env with real values
docker build -t estimategenie-api:prod .
docker run -p 8000:8000 --env-file .env estimategenie-api:prod
```

### Or with docker-compose (dev profile)

```bash
cd backend
docker compose up --build
```

## 3) DNS & CORS

- Frontend origin(s): <https://estimategenie.net> and <https://www.estimategenie.net>
- API base: <https://api.estimategenie.net>
- Point `api.estimategenie.net` to your backend host and ensure TLS (reverse proxy)
- Ensure ALLOW_ORIGINS includes both frontend origins.

## 4) Payments (Stripe)

- Set all Stripe env vars above.
- Configure webhook in Stripe dashboard to: `https://api.estimategenie.net/api/v1/webhooks/stripe`
- Test flow: register with plan=pro → checkout session created → webhook marks subscription active.
- Check `GET /api/v1/payment/status` returns `{ configured: true }`.

## 5) Post-deploy checks

- `GET https://api.estimategenie.net/health` → 200
- `GET https://api.estimategenie.net/api/v1/ping` → `{ ok: true }`
- Register and login from frontend; verify `Authorization: Bearer` on API requests.
- Upload image on mobile or dashboard flow; ensure a quote response with totals.

## 6) CI

- GitHub Actions workflow `.github/workflows/ci.yml` runs backend tests and lints on PRs and pushes to main.

## 7) Troubleshooting

- 401 on quotes: ensure token/api key header is sent.
- 403 on quotes: plan limit reached; upgrade or reset usage.
- 503 on payments: Stripe env vars missing or not configured.
- CORS errors: set ALLOW_ORIGINS to include production origins.
