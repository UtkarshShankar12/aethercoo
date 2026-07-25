# AetherCOO — Autonomous Multi-Agent AI Business Engine

AetherCOO is a premium business planning platform that uses a sequential pipeline of virtual executive agents to audit, model, and roadmap startup ideas.

It replaces standard corporate reports with blunt, realistic, numbers-driven feedback.

---

## Workspace Layout

```
.
├── index.html
├── package.json
├── vite.config.js
├── README.md
├── src/                      # Vite React Frontend
│   ├── main.jsx
│   ├── index.css
│   ├── App.jsx               # Integrates with Websockets and FastAPI
│   └── components/
│       ├── GoalInput.jsx     # Sleek Command-bar layout
│       ├── HeroOrb.jsx       # iridescence 3D status orb
│       ├── AgentPipeline.jsx # Active agent status logs
│       ├── FinalReport.jsx   # Interactive charts & grounded advisor chat
│       └── HistoryView.jsx   # Archive run recall cards
└── backend/                  # FastAPI Backend App
    ├── app/
    │   ├── main.py           # FastAPI entrypoint
    │   ├── config.py         # Environment variables validation
    │   ├── database.py       # Local SQLite Database client
    │   ├── schemas.py        # Pydantic JSON schemas
    │   ├── routes/
    │   │   └── runs.py       # API endpoints (CRUD, Websockets, Chat)
    │   └── agents/
    │       ├── orchestrator.py # Multi-agent execution orchestrator
    │       ├── ceo.py        # Business model agent
    │       ├── research.py   # Competitor/SWOT agent (Claude Haiku)
    │       ├── finance.py    # Cashflow spreadsheet agent
    │       └── qa.py         # Viability rating & risk matrix agent
    ├── requirements.txt      # Python dependencies
    └── README.md             # Detailed backend local setup instructions
```

---

## Quick Start Guide

### 1. Startup the Backend Service
SQLite is built into Python. On startup, the backend automatically initializes the `aethercoo.db` file and migrates all required tables. There is no manual database setup or SQL import required.

See [backend/README.md](backend/README.md) for environment variables configuration and dependencies installation steps:
```bash
cd backend
python -m venv venv
# Activate virtual environment
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```
FastAPI runs on `http://localhost:8000`.

### 2. Startup the Frontend Dashboard
```bash
# Return to the root directory
# Install node packages
npm install

# Run the Vite server locally
npm run dev
```
Open `http://localhost:5173` in your browser.
