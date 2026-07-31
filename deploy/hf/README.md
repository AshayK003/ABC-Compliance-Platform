---
title: ABC Compliance Platform
emoji: 🐕
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8080
pinned: false
---

# ABC Compliance Platform

Digital compliance infrastructure for Animal Birth Control (ABC) centres under the Supreme Court-mandated ABC Rules 2023.

Live demo of the backend API. Track surgeries, run surprise inspections, follow the fund trail, and generate compliance reports.

## Local development

```bash
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```
