---
name: run-android-autotests
description: |
  Launch, smoke-test, and drive the Android-AutoTests platform (Django + Vue).
  Use when asked to run, start, restart, check status, take screenshots, or verify the
  platform is healthy after code changes. Covers all 3 services: Redis, Django backend,
  and Vue frontend. AgentScope runs in-process inside Django.
---

# Run: Android-AutoTests

AI-driven Android UI automation test platform. Three services: Redis (`:6379`),
Django backend (`:8766`, with AgentScope in-process), Vue frontend (`:5173`).

All paths below are relative to the repo root.

## Prerequisites

All three are required. The platform will not start if any is missing.

```bash
python --version   # >= 3.10
node --version     # >= 18
npm --version      # >= 9
redis-cli ping     # Redis must be running
```

MySQL (or SQLite) with a database named `android_autotests`. If using MySQL,
the default credentials are `autotests / autotests2026` (configurable via `.env`).

## Setup (first time only)

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Database
python manage.py migrate
python manage.py createsuperuser   # or use admin/admin123 if auto-created

# 3. Configure .env (copy from .env.example if needed)
# Key settings: DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DJANGO_SECRET_KEY
```

## Run (agent path)

### Smoke test (fast — use this first after any change)

```bash
python .claude/skills/run-android-autotests/driver.py --verbose
```

This checks all 3 services, auth, key API endpoints, and frontend — exit code 0
on success. Run it after Django model/view changes or after `npm run build`.

### Launch platform

```bash
python run.py start           # all 3 services (dependency order: redis → backend → frontend)
python run.py status          # check what's running
python run.py restart         # restart all (stops → 2s wait → start)
python run.py logs            # tail last 20 lines of each service log
```

### Stop

```bash
python run.py stop            # stop all except Redis
python run.py stop frontend   # stop one service
```

### Drive the browser

After launch, use Playwright MCP tools (already available in Claude Code) to
interact with the app at `http://localhost:5173`.

**Auth** — get a JWT token for API calls:
```bash
curl -s -X POST http://127.0.0.1:8766/api/ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Key routes:**

| Path | Module |
|------|--------|
| `/dashboard` | Dashboard (home) |
| `/devices` | Device management |
| `/elements` | Element locator |
| `/cases` | Case manager |
| `/runner` | Test runner / execution engine |
| `/reports` | Report generator |
| `/ai-assistant` | AI assistant |
| `/workflow` | Workflow workbench |
| `/login` | Login page |

**API base:** `http://localhost:8766/api/`
**Django admin:** `http://localhost:8766/admin/`

A typical Playwright MCP interaction to verify the dashboard:
```
nav http://localhost:5173/dashboard
wait-for text=仪表盘
screenshot
console --errors
```

## Run (human path)

```bash
python run.py start
# Open http://localhost:5173 in a browser
# Login: admin / admin123
```

Useful for visual inspection. Useless in headless environments.

## Test

```bash
# Backend
python manage.py test

# Frontend
cd frontend && npx vite build --mode development 2>&1 | tail -10
```

There is no full e2e suite. The driver above is the integration smoke test.

## Gotchas

- **Django restart required after model/route changes.** New routes and
  migrations are invisible to a running Daphne server. `python run.py restart
  backend` after any `models.py` or `urls.py` change.
- **AgentScope runs in-process.** It depends on Redis for message bus. If Redis is
  down, AI features won't work. `redis-cli ping` first.
- **MySQL required by default.** `run.py` sets `DB_ENGINE=mysql`. For SQLite,
  set `DB_ENGINE=sqlite` before launching, or edit `run.py`'s `BASE_ENV`.
- **Frontend dev server is Vite.** It compiles routes on demand — the first
  page load after `run.py start` can take 10s+. Wait for the dashboard to
  render before interacting.
- **API root requires auth.** `GET /api/` returns 401 without a Bearer token.
  This is expected. Use the login endpoint to get a token.
- **Vue SPA routing.** Direct URL navigation requires the Vite dev server.
  `/devices` works; `/device-pool` gives 404 (SPA routes don't match
  filesystem paths).
- **Default credentials** are `admin / admin123`. Created by the platform seed
  data, not `createsuperuser`. Check the `.env` file for `PLATFORM_ADMIN_*`
  variables.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| AgentScope won't work | `redis-cli ping` — if Redis is down, start it first |
| `Port already in use` | `python run.py stop` then `python run.py start` |
| Django 500 after migration | Check `logs/backend.log` — often a missing column or unapplied migration |
| Frontend white screen | Wait 5s for Vite HMR, hard-refresh. Check `logs/frontend.log` |
| API 401 on all calls | Token expired — re-login. Token TTL is 1 hour (`JWT_ACCESS_TTL`) |
| `no such table` | `python manage.py migrate` — migrations not applied |
| `database is locked` (SQLite) | `python run.py restart` — SQLite doesn't handle concurrent writes well |
| AI `ModuleNotFoundError` | `pip install -r requirements.txt` — dependency missing |
