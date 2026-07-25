# AetherCOO API Backend

Production-ready sequential multi-agent AI execution engine built with FastAPI, local SQLite database, and the Google Gemini API.

---

## Architecture Overview

AetherCOO translates user startup ideas into unified execution dashboards. It coordinates 4 virtual executive agents:
1. **CEO Agent:** Analyzes idea scope, target demographics, value prop, and sets the baseline profile.
2. **Research Agent:** Performs competitor scanning and a brutally honest SWOT analysis using Gemini Flash.
3. **Finance Agent:** Computes INR pricing metrics, payback period, gross margins, and forecasts a cumulative 12-month projection sheet.
4. **QA Risk Agent:** Audits compliance, details high/medium risk categories, outlines realistic mitigations, and scores overall viability.

A final **Consolidator** pass merges the agent reports and writes the custom month-by-month roadmap and revenue logic to a local SQLite database file (`aethercoo.db`).

---

## Environment Configuration

Create a `.env` file in the `backend` directory matching the keys in [.env.example](.env.example):

```bash
# Google Gemini API Credentials
GEMINI_API_KEY=your-gemini-api-key-here

# Application Settings
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"]
HOST=0.0.0.0
PORT=8000
```
> [!WARNING]
> Do NOT enable billing on the Google Cloud project this API key belongs to. Doing so permanently removes the free tier, converting all requests to paid tier usage. Keep it on the default free tier.

---

## Free-Tier Guardrails

Because the Gemini free tier has tight rate limits (~1,500 requests/day, 15 requests/minute), the backend enforces several guardrails:
* **Global Capacity Cap:** Rejects new runs or boardroom advisor queries if the system exceeds 1,200 API calls globally within a 24-hour window (80% of daily quota), returning a clean "daily capacity reached" message.
* **Per-User daily run cap:** Caps individual user IDs at 10 runs per day.
* **Request Spacing Limiter:** Automatically spaces all global API requests by at least 4.1 seconds, preventing concurrent runs from collectively triggering 429 Rate Limit responses.
* **Exponential Backoff:** Retries API calls automatically (1s, 2s, 4s, up to 3 attempts) if rate limit exhaustion errors are encountered.

---

## Database Setup

SQLite is built directly into Python. On startup, the backend automatically initializes the `aethercoo.db` file and migrates all required tables. There is no manual database setup or SQL import required.

---

## Local Development Setup

Ensure you have **Python 3.10+** installed:

### 1. Initialize Virtual Environment & Packages
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate venv (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the FastAPI Development Server
```bash
# Start server with live reload on port 8000
python app/main.py
```
The server will boot at `http://localhost:8000`. You can inspect the interactive OpenAPI swagger documentation at `http://localhost:8000/docs`.

---

## API Routes Listing

* **Runs Orchestration:**
  * `POST /api/runs` — Accepts `{idea: string, user_id: string}`, kicks off background agent run. Enforces limit of 5 runs/hour.
  * `GET /api/runs` — Retrieves user run archives list.
  * `GET /api/runs/{run_id}` — Returns the final consolidated dashboard JSON.
  * `DELETE /api/runs/{run_id}` — Clears a run and associated tables.
* **WebSocket Streams:**
  * `WS /api/runs/{run_id}/stream` — Streams log steps and complete notifications to the client.
* **Ask the Advisor Boardroom Chat:**
  * `POST /api/runs/{run_id}/advisor` — Grounded advisor chat. Accepts history and question, returns blunt numbers-driven context advice.

---

## Production Deployment

### Backend (Railway / Render / Heroku)
1. Link your repository.
2. Set build command to `pip install -r requirements.txt`.
3. Set start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Configure env variables listed above in the hosting dashboard.

### Frontend (Vercel / Netlify)
1. Deploy the React static build (`npm run build`).
2. Update the `BACKEND_URL` and `WS_URL` inside `src/App.jsx` to reference your hosted backend API service domain.
