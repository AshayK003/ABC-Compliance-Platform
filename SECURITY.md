# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.5.x   | ✅ |
| < 0.5   | ❌ |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report privately via GitHub Security Advisories:
1. Go to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Include: affected endpoint/component, reproduction steps, impact assessment

You will receive an acknowledgment within 72 hours. Fixes are prioritized by
severity and released as soon as practical; you will be credited in the
release notes unless you prefer to remain anonymous.

## Security Model (Summary)

- **Auth:** JWT access tokens (15 min) + refresh tokens (7 days) in `httpOnly`
  `SameSite` cookies; Bearer-header fallback for API clients. Refresh tokens
  are revocable server-side (`token_version` bump on logout/deactivation/
  admin change).
- **Registration:** Self-signup creates *inactive* accounts pending admin
  approval — no instant access to centre data.
- **Authorization:** Role-based (`admin`, `vet`, `surgeon`) plus object-level
  centre-scoping on entity reads and writes (dogs, surgeries, inspections,
  allocations, expenses, complaints). Cross-centre reads return 404 so
  record existence is not leaked; lists are force-scoped to the caller's
  centre. Staff admin endpoints serialise a `StaffOut` view (no password
  hashes). `POST /audit` is admin-only; routine audit events are
  written server-side.
- **Session window:** deactivation/role change revokes refresh tokens
  immediately (`token_version`); outstanding access tokens remain valid up
  to their 15-minute expiry. This short window is an accepted trade-off.
- **Account lifecycle:** Deletion deactivates rather than hard-deletes,
  preserving the surgical/audit history that references the staff record.
- **Secrets:** All configuration via environment variables. `SECRET_KEY` is
  validated at startup (minimum 32 bytes, default value rejected).
- **Rate limiting:** single shared slowapi instance on auth and public
  endpoints (5/min login, 3/hr register, 10/hr complaints); 429 behaviour
  covered by regression tests.
- **CSRF posture:** state-changing endpoints accept JSON bodies only.
  Browsers cannot send cross-site credentialed requests with
  `Content-Type: application/json` without a CORS preflight, which the
  whitelist denies — so cookie-based CSRF is structurally mitigated
  without a token scheme. Revisit with explicit tokens if form-encoded
  or multipart endpoints are ever added.
- **Headers:** HSTS, CSP, X-Frame-Options, nosniff, strict Referrer-Policy.

Dependency audit runs in CI (`pip-audit`, `npm audit --audit-level=high`).
