# AetherCOO — Autonomous Multi-Agent AI Business Engine

> **Submit a raw business idea. Get a CEO, Research, Finance & QA Risk report — live, streamed, in seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)

---

## What It Does

AetherCOO orchestrates a **sequential pipeline of 5 specialized AI agents** — all powered by Google Gemini — that analyze any business idea and produce a consolidated strategy dashboard:

| Agent | Role | Output |
|-------|------|--------|
| **CEO Agent** | Strategic framing | Business model, industry, audience, value prop |
| **Research Agent** | Competitive intel | Competitors, SWOT analysis, market analysis |
| **Finance Agent** | Unit economics | CAC, LTV, 6-month financial projections |
| **QA Risk Agent** | Risk auditing | Trust score, risks, regulatory flags |
| **Consolidator** | Synthesis | 6-month roadmap, revenue model, final dashboard |

Results stream live over **WebSocket** with real-time progress updates, falling back to HTTP polling automatically.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         BROWSER (React 18)                           │
│  Landing → Submit Idea → Live Stream View → Final Dashboard Report   │
│                    ↑ WebSocket / HTTP Polling Fallback               │
└────────────────────┬─────────────────────────────────────────────────┘
                     │ HTTPS / WSS
┌────────────────────▼─────────────────────────────────────────────────┐
│                   RENDER.COM — Docker Container                      │
│                   FastAPI (uvicorn, 1 worker)                        │
│                                                                      │
│  POST /api/runs ──► BackgroundTask ──► Orchestrator Pipeline         │
│                                                  │                   │
│                    ┌─────────────────────────────▼──────────────┐   │
│                    │  1. CEO Agent  (gemini-2.5-flash)           │   │
│                    │  2. Research Agent                          │   │
│                    │  3. Finance Agent                           │   │
│                    │  4. QA Risk Agent  (with graceful fallback) │   │
│                    │  5. Consolidator   (final dashboard)        │   │
│                    └─────────────────────────────┬──────────────┘   │
│                                                  │                   │
│  SQLite (aethercoo.db) ◄─────────────────────────┘                  │
│  Persists: runs, agent_outputs, dashboard, costs, advisor_messages   │
│                                                                      │
│  Rate Limiting: 5 runs/hour/user  ·  Input: 10–2000 chars           │
│  Security Headers: HSTS, CSP, X-Frame, X-Content-Type, Referrer     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) 0.115 + Uvicorn (async ASGI)
- [Google Gemini API](https://aistudio.google.com) (`gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash` fallback chain)
- SQLite via Python `sqlite3` (persistent, zero-config)
- WebSockets for live streaming
- Pydantic v2 structured output schemas
- SlowAPI rate limiting

**Frontend**
- React 18 + Vite
- Vanilla CSS (dark theme, glassmorphism)
- WebSocket + HTTP polling fallback
- Recharts for financial charts

**Infrastructure**
- 🐳 Docker (non-root hardened image)
- [Render.com](https://render.com) — backend (free tier, 750 hrs/mo)
- [Netlify](https://netlify.com) — frontend (free tier, unlimited)
- HTTPS everywhere via platform TLS

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 1. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/aethercoo.git
cd aethercoo
```

**Backend env:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set your GEMINI_API_KEY
```

**Frontend env:**
```bash
cp .env.example .env.local
# .env.local already points to http://localhost:8000
```

### 2. Run Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 3. Run Frontend

```bash
# From repo root
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 4. Run Tests

```bash
cd backend
python -m pytest tests/ -v
# 12 tests — all should pass without a real Gemini API key
```

---

## Cloud Deployment

### Backend → Render.com (Docker)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Set **Root Directory** to `backend/`
5. Set **Runtime** to `Docker`
6. In **Environment Variables** (Render dashboard), add:
   ```
   GEMINI_API_KEY = <your key>
   CORS_ORIGINS   = ["https://your-app.netlify.app"]
   PORT           = 8000
   ```
7. Deploy — your backend URL will be: `https://aethercoo-backend.onrender.com`

### Frontend → Netlify

1. Go to [netlify.com](https://netlify.com) → **Add new site → Import from Git**
2. Connect your GitHub repo
3. Build settings (auto-detected from `netlify.toml`):
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
4. In **Site configuration → Environment variables**, add:
   ```
   VITE_API_URL = https://aethercoo-backend.onrender.com
   VITE_WS_URL  = wss://aethercoo-backend.onrender.com
   ```
5. Deploy — your frontend URL will be: `https://aethercoo.netlify.app`

> **Update CORS** — after getting your Netlify URL, update `CORS_ORIGINS` in Render to match.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/runs` | Submit a business idea |
| `GET` | `/api/runs?user_id=` | List run history |
| `GET` | `/api/runs/diag/check` | Verify Gemini API key |
| `GET` | `/api/runs/{run_id}` | Get completed dashboard |
| `DELETE` | `/api/runs/{run_id}` | Delete a run |
| `POST` | `/api/runs/{run_id}/advisor` | Ask the AI advisor |
| `WS` | `/api/runs/{run_id}/stream` | Live execution stream |

### POST /api/runs

```json
{
  "idea": "A SaaS for restaurant reservations (10–2000 chars)",
  "user_id": "anonymous-uuid-here"
}
```

**Response:**
```json
{ "run_id": "550e8400-e29b-41d4-a716-446655440000", "status": "pending" }
```

---

## Security Measures

| Control | Implementation |
|---------|---------------|
| **HTTPS/WSS** | Platform TLS on Render + Netlify |
| **CORS** | Locked to specific frontend origin (not wildcard) |
| **Security Headers** | HSTS, X-Frame-Options, X-Content-Type, X-XSS, Referrer-Policy |
| **Content-Security-Policy** | Set in `netlify.toml` headers |
| **Input Validation** | Pydantic: idea 10–2000 chars, user_id max 128 chars |
| **Rate Limiting** | 5 runs/hour/user (SlowAPI + in-memory enforcement) |
| **Non-root Docker** | Container runs as `appuser`, not root |
| **Secret Management** | API keys via env vars only — never committed |
| **No Wildcard CORS** | `allow_credentials=False`, explicit method/header lists |
| **Dependency Audit** | Removed dead `supabase` package; pinned all versions |

---

## Project Structure

```
aethercoo/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, security headers
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # SQLite layer (5 tables)
│   │   ├── schemas.py           # Pydantic I/O models
│   │   ├── routes/
│   │   │   └── runs.py          # All REST + WebSocket endpoints
│   │   └── agents/
│   │       └── orchestrator.py  # 5-agent Gemini pipeline
│   ├── tests/
│   │   └── test_api.py          # 12 integration tests
│   ├── Dockerfile               # Hardened non-root image
│   ├── .dockerignore
│   ├── requirements.txt
│   └── render.yaml              # Render.com deployment config
├── src/
│   └── App.jsx                  # React frontend
├── public/
│   └── favicon.svg
├── netlify.toml                 # Netlify build + security headers
├── .env.example                 # Frontend env template
└── README.md
```

---

## License

[MIT](LICENSE) © 2026 AetherCOO
