# Deployment

The backend runs on a **Hugging Face Spaces Docker space** (free tier, no credit card).
The frontend is served separately on Vercel. The production contract target remains
self-hostable infrastructure (NIC cloud.gov.in) — this deployment is the live demo.

## Architecture

| Layer | Where | Cost |
|-------|-------|------|
| Backend (FastAPI, Docker) | HF Spaces Docker space | Free (2 vCPU / 16 GB) |
| Database (PostgreSQL) | Neon free tier | Free (0.5 GB, no credit card) |
| Frontend (React) | Vercel | Free |

The Space suspends after ~48 h of inactivity. A keep-alive ping to `/health` every
24 h keeps it warm so the demo link is always responsive.

## One-time setup

1. **Create the Space** at https://huggingface.co/new-space — name it
   `abc-compliance`, set SDK to **Docker**.
2. **Create a token** at https://huggingface.co/settings/tokens with **write access
   to Spaces**.
3. **Add GitHub secrets/variables** (Settings → Secrets and variables → Actions):
   - Secret `HF_TOKEN` — the token from step 2
   - Variable `HF_SPACE_ID` — `AshayK003/abc-compliance`
4. **Add Space secrets** (Space Settings → Variables and secrets):
   - `DATABASE_URL` — Neon pooled connection string
     (`postgresql+asyncpg://...@...neon.tech/...?sslmode=require`)
   - `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `ALLOWED_ORIGINS` — your Vercel frontend URL, **JSON list format**:
     `["https://your-frontend.vercel.app"]` (a plain string crashes the app —
     pydantic-settings parses list fields as JSON)
5. **Push to master.** CI runs tests, then the deploy job uploads the app to the
   Space. The Space rebuilds and runs `alembic upgrade head` before starting.

## Deploying manually

```bash
HF_TOKEN=... HF_SPACE_ID=... python scripts/deploy_hf.py
```

## After deploy

- Backend URL: `https://ashayk003-abc-compliance.hf.space`
- Health check: `https://ashayk003-abc-compliance.hf.space/health`
- Point the Vercel frontend at the backend URL and add it to `ALLOWED_ORIGINS`.
