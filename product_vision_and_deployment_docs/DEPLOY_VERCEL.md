# Deploying ARGUS to Vercel (Frontend + Backend)

ARGUS ships as two independent apps — a Vite/React frontend and a FastAPI backend — so they deploy as **two separate Vercel projects** from the same repo. This guide covers both, plus every environment variable Vercel needs.

> **Read this first — honest limitations of running FastAPI on Vercel:**
> Vercel's Python runtime is serverless (each request spins up a function, no long-lived process). Two things in ARGUS don't naturally fit that model:
> 1. **FortyGuard's submit-and-poll pattern** can take up to `POLL_TIMEOUT_SECONDS` (120s) per call, and a full DISCOVER scan hits 9 cells. On Vercel Hobby, functions time out at 10s; on Pro, up to 300s with `maxDuration` set explicitly (see below). A full city scan may still need the Pro plan.
> 2. **The in-process `AUTO_SCAN_ENABLED` cron (APScheduler)** requires a persistent process — it will not survive between serverless invocations. Use **Vercel Cron Jobs** instead (covered below) to hit a scan endpoint on a schedule.
>
> If you want zero deployment friction and no plan/timeout tradeoffs, consider Render/Railway/Fly.io for the backend instead, and only put the frontend on Vercel (pointing `vercel.json`'s rewrite at that backend's URL — same rewrite step as below, just a different origin). Everything else in this guide still applies.

---

## 0. Prerequisites

- A **MongoDB Atlas** cluster (Vercel serverless has no local disk/DB — you need a hosted Mongo). Free tier is fine. Grab the connection string (`mongodb+srv://...`).
- Your `FORTYGUARD_API_KEY`, `GROQ_API_KEY` (or `OPENAI_API_KEY` if using OpenAI for the RESPOND stage — ARGUS uses the OpenAI Python SDK pointed at Groq's OpenAI-compatible endpoint).
- The [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`, then `vercel login`.
- Two separate Vercel projects — one for `backend/`, one for `frontend/`. Do **not** try to deploy both from repo root as a single project.

---

## 1. Backend — FastAPI on Vercel

### 1.1 Add the missing dependency
`backend/requirements.txt` doesn't yet list `apscheduler` (used for the optional auto-scan cron) — add it:

```
apscheduler>=3.10.4
```

(If you're following the "skip in-process cron, use Vercel Cron Jobs" recommendation above, you can drop `AUTO_SCAN_ENABLED` entirely and skip this — see §1.4.)

### 1.2 Create a Vercel entrypoint

Vercel's Python runtime looks for an ASGI `app` object exposed from a file under `api/`. Create `backend/api/index.py`:

```python
import sys
from pathlib import Path

# Make argus_agent importable the same way it is when run locally
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from argus_agent.main import app  # noqa: E402

# Vercel's Python runtime imports this module and looks for `app`
```

### 1.3 Add `backend/vercel.json`

```json
{
  "version": 2,
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/index.py" }
  ],
  "functions": {
    "api/index.py": {
      "maxDuration": 300
    }
  }
}
```

`maxDuration: 300` (5 minutes) requires a **Pro** plan — Hobby caps at 10s regardless of this setting. If you're on Hobby, expect single-cell queries to work but a full 9-cell DISCOVER scan to likely time out; consider reducing scan scope or moving the backend off Vercel.

### 1.4 Replace the in-process cron with a Vercel Cron Job (recommended)

Instead of `AUTO_SCAN_ENABLED=true` (which relies on APScheduler staying alive — it won't, on serverless), expose the existing scan logic behind an endpoint and let Vercel's own scheduler call it. Since `POST /api/agent/scan` already takes a `city_id`, the simplest approach is a small wrapper route that loops the 51 cities (reusing `scan_all_cities_background` from `main.py`), then schedule it in `backend/vercel.json`:

```json
{
  "crons": [
    { "path": "/api/cron/scan-all", "schedule": "0 2 * * *" }
  ]
}
```

(Add this alongside the `builds`/`routes`/`functions` keys above — `vercel.json` supports all of them together.) You'll need to add a thin `GET /api/cron/scan-all` route in `routes.py` that calls the same logic as `scan_all_cities_background()`, since Vercel Cron sends a `GET` request, not something your existing `POST /api/agent/scan` per-city endpoint expects. Protect it with a shared secret header if you don't want it publicly triggerable.

### 1.5 Set environment variables (Vercel dashboard or CLI)

In the **backend** Vercel project → Settings → Environment Variables (or via CLI), add:

| Variable | Value | Notes |
|---|---|---|
| `FORTYGUARD_API_KEY` | your key | leave unset to run fully on dummy data |
| `GROQ_API_KEY` | your key | used for the RESPOND-stage LLM calls |
| `OPENAI_API_KEY` | your key | only if you're using OpenAI instead of/alongside Groq |
| `MONGO_URI` | `mongodb+srv://...` | must be Atlas or another hosted Mongo — no local Mongo on Vercel |

CLI equivalent:
```bash
cd backend
vercel link            # first time only, links this folder to a Vercel project
vercel env add FORTYGUARD_API_KEY production
vercel env add GROQ_API_KEY production
vercel env add MONGO_URI production
# repeat for preview/development environments as needed, or select "all" when prompted
```

### 1.6 Deploy

```bash
cd backend
vercel --prod
```

Note the deployment URL Vercel gives you (e.g. `https://argus-backend.vercel.app`) — the frontend needs it next.

---

## 2. Frontend — Vite/React on Vercel

The frontend's `api/client.ts` (and a few components) call relative paths like `fetch("/api/...")`. Locally, `vite.config.ts` proxies `/api` to `http://localhost:8000`. In production on Vercel, that dev-only proxy doesn't exist — so we recreate the same effect with a `vercel.json` rewrite, no source code changes needed.

### 2.1 Create `frontend/vercel.json`

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://YOUR-BACKEND-DEPLOYMENT.vercel.app/api/:path*" }
  ]
}
```

Replace `YOUR-BACKEND-DEPLOYMENT.vercel.app` with the URL from step 1.6 (or your custom domain if you attach one to the backend project).

### 2.2 Environment variables

The frontend currently has **no build-time environment variables** — the backend URL is handled entirely via the `vercel.json` rewrite above, not a `VITE_*` variable. If you later refactor `client.ts` to use an absolute base URL instead of the rewrite (e.g. for a non-Vercel backend), add:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://YOUR-BACKEND-DEPLOYMENT.vercel.app` |

and update `request()` in `client.ts` to prefix it: `` fetch(`${import.meta.env.VITE_API_BASE_URL}/api${path}`) ``. Not required for the default Vercel-to-Vercel rewrite setup.

### 2.3 Deploy

```bash
cd frontend
vercel link
vercel --prod
```

Vercel auto-detects the Vite build (`npm run build`, output in `dist/`) — no extra config needed beyond `vercel.json`.

---

## 3. Verify

```bash
curl https://YOUR-FRONTEND-DEPLOYMENT.vercel.app/api/health
# → {"status":"ok"}   (proxied through to the backend)

curl https://YOUR-FRONTEND-DEPLOYMENT.vercel.app/api/cities
# → 51 cities
```

Open the frontend URL in a browser — the national map and per-city dashboards should behave exactly as they do locally, minus the caveats in the box at the top of this doc.

---

## 4. Quick Troubleshooting

| Symptom | Likely cause |
|---|---|
| `504` on `/api/agent/scan` | Full DISCOVER scan exceeded `maxDuration` — you're on Hobby, or Pro's 300s still isn't enough for a slow FortyGuard response chain |
| `/api/*` returns the frontend's own 404 page | `frontend/vercel.json` rewrite destination is wrong, or missing entirely |
| `pymongo.errors.ServerSelectionTimeoutError` | `MONGO_URI` env var not set on the **backend** Vercel project, or Atlas network access doesn't allow `0.0.0.0/0` (Vercel functions have no fixed IP — you must allow all IPs in Atlas Network Access, or use Atlas's Vercel integration) |
| Auto-scan never runs | `AUTO_SCAN_ENABLED=true` alone won't work on serverless — use the Vercel Cron Job approach in §1.4 instead |
