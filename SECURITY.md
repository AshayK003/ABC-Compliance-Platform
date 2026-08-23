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
  centre-scoping on entity writes (dogs, surgeries, inspections, expenses).
- **Account lifecycle:** Deletion deactivates rather than hard-deletes,
  preserving the surgical/audit history that references the staff record.
- **Secrets:** All configuration via environment variables. `SECRET_KEY` is
  validated at startup (minimum 32 bytes, default value rejected).
- **Rate limiting:** slowapi on auth and public endpoints.
- **Headers:** HSTS, CSP, X-Frame-Options, nosniff, strict Referrer-Policy.

Dependency audit runs in CI (`pip-audit`, `npm audit --audit-level=high`).
