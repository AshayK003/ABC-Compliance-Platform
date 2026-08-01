# Deployment Guide

## Overview

This guide covers deploying the ABC Compliance Platform to production environments. The platform supports multiple deployment targets with a focus on free-tier friendly options for civic-tech / public-sector use cases.

---

## Architecture Recap

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UptimeRobot (5-min ping)                      │
└─────────────────────────────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
┌───────────────────┐ ┌───────────────────┐
│  HF Spaces        │ │     Vercel        │
│  (Docker)         │ │   (Static)        │
│  Backend API      │ │  Frontend SPA     │
│  :8000            │ │  + /api proxy     │
└───────────────────┘ └───────────────────┘
          │                   │
          └─────────┬─────────┘
                    ▼
          ┌───────────────────┐
          │   Neon Postgres   │
          │  (Serverless)     │
          └───────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │   Upstash Redis   │
          │   (Free Tier)     │
          └───────────────────┘
```

---

## Prerequisites

### Accounts Required
- **GitHub** — source code, CI/CD, container registry
- **Hugging Face** — Spaces (Docker) for backend
- **Vercel** — frontend hosting
- **Neon** — serverless Postgres
- **Upstash** — serverless Redis (optional, for rate limiting / cache)
- **UptimeRobot** — keep-alive monitoring

### Local Tools
- Docker & Docker Compose
- Git
- `hf` CLI (optional): `pip install huggingface_hub[cli]`
- `vercel` CLI (optional): `npm i -g vercel`

---

## 1. Database — Neon Postgres

### Create Project
1. Go to [neon.tech](https://neon.tech) → New Project
2. Name: `abc-compliance`
3. Region: Choose closest to your users (e.g., `ap-south-1` for India)
3. Copy connection string: `postgresql://user:pass@ep-xxx.neon.tech/abc_dashboard?sslmode=require`

### Configure for asyncpg
Neon uses `sslmode=require&channel_binding=require` which asyncpg doesn't accept directly. Transform in your env:

```bash
# Original from Neon
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/abc_dashboard?sslmode=require&channel_binding=require"

# Transform for asyncpg (drop channel_binding, sslmode→ssl)
DATABASE_URL="postgresql+asyncpg://user:pass@ep-xxx.neon.tech/abc_dashboard?ssl=require"
```

### Run Migrations
```bash
# Local with Neon URL
DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
```

---

## 2. Cache — Upstash Redis (Optional but Recommended)

### Create Database
1. Go to [upstash.com](https://upstash.com) → New Redis Database
2. Name: `abc-compliance-cache`
3. Region: Same as Neon
4. Type: Free tier (100MB, 10K commands/day)
5. Copy `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`

### Environment Variables
```bash
REDIS_URL="redis://default:token@host:port"  # or use REST API in code
```

---

## 3. Backend — Hugging Face Spaces (Docker)

### Create Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Owner: your account/org
3. Name: `abc-compliance-api`
4. SDK: **Docker**
4. Hardware: **CPU Basic** (free)
5. Visibility: **Private** (recommended for civic data)

### Repository Secrets (HF Space Settings → Repository Secrets)
| Secret | Value |
|--------|-------|
| `DATABASE_URL` | Transformed Neon URL (see above) |
| `SECRET_KEY` | 32+ char random string (`openssl rand -hex 32`) |
| `DEBUG` | `false` |
| `REDIS_URL` | Upstash URL (if using) |
| `ALLOWED_ORIGINS` | `["https://your-vercel-app.vercel.app"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `CACHE_ENABLED` | `true` |
| `CACHE_TTL_SECONDS` | `30` |

### Deploy
**Option A: Auto-deploy from GitHub (Recommended)**
1. In Space Settings → **Repository** → Connect to your GitHub repo
2. Set **Branch**: `main`
3. Set **Dockerfile Path**: `Dockerfile`
4. Push to `main` → auto-deploys

**Option B: Manual via `hf` CLI**
```bash
hf space create abc-compliance-api --sdk docker
# Push your repo to the space
git remote add hf https://huggingface.co/spaces/your-user/abc-compliance-api
git push hf main
```

### Verify Deployment
- Space URL: `https://your-user-abc-compliance-api.hf.space`
- Health: `https://your-user-abc-compliance-api.hf.space/health`
- Swagger (dev only): `https://your-user-abc-compliance-api.hf.space/docs`

---

## 4. Frontend — Vercel

### Create Project
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repo
3. Framework Preset: **Vite**
4. Root Directory: `frontend`
5. Build Command: `npm run build`
6. Output Directory: `dist`
7. Install Command: `npm ci`

### Environment Variables (Vercel Project Settings → Environment Variables)
| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-user-abc-compliance-api.hf.space/api/v1` |

### Deploy
- Push to `main` → auto-deploys
- Preview deployments for PRs

### Configure API Proxy (vercel.json)
Create `frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-user-abc-compliance-api.hf.space/api/v1/$1"
    }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "https://your-vercel-app.vercel.app" },
        { "key": "Access-Control-Allow-Credentials", "value": "true" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PATCH,DELETE,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type,Authorization" }
      ]
    }
  ]
}
```

### Update HF Space CORS
In HF Space secrets, update `ALLOWED_ORIGINS`:
```json
["https://your-vercel-app.vercel.app"]
```

---

## 5. Keep-Alive — UptimeRobot

### Create Monitor
1. Go to [uptimerobot.com](https://uptimerobot.com) → Add New Monitor
2. Type: **HTTP(s)**
3. URL: `https://your-user-abc-compliance-api.hf.space/health`
4. Interval: **5 minutes**
5. Alert Contacts: Add your email
6. Status Page: Optional public status page

### Why This Matters
HF Spaces **suspends after 48 hours of inactivity**. UptimeRobot's 5-min ping keeps the space warm.

---

## 6. Environment Variable Reference

### Backend (HF Space Secrets / .env)
```bash
# Required
DATABASE_URL="postgresql+asyncpg://user:pass@ep-xxx.neon.tech/abc_dashboard?ssl=require"
SECRET_KEY="your-32-char-secret"
ALLOWED_ORIGINS='["https://your-vercel-app.vercel.app"]'

# Optional (with defaults)
DEBUG="false"
REDIS_URL="redis://default:token@host:port"
ACCESS_TOKEN_EXPIRE_MINUTES="15"
REFRESH_TOKEN_EXPIRE_DAYS="7"
CACHE_ENABLED="true"
CACHE_TTL_SECONDS="30"
```

### Frontend (Vercel Environment Variables)
```bash
VITE_API_URL="https://your-user-abc-compliance-api.hf.space/api/v1"
```

---

## 7. Dockerfile Reference (Production)

```dockerfile
# Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app

# System deps (for asyncpg, bcrypt, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY . .

# Non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Multi-stage (optional, smaller image):**
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN adduser --disabled-password --gecos '' appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. Post-Deployment Verification

### Checklist
- [ ] `GET https://your-api.hf.space/health` → `{"status":"healthy","checks":{"database":true,"redis":true}}`
- [ ] `POST https://your-api.hf.space/api/v1/auth/login` → returns access_token + sets cookies
- [ ] `GET https://your-api.hf.space/api/v1/centres` → returns centre list
- [ ] Frontend loads at `https://your-app.vercel.app`
- [ ] Login works on frontend
- [ ] Centres page shows seeded data (run `scripts/seed_demo.py` if empty)
- [ ] UptimeRobot shows "UP" status

### Run Seed Data (if needed)
```bash
DATABASE_URL="your-neon-url" python scripts/seed_demo.py
```

---

## 9. Rollback Procedure

### HF Spaces
1. Go to Space → **Settings** → **Repository** → **Build History**
2. Click **Rollback** on previous successful build
3. Or: `git revert <bad-commit> && git push origin main`

### Vercel
1. Go to Project → **Deployments**
2. Click **...** on previous deployment → **Promote to Production**

### Database
- Alembic: `alembic downgrade -1` (if migration was expand-contract safe)
- Neon: Point-in-time restore (last 7 days on free tier)

---

## 10. Cost Summary (Free Tier)

| Service | Free Tier Limits | Monthly Cost |
|---------|------------------|--------------|
| Hugging Face Spaces | 1 CPU, 16GB RAM, 48h idle suspend | $0 |
| Vercel | 100GB bandwidth, unlimited personal projects | $0 |
| Neon Postgres | 0.5 GB storage, 190 hrs compute/mo | $0 |
| Upstash Redis | 100MB, 10K commands/day | $0 |
| UptimeRobot | 50 monitors, 5-min intervals | $0 |
| **Total** | | **$0/month** |

---

## 11. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `503 Service Unavailable` | Space suspended | Check UptimeRobot; manual wake via HF Space "Restart" |
| `CORS error` | Origin not in `ALLOWED_ORIGINS` | Add Vercel URL to HF Space secrets |
| `DB connection failed` | Wrong `DATABASE_URL` format | Use `ssl=require` not `sslmode=require`; drop `channel_binding` |
| `Redis connection failed` | Upstash URL wrong | Use REST API or standard `redis://` with token |
| `401 on valid token` | Clock skew / secret mismatch | Ensure `SECRET_KEY` matches; check token expiry |
| `422 on valid payload` | Pydantic validation | Check field types (Decimal vs float, date strings) |

---

## 12. Security Checklist (Pre-Production)

- [ ] `SECRET_KEY` is 32+ chars, not default
- [ ] `DEBUG=false` in production
- [ ] `ALLOWED_ORIGINS` only includes production frontend
- [ ] `SECURE=true` on cookies (HF Spaces uses HTTPS)
- [ ] CSP headers strict in prod (no `unsafe-inline/eval`)
- [ ] Rate limits enabled on auth endpoints
- [ ] Swagger/docs disabled in prod (`DEBUG=false`)
- [ ] Health endpoint returns minimal info
- [ ] No `.env` committed to git
- [ ] Dependabot/Renovate enabled for vulnerability alerts