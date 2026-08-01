# Contributing to ABC Compliance Platform

Thank you for your interest in contributing! This project follows a standard open-source workflow with a few project-specific conventions.

---

## 🛠 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### One-Time Setup
```bash
# Clone & enter
git clone https://github.com/AshayK003/ABC-Compliance-Platform.git
cd ABC-Compliance-Platform

# Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install

# Frontend
cd frontend
npm install
cd ..

# Infrastructure
docker compose up -d db redis
cp .env.example .env               # edit DATABASE_URL if needed
alembic upgrade head
```

### Verify Setup
```bash
# Backend tests
pytest -q                          # 71 passed

# Frontend checks
cd frontend
npm run lint
npm run typecheck
npm run build
```

---

## 📋 Code Style

### Backend (Python)
```bash
# Format
black src tests
isort src tests

# Lint
flake8 src tests
mypy src

# Pre-commit runs all above automatically
```
**Standards:**
- Black (line-length 100)
- isort (black profile)
- flake8 (E, F, W, B, C90, I)
- mypy (strict, ignore-missing-imports)

### Frontend (TypeScript/React)
```bash
cd frontend

# Format + Lint
npm run lint          # ESLint + Prettier

# Typecheck
npm run typecheck     # tsc --noEmit
```
**Standards:**
- ESLint (Airbnb + TypeScript recommended)
- Prettier (single quotes, trailing commas, 100 char)
- TypeScript strict mode

---

## 🌿 Branch & Commit Conventions

### Branch Naming
```
<type>/<short-description>

# Examples
feat/centre-search-filter
fix/auth-refresh-token-expiry
chore/update-dependencies
docs/update-readme
refactor/cache-invalidation
test/add-fund-tracker-tests
```

### Commit Messages (Conventional Commits)
```
<type>(<scope>): <short description>

<body (optional)>

<footer (optional)>

# Types: feat, fix, chore, docs, refactor, test, perf, build, ci, revert
# Examples:
feat(centres): add district filter to list endpoint
fix(auth): handle expired refresh token gracefully
test(funds): add allocation balance validation test
chore(deps): update fastapi to 0.115.0
```

---

## 🔁 PR Workflow

### Before Opening a PR
1. **Run full test suite locally:** `pytest -q` (backend) + `npm run lint && npm run typecheck && npm run build` (frontend)
2. **Update tests** for new behavior
3. **Update docs** if API contracts or env vars change
4. **Rebase** on `main` (not merge)
5. **Squash** related commits into logical units

### PR Requirements
- [ ] All CI checks pass (GitHub Actions)
- [ ] At least 1 review from maintainer
- [ ] No merge conflicts
- [ ] Descriptive title + body (what, why, how)
- [ ] Linked issue (if applicable): `Closes #123`

### Review Checklist (for reviewers)
- [ ] Code follows style guides
- [ ] Tests cover new logic (auth, validation, error paths)
- [ ] No hardcoded secrets or debug logs
- [ ] Database migrations are expand-contract safe
- [ ] API changes are backward-compatible or versioned
- [ ] Frontend builds without warnings

---

## 🧪 Testing Requirements

### Backend
```bash
# Unit + Integration
pytest -q

# With coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```
**Required test coverage:**
- Auth: 401/403/422 paths, token refresh, logout, delete account
- Validation: 422 for invalid input on every POST/PATCH
- Rate limiting: 429 after threshold
- Error handling: 500 returns generic message
- Business logic: expense validation, allocation balance

### Frontend
```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

---

## 🗄 Database Migrations

### Creating a Migration
```bash
# After model changes in src/models/base.py
alembic revision --autogenerate -m "descriptive message"

# Review the generated file in alembic/versions/
# Apply
alembic upgrade head
```

### Migration Rules (Expand-Contract Pattern)
| ❌ Never Do | ✅ Always Do |
|-------------|--------------|
| Drop a column | Add new column (nullable or with default) |
| Rename a column | Add new column, backfill, deploy, then drop old |
| Change column type | Add new column with new type, backfill, deploy, drop old |
| Add NOT NULL without default | Add nullable, backfill, then ALTER COLUMN SET NOT NULL |

---

## 📦 Dependency Management

### Backend
```bash
# Add dependency
pip install package-name
pip freeze > requirements.txt   # or update pyproject.toml

# Audit
pip-audit
```

### Frontend
```bash
cd frontend
npm install package-name
npm audit --audit-level=high
```

**Policy:** Prefer stdlib / minimal deps. Justify any heavy dependency in PR.

---

## 🐛 Bug Reports

Use the **Bug Report** issue template. Include:
- Environment (OS, Python/Node versions, Docker)
- Steps to reproduce (minimal)
- Expected vs actual behavior
- Logs / screenshots
- `pytest` output if test-related

---

## ✨ Feature Requests

Use the **Feature Request** issue template. Include:
- Problem statement (what user pain does this solve?)
- Proposed solution (API + UI sketch if applicable)
- Alternatives considered
- Impact on existing modules

---

## 🔒 Security Issues

**Do not open public issues** for security vulnerabilities.

Email: `security@ashayk.com` (or use GitHub Security Advisories)

Include:
- Description of vulnerability
- Impact assessment
- Proof of concept (if safe)
- Suggested fix

---

## 📄 License

By contributing, you agree that your contributions will be licensed under **AGPL v3** (same as the project).

---

## 🙋 Questions?

- **Discord:** [Project Discord](https://discord.gg/placeholder)
- **Discussions:** [GitHub Discussions](https://github.com/AshayK003/ABC-Compliance-Platform/discussions)
- **Maintainer:** Ashay Kushwaha (@AshayK003)