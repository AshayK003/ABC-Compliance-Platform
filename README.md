# ABC Compliance Platform

Digital compliance infrastructure for Animal Birth Control (ABC) centres under the **Supreme Court-mandated ABC Rules 2023**.

Track surgeries, conduct surprise inspections, manage fund allocation, and generate compliance reports — all from a single platform built for state animal welfare boards and the AWBI.

## Status

Early development — pilot phase for 3 BBMP centres in Karnataka.

## Features

- **Surgery Log** — Offline-first logging of spay/neuter surgeries with dog ID, GPS, photos, vet details, and weight tracking
- **Surprise Inspections** — Inspector mobile workflow with photo evidence, digital sign-off, and auto-generated reports
- **Fund Trail** — End-to-end tracking from central grant → state allocation → surgery-level expense
- **Compliance Dashboard** — Per-centre green/yellow/red status, fund utilisation %, inspection cadence
- **Committee Portal** — High Court–mandated committee view of real-time compliance across all centres
- **Citizen Grievance API** — Public complaint filing with SLA tracking
- **RTI Exports** — One-click compliance data export for Right to Information requests

## Tech Stack (Planned)

| Layer | Choice |
|-------|--------|
| Backend | Python (FastAPI) |
| Frontend | React + Tailwind CSS |
| Database | PostgreSQL |
| Cache | Redis |
| Async | Celery |
| File Storage | MinIO |
| Infrastructure | NIC cloud.gov.in |

## Pilot Architecture

Modular monolith deployed on NIC Kubernetes — single FastAPI service with module boundaries enforced in code, not network. Designed for 500+ centres at launch, with extraction path to microservices if needed.

## Roadmap

| Phase | Timeline | Scope |
|-------|----------|-------|
| Pilot Core | Weeks 1-3 | Auth, centres CRUD, surgery log, basic dashboard |
| Pilot Hardening | Weeks 4-6 | Fund tracking, inspection sign-off, citizen API, RTI exports, Kannada i18n |
| State Rollout | Weeks 7-12 | Multi-tenancy, AWBI national dashboard, bulk onboarding, production deploy |

## License

AGPL v3 — see [LICENSE](LICENSE).
