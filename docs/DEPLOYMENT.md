# Deployment

The backend runs on **Northflank** (Docker, free tier, no credit card) with **Neon Postgres** (free, no card).
The frontend is served on **Vercel** (free, no card).
Keep-alive: **UptimeRobot** free (5-min HTTP checks on `/health`) — keeps the Northflank service warm even when your laptop is off.
The production contract target remains self-hostable on NIC cloud.gov.in; this demo stack is proof-only.

## Backend (Northflank)

### Prerequisites
- GitHub account
- Northflank account (free, no card — https://northflank.com)
- Neon Postgres project (free, no card — https://neon.tech)

### One-time setup
1. **Neon** → create project `abc` → region **Singapore** (closest to India) → copy pooled connection string → transform:
   ```
   postgresql+asyncpg://neondb_owner:<password>@<host>-pooler.<region>.aws.neon.tech/neondb?sslmode=require
   ```
2. **Northflank** → **New Service** → connect this GitHub repo → **Docker** → free tier
   - Build command: (empty — uses Dockerfile)
   - Start command: (empty — uses Dockerfile CMD)
   - Environment variables (Service → Environment):
     - `DATABASE_URL` — your transformed Neon URL
     - `SECRET_KEY` — generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
     - `ALLOWED_ORIGINS` — JSON list: `["https://<your-vercel-app>.vercel.app"]`
3. **UptimeRobot** (free) → add monitor on `https://<your-northflank-app>.northflank.app/health` → interval 5 min
   - This pings 288×/day, keeping the free Northflank service (15-min spin-down) permanently warm

### How it works
- Push to `master` → GitHub Actions runs tests → Northflank auto-deploys the new image
- Dockerfile runs `alembic upgrade head` on start → fresh DB auto-migrates
- Health endpoint at `/health` → UptimeRobot keeps it warm

## Frontend (Vercel)

1. Vercel → **Add New → Project** → import this repo → framework **Vite**
2. Root directory: `frontend`
3. Environment Variable (build-time): `VITE_API_URL` = `https://<your-northflank-app>.northflank.app`
4. Deploy
5. Update Northflank's `ALLOWED_ORIGINS` with the Vercel URL, redeploy

## Local development

```bash
cd D:/Personal\ projects/ABC-Compliance-Platform
docker compose up  # if you have docker-compose.yml
# or
DATABASE_URL=... SECRET_KEY=... ALLOWED_ORIGINS='["http://localhost:5173"]' python -m uvicorn src.main:app --reload
```

## Verification

```bash
curl https://<your-northflank-app>.northflank.app/health
# {"status":"ok","version":"0.1.0"}
```