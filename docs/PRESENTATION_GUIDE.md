# AetherCOO — Complete Presentation Guide
> Built from your actual source code. Every detail here is verified against your files.

---

## ⚠️ IMPORTANT NOTES BEFORE YOU START

- **What is ACTUALLY deployed on AWS:** Your `config.py` and `task-definition.json` confirm AWS S3 + ALB + ECS Fargate + Secrets Manager are configured. The CORS list in `config.py` contains the actual S3 website URL (`aethercoo-frontend-724413959665.s3-website-us-east-1.amazonaws.com`) and the ALB URL (`aethercoo-alb-1943562157.us-east-1.elb.amazonaws.com`). This is your primary deployment. Your `README.md` also mentions Render.com + Netlify as an alternative deployment. Confirm with professors which deployment you're presenting.
- **The Gemini API key is fetched from AWS Secrets Manager** at container startup via the ECS task definition (confirmed in `task-definition.json`). The key is NOT hardcoded.
- **There are exactly 5 agents** (confirmed from code): CEO, Research, Finance, QA Risk, and Consolidator.
- **The database is SQLite**, not a cloud database like PostgreSQL or Supabase.

---

## 1. COMPLETE PROJECT UNDERSTANDING

### What AetherCOO Is

AetherCOO is a web application that takes any business idea you type in plain English — like *"Launch a subscription box for premium organic Matcha tea targeted at Gen-Z remote workers"* — and automatically runs it through a team of 5 specialized AI agents. These agents act like a virtual executive team: a CEO, a Market Researcher, a Finance Analyst, a QA Risk Auditor, and a final Consolidator. Together, they produce a complete, honest business strategy report in real time.

The word **COO** stands for Chief Operating Officer — the person who operationalizes a CEO's vision. AetherCOO is an automated COO for your startup idea.

### What Problem It Solves

When someone has a business idea, figuring out:
- Is this idea viable?
- Who are my competitors?
- How much will this cost me?
- When will I break even?
- What are the risks?

...normally takes weeks of research, hiring consultants, or spending hours on spreadsheets. AetherCOO compresses that entire process into a 1–2 minute automated run.

### Who Would Use It

- First-time entrepreneurs who have an idea but don't know where to start
- Students validating startup ideas
- Business founders who want a quick, honest sanity check before committing money
- Hackathon teams, startup competitions, accelerator programs

---

### The Complete Flow: Submit → Result

Here is exactly what happens at every technical step when a user presses **Launch**:

#### STEP 1 — User opens the app (Frontend loads from AWS S3)

The React frontend is built into a set of static HTML/CSS/JavaScript files. These files are stored in an **AWS S3 bucket** which is configured as a static website host. When a user visits the URL, AWS S3 serves these files directly to the browser, the same way a normal website loads.

There is no server involved yet at this point. The browser just downloads and displays the landing page.

#### STEP 2 — User types a business idea and clicks Launch

The landing page has a text input box. The user types their idea (minimum 10 characters, maximum 2000 characters — validated by the frontend and backend both).

When the user clicks **Launch**, the `handleLaunch` function in `App.jsx` fires.

#### STEP 3 — Frontend sends POST /api/runs to the AWS ALB

The frontend makes an **HTTP POST request** to:
```
POST /api/runs
Body: { "idea": "user's idea text", "user_id": "anonymous-uuid" }
```

The `user_id` is a UUID (a unique random ID, like a fingerprint) that was automatically generated and stored in the browser's **localStorage** the first time the user visited the site. This is how the system tracks users without requiring login.

This request goes to the **AWS Application Load Balancer (ALB)** — not directly to the backend. The ALB is a traffic manager that sits in front of the backend and routes requests to the correct container.

#### STEP 4 — AWS ALB forwards request to the ECS Fargate container

The ALB receives the request and **forwards** it to the backend container running inside **AWS ECS Fargate**. Think of ECS Fargate as a managed server that runs your Docker container in the cloud — you don't have to manage any virtual machines yourself.

#### STEP 5 — FastAPI Backend receives the request

Inside the Fargate container, the **FastAPI** application (a Python web framework) is running. Specifically, the endpoint `POST /api/runs` in `routes/runs.py` handles the request.

**Before doing anything with AI, the backend runs 3 safety checks:**

1. **Global capacity check:** Has the system received more than 1,200 requests in the last 24 hours? If yes → reject (status 429)
2. **Per-user daily limit:** Has this specific user submitted more than 10 runs today? If yes → reject (status 429)  
3. **Per-user hourly limit:** Has this user submitted more than 5 runs in the last hour? If yes → reject (status 429)

If all checks pass, the backend:
- Creates a new **run record** in the SQLite database with status `"pending"` and a unique `run_id`
- Returns `{ "run_id": "uuid", "status": "pending" }` immediately to the frontend
- Starts the **orchestration pipeline in the background** (so the HTTP response goes back fast, and AI work happens separately)

#### STEP 6 — Frontend connects via WebSocket for live updates

As soon as the frontend gets the `run_id` back, it immediately opens a **WebSocket connection** to:
```
WS /api/runs/{run_id}/stream
```

A WebSocket is a persistent, two-way connection between the browser and the server — unlike a normal HTTP request which is one-shot. This allows the server to **push live updates** to the browser as each agent finishes its work. The user sees a live log terminal updating in real time.

**Fallback:** If WebSocket fails (network issue, firewall), the frontend automatically switches to **HTTP polling** — it checks `GET /api/runs/{run_id}` every 3 seconds until the run is complete.

#### STEP 7 — The Orchestrator Pipeline runs 5 agents sequentially

The `run_orchestration` function in `orchestrator.py` now runs in the background. It calls 5 AI agents **one after another** (sequentially, not in parallel), because each agent uses the output of the previous one.

Here is the exact sequence:

---

**Agent 1: CEO Agent**
- The orchestrator sets the run status to `"ceo_working"` in the database
- It sends a prompt to Google Gemini API with the user's idea
- The system prompt tells Gemini to act as a "Chief Strategist" — blunt, no corporate buzzwords
- The Gemini model outputs a structured JSON with: `subject`, `businessModel`, `modelType`, `industry`, `location`, `audience`, `core_value_prop`
- This output is saved to the database

Example CEO output for "Matcha tea subscription":
- Subject: "Premium Organic Matcha Tea Subscription Box"  
- Business Model: "Subscription / Recurring Delivery"  
- Industry: "Food & Beverage"  
- Audience: "Gen-Z remote workers"

---

**Agent 2: Research Agent**
- Gets the CEO's output as additional context
- Status becomes `"research_working"` 
- System prompt: act as a "skeptical market analyst who sees through hype"
- Outputs: list of 3–4 competitors, a full SWOT analysis (Strengths, Weaknesses, Opportunities, Threats), and a market analysis paragraph
- SWOT is brutally honest — for example, Weaknesses will say things like "zero brand recognition" and "founder burnout risk"
- Output saved to database

---

**Agent 3: Finance Agent**
- Gets CEO + Research outputs as context
- Status becomes `"finance_working"`
- System prompt: "conservative, quantitative — you hate inflated forecasts"
- All numbers are in **Indian Rupees (₹)**
- Outputs:
  - **CAC (Customer Acquisition Cost):** How much it costs to get one customer
  - **LTV (Customer Lifetime Value):** How much one customer is worth over time
  - **LTV/CAC Ratio:** Must be 3x–5x for the business to be viable
  - **Payback Period:** How many months to recover CAC
  - **Break-even Timeline:** e.g., "Month 8–10"
  - **Total 6-Month Budget:** What you need to survive 6 months
  - **5 periods of projected financials:** Month 1–2, Month 3–4, Month 5–6, Month 7–9, Month 10–12 (with revenue, expenses, profit for each)
- The first 1–2 periods are expected to show negative profit (spending to build)
- Output saved to database

---

**Agent 4: QA Risk Agent**
- Gets all 3 previous outputs as context
- Status becomes `"qa_working"`
- System prompt: "cautious, risk-averse, the checks-and-balances layer"
- Outputs:
  - **Trust Score:** A viability score from 0–100. Conservative — most startups fail.
  - **Assumptions:** Key conditions that must be true for the plan to work
  - **Risks:** 3–4 specific risks with severity (High/Medium/Low) and mitigation steps
  - **Recommendations:** 3–4 direct next-step suggestions (e.g., "Don't quit your day job yet")
- **Graceful degradation:** If the QA Agent's Gemini API call fails (e.g., rate limit), the system does NOT crash. It falls back to a default risk matrix and continues.

---

**Agent 5: Consolidator**
- Takes ALL 4 previous agents' outputs and synthesizes them
- Outputs the final unified **RunDashboard** — a single, comprehensive JSON object
- Generates NEW content that wasn't in previous agents:
  - **6-Month Roadmap:** One priority per month, with specific actions, a monthly budget allocation, and a "reality check" condition
  - **Revenue Model:** Primary revenue stream, secondary revenue stream, and an "Honest Truth" about cash flow timing
- The Consolidator assembles the master dashboard and saves it to a dedicated `run_dashboard` table in SQLite

#### STEP 8 — Backend broadcasts "completed" via WebSocket

When the Consolidator finishes, the orchestrator sends a WebSocket message:
```json
{ "type": "completed", "dashboard": { ...entire report... } }
```

The frontend receives this, stores the dashboard data in React state, and after a 1.2-second transition delay, switches to the **Final Report screen**.

#### STEP 9 — User sees the Final Dashboard

The `FinalReport.jsx` component displays the results across 5 tabs:
1. **6-Month Roadmap** — monthly plan with budget and reality checks
2. **How You Earn** — revenue model + SWOT
3. **Competition & Risks** — market analysis, competitors table, risk matrix
4. **Budget & Numbers** — interactive financial chart + P&L table + key metrics
5. **Ask the Advisor** — live AI chat grounded in the run's report data

The user can also **download the plan as a `.txt` file** directly from the browser.

---

## 2. PROBLEM STATEMENT

### What Problem We Identified

When someone has a business idea, validating it is extremely slow and manual. You need a market researcher to find competitors, a finance expert to model numbers, a risk consultant to spot problems — that's weeks of work and potentially thousands of rupees in consulting fees.

Even with AI tools like ChatGPT, you'd have to ask multiple separate questions, copy-paste context between sessions, and manually piece together the outputs. There's no structured, automated workflow.

### 30–45 Second Speaking Answer

*"The problem we identified is simple: good business ideas die because people don't have the time, money, or expertise to validate them properly. Traditional business analysis requires hiring multiple specialists — a market researcher, a financial analyst, a risk consultant — which is expensive and slow, taking weeks.*

*Even with modern AI tools, users have to manually prompt each specialist area separately, copy results between conversations, and piece it all together themselves. There's no structured, automated system for this.*

*AetherCOO solves this by creating a pipeline of 5 specialized AI agents that work sequentially — each one feeding its output into the next — to produce a complete, honest, structured business strategy report in under 2 minutes. What used to take weeks and significant money now takes seconds."*

---

## 3. OBJECTIVE

### Technical Objectives
1. Build a **sequential multi-agent AI pipeline** using Google Gemini that produces structured, validated JSON outputs at each stage
2. Implement **real-time communication** using WebSockets, with HTTP polling as an automatic fallback
3. **Containerize** the backend using Docker and deploy it on AWS ECS Fargate (serverless containers)
4. Store AI agent outputs **persistently** in SQLite with 5 normalized tables
5. Implement **rate limiting and capacity management** to prevent API abuse (5 runs/hour/user, 10 runs/day/user)
6. Retrieve secrets securely from **AWS Secrets Manager** — no API keys hardcoded anywhere
7. Add **graceful degradation** so the QA agent failure doesn't break the entire pipeline

### Business Objectives
1. Allow anyone to validate a business idea in under 2 minutes
2. Present outputs in **plain English**, not technical jargon — no corporate buzzwords
3. Provide **actionable, brutally honest advice** including what could go wrong
4. Make the tool accessible for free (rate-limited demo)

### AI Objectives
1. Use **structured output** (Gemini's JSON mode + Pydantic schemas) to guarantee consistent, parseable responses from the AI
2. Chain agents so each one **builds on the previous agent's context** — not isolated AI calls
3. Implement a **model fallback chain**: try `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash` if rate limits are hit
4. Add a **global rate limiter** that spaces API calls at least 4.1 seconds apart to stay under Gemini's 15 requests/minute limit

### Deployment Objectives
1. Host the frontend statically on **AWS S3** (zero server cost for static files)
2. Run the backend on **AWS ECS Fargate** (serverless containers — no EC2 to manage)
3. Route traffic through an **AWS Application Load Balancer** for reliability and HTTPS
4. Store the Gemini API key in **AWS Secrets Manager** (not in environment variables hardcoded into code)

### Short Presentation Answer

*"Our objectives are threefold. Technically, we wanted to prove that multiple AI agents can work as a coordinated pipeline — not as isolated chatbots. Business-wise, we wanted to make professional business validation accessible to anyone, not just people who can afford consultants. And from a deployment perspective, we wanted to demonstrate a real-world cloud architecture using AWS services — S3, ECS Fargate, Application Load Balancer, and Secrets Manager."*

---

## 4. COMPLETE SYSTEM ARCHITECTURE

### Component 1: User (Browser)

**What it is:** The person using the app on any web browser (Chrome, Firefox, etc.)

**What happens there:**
- The user opens the AetherCOO URL
- A UUID (unique anonymous ID) is auto-generated and saved in the browser's `localStorage`. This is the user's permanent anonymous identity — no account required.
- The user types a business idea and clicks **Launch**
- The browser then handles WebSocket communication for live updates

---

### Component 2: React Frontend

**What it is:** React is a JavaScript framework for building user interfaces. "Frontend" means everything the user sees and clicks on.

**Why we used it:** React makes it easy to manage "which screen is showing right now" and update the UI automatically when data changes (like when a new log message arrives).

**What it does in AetherCOO:** Manages 4 screens:
1. **Landing (GoalInput):** The input form with example idea chips and the animated hero orb
2. **Executing (AgentPipeline):** 4 animated agent cards + live terminal log + progress bar
3. **Report (FinalReport):** Full dashboard with 5 tabs and the advisor chat
4. **History (HistoryView):** Past runs list, click to reload any report

**Key libraries used:**
- `framer-motion` — for smooth animations on agent cards and progress bars
- `recharts` — for the financial area chart in the Budget tab
- `lucide-react` — for icons (Shield, TrendingUp, etc.)
- `Tailwind CSS` — for styling

**What happens to data:** The frontend holds report data in React state (`useState`). When the WebSocket sends the final dashboard, it's stored as a JavaScript object and passed to `FinalReport.jsx` as props.

---

### Component 3: AWS S3 (Static Website Hosting)

**What it is:** Amazon S3 (Simple Storage Service) is a file storage service. It has a feature that lets you serve files directly as a website.

**Why we used it:** The React app, once built with `npm run build`, becomes a folder of static HTML/CSS/JS files. You don't need a running server to serve these — S3 can do it for free (or near-free). There's no compute involved. It's like hosting files on a public USB drive on the internet.

**What it does in AetherCOO:** Stores the built React frontend files (`dist/` folder). When anyone visits the URL, S3 serves `index.html` directly to the browser. The browser downloads the React JavaScript bundle and runs it locally.

**What happens to data:** No data processing. S3 just stores and delivers static files.

**What happens next:** The browser runs the React app, and the user sees the landing page.

---

### Component 4: AWS Application Load Balancer (ALB)

**What it is:** A load balancer is a traffic director. It sits in front of your actual servers and forwards incoming requests to the right place.

**Why we used it:** 
1. It provides a stable, permanent URL for the backend (even if the container restarts or changes IP)
2. It can handle HTTPS termination (encrypting traffic)
3. It can distribute traffic across multiple containers if you need to scale
4. It performs health checks — if the container is unhealthy, the ALB stops sending traffic to it

**What it does in AetherCOO:** Receives all API requests from the frontend (like `POST /api/runs`) and forwards them to the backend container running in ECS Fargate. The CORS configuration in `config.py` includes the ALB's URL (`aethercoo-alb-1943562157.us-east-1.elb.amazonaws.com`).

**What happens to data:** The ALB doesn't modify data. It just routes the HTTP/WebSocket request to the backend container.

**What happens next:** The request arrives at the FastAPI backend inside the Docker container.

---

### Component 5: AWS ECS Fargate

**What it is:** ECS stands for Elastic Container Service. Fargate is a "serverless" mode — you tell AWS "run this Docker container" and AWS handles all the underlying server infrastructure for you. You don't manage VMs (Virtual Machines), you just say what container you want and AWS runs it.

**Why we used it:** 
- No need to provision or manage servers (EC2 instances)
- The container starts with the exact environment we defined in the Dockerfile
- Scales automatically if needed
- Our task definition allocates **512 CPU units and 1024 MB of memory** to the backend

**What it does in AetherCOO:** Runs our Docker container continuously. The container listens on port 8000 for incoming requests. When a request arrives from the ALB, it's processed by the FastAPI application running inside.

**What happens to data:** ECS just provides the computing environment. The actual processing happens inside the Docker container.

**What happens next:** The Docker container processes the request.

---

### Component 6: Docker Container

**What it is:** Docker is a tool that packages an application with all its dependencies (Python, libraries, etc.) into a self-contained "container" that runs consistently anywhere.

**Why we used it:** 
- Guarantees that the exact same Python version (3.11) and libraries run in development and in production
- The container is **hardened** — it runs as a non-root user called `appuser` (not as an administrator), which is a security best practice
- AWS ECS requires a Docker container image to run

**Our Dockerfile does the following:**
1. Starts from `python:3.11-slim` (a minimal Python image)
2. Copies `requirements.txt` and installs all Python packages
3. Copies the `app/` source code
4. Creates a non-root user `appuser` and switches to it
5. Exposes port 8000
6. Runs a health check every 30 seconds (`GET /health`)
7. Starts the server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`

**What happens to data:** The container runs Python, which runs FastAPI, which processes the request.

**What happens next:** FastAPI handles the incoming HTTP request.

---

### Component 7: FastAPI Backend

**What it is:** FastAPI is a modern Python web framework for building APIs (Application Programming Interfaces — ways for different programs to talk to each other). It's fast, async-capable, and automatically generates documentation.

**Why we used it:**
- Natively supports **async** operations (crucial for WebSockets and background tasks)
- Built-in **Pydantic** integration for request/response validation
- Auto-generates `/docs` page (Swagger UI) for the API
- Lightweight and fast

**What it does in AetherCOO:** 
- Defines all API endpoints (routes)
- Validates incoming requests using Pydantic schemas
- Runs the rate limit checks
- Creates database records
- Starts the agent orchestration as a background task
- Manages WebSocket connections
- Adds security headers to every response (HSTS, X-Frame-Options, X-XSS-Protection, etc.)

**Security headers added to every response:**
- `X-Content-Type-Options: nosniff` — prevents MIME sniffing attacks
- `X-Frame-Options: DENY` — prevents clickjacking
- `X-XSS-Protection: 1; mode=block` — blocks cross-site scripting
- `Strict-Transport-Security` — forces HTTPS for 1 year

**What happens to data:** Request body is validated, rate limits are checked, a database record is created, background orchestration is triggered.

**What happens next:** The Gemini API key is needed. The backend reads it from AWS Secrets Manager.

---

### Component 8: AWS Secrets Manager

**What it is:** A secure storage service for sensitive information like API keys, passwords, and database credentials.

**Why we used it:** 
- You should NEVER hardcode an API key in source code (it could be leaked on GitHub)
- Environment variables are slightly better but can appear in logs
- Secrets Manager stores the key encrypted, and only authorized AWS roles can access it
- The key rotates without needing to redeploy the application

**How it's implemented in AetherCOO:**
In the ECS task definition (`task-definition.json`), there's a `secrets` section:
```json
{
  "name": "GEMINI_API_KEY",
  "valueFrom": "arn:aws:secretsmanager:us-east-1:724413959665:secret:aethercoo/gemini-eyg2q2:GEMINI_API_KEY::"
}
```
This tells ECS: "When starting this container, go to Secrets Manager, retrieve the secret at this ARN (Amazon Resource Name — basically an address), and inject it as the environment variable `GEMINI_API_KEY`."

The `config.py` reads: `gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")`

**What happens to data:** The Gemini API key is injected into the container at startup time as an environment variable. No hardcoding anywhere.

**What happens next:** The orchestrator uses this key to call Google Gemini.

---

### Component 9: Google Gemini API

**What it is:** Google Gemini is Google's large language model (LLM) — an AI that can understand and generate text. The API (Application Programming Interface) lets developers send text and receive AI-generated text back.

**Why we used it:**
- Supports **structured JSON output** (telling the AI to output only valid JSON matching a specific schema) — essential for our agent pipeline
- Has a model fallback chain: `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash`
- Free tier available for development

**How it's used:** The `call_agent_structured()` function in `orchestrator.py`:
1. Takes a **system prompt** (who the AI should pretend to be) + **user prompt** (what to analyze)
2. Sends the Pydantic schema (the exact JSON structure expected) to Gemini via `response_mime_type="application/json"`
3. Gemini returns a JSON response
4. The function validates the JSON against the Pydantic schema
5. Returns the validated Python object

**Rate limiting logic:**
- A global lock ensures API calls are spaced **at least 4.1 seconds apart**
- This keeps calls under Gemini's free tier limit of 15 requests/minute
- On rate limit errors (HTTP 429), the system tries the next model in the fallback chain

**What happens to data:** The business idea and context from previous agents are sent as text. Gemini returns structured JSON that is validated and stored in SQLite.

---

### Component 10: Agent Orchestration

**What it is:** The `run_orchestration` function in `orchestrator.py`. It's the master controller that calls each agent in sequence and passes outputs between them.

**Why sequential (not parallel):**
- Each agent NEEDS the previous agent's output as context
- The Research Agent needs to know what business model the CEO identified
- The Finance Agent needs to know what competitors Research found
- The QA Agent needs to know what budget Finance calculated
- Running them in parallel would mean they can't reference each other

**What it does:**
1. Calls CEO → saves output → broadcasts log to WebSocket
2. Calls Research (with CEO output as context) → saves → broadcasts
3. Calls Finance (with CEO + Research output as context) → saves → broadcasts
4. Calls QA Risk (with all 3 previous outputs as context) → saves → broadcasts
5. Calls Consolidator (with all 4 outputs) → saves final dashboard → broadcasts "completed"

**Throughout the pipeline:**
- Token counts (input + output) are accumulated to track total usage
- Run status is updated in the database at each step (`ceo_working`, `research_working`, etc.)
- Progress percentage (0–100) is broadcast to the frontend at each step

---

### Components 11–13: 5 Specialized AI Agents

*(See Section 5 for detailed agent breakdown)*

---

### Component 14: SQLite Database

**What it is:** SQLite is a lightweight, file-based relational database (like a spreadsheet but structured and queryable). The database is a single file: `aethercoo.db`.

**Why we used it:** 
- Zero configuration — no separate database server to set up
- Persistent across container restarts (if the volume is mounted)
- Sufficient for the current scale
- Standard Python library supports it natively

**5 tables in the database:**
1. `runs` — one record per business run (id, user_id, idea_text, status, viability_score, created_at)
2. `run_agent_outputs` — stores CEO/Research/Finance/QA output JSON per run
3. `run_dashboard` — stores the final consolidated dashboard JSON (roadmap, revenue, risk, budget)
4. `advisor_messages` — stores conversation history for the AI boardroom chat
5. `run_costs` — stores input tokens, output tokens, estimated API cost per run

**What happens to data:** Each agent's output is serialized to JSON and stored. The dashboard query joins data from multiple tables to assemble the final response.

---

### Component 15: Results Return to Frontend

After the Consolidator finishes:
1. The full dashboard JSON is sent via WebSocket to the frontend
2. The frontend's `setReportData(message.dashboard)` stores it in React state
3. After 1.2 seconds, the screen transitions to `FinalReport`
4. The history list is refreshed (`refreshHistory()`) to show the new run

---

## 5. FRONTEND

### Framework: React (v19) + Vite

**React** is the JavaScript framework for building the UI. **Vite** is the build tool — it's what compiles and bundles the React code into files that browsers can understand.

**Key Libraries:**
| Library | Version | Purpose |
|---------|---------|---------|
| `react` | 19.2.7 | UI framework |
| `framer-motion` | 12.x | Smooth animations on agent cards, progress bars |
| `recharts` | 3.x | Financial area chart in Budget tab |
| `lucide-react` | 1.x | Icons (shield, trending-up, etc.) |
| `tailwindcss` | 4.x | CSS utility classes for styling |

---

### Pages / Screens

The app has **4 screens**, controlled by a single `screen` state variable in `App.jsx`:

#### Screen 1: Landing (`GoalInput.jsx`)
- **Left side:** Headline + description + the text input form + 3 example idea chips
- **Right side:** The `HeroOrb` — an animated decorative visual element
- The input has a **Terminal icon** prefix, styled as a command bar
- Clicking an example chip auto-fills the text box
- The **Launch button** submits the form

#### Screen 2: Executing (`AgentPipeline.jsx`)  
- **4 Agent Cards** arranged in a row (CEO → Research → Finance → QA Risk)
- Each card can be in 3 states: `idle` (dimmed), `working` (glowing + animated), `done` (green checkmark)
- An **animated beam** travels horizontally across the connecting line between cards when any agent is working
- A **progress bar** (0–100%) shows the overall run completion
- A **live terminal** at the bottom shows all log messages from the backend, color-coded by agent:
  - CEO = blue (`#0052FF`)
  - Research = green (`#39FF14`)
  - Finance = white
  - QA = pink (`#FF007A`)

#### Screen 3: Report (`FinalReport.jsx`)
- **Top banner:** Business name, model type, industry, audience
- **Reality check banner:** Key assumptions from the QA agent (in yellow warning style)
- **5 tabs:**
  1. **6-Month Roadmap** — each month has a priority, action list, budget allocation, and a "Reality Check" condition
  2. **How You Earn** — primary revenue, secondary revenue, the "Honest Truth" about cash timing, recommendations, SWOT grid
  3. **Competition & Risks** — market analysis paragraph, competitors list, risk matrix table (category, description, severity badge, mitigation)
  4. **Budget & Numbers** — area chart (revenue + net profit over 12 months), 4 key metric cards (total budget, break-even, CAC, LTV), P&L table
  5. **Ask the Advisor** — split view: quick-question shortcuts on left, chat interface on right
- **Download button** — exports the entire plan as a `.txt` file

#### Screen 4: History (`HistoryView.jsx`)
- Lists all past runs for the current user (fetched from `GET /api/runs?user_id=...`)
- Each run shows: business idea text, status, viability score, timestamp
- Clicking a run loads the full report from `GET /api/runs/{run_id}` and switches to the report screen

---

### How the Frontend Communicates with the Backend

There are 4 types of communication:

| # | Type | Endpoint | When |
|---|------|----------|------|
| 1 | `POST` HTTP | `/api/runs` | When user clicks Launch |
| 2 | `WebSocket` | `/api/runs/{run_id}/stream` | Immediately after step 1, for live updates |
| 3 | `GET` HTTP polling | `/api/runs/{run_id}` | Every 3 seconds if WebSocket fails |
| 4 | `POST` HTTP | `/api/runs/{run_id}/advisor` | When user sends a chat message in the Advisor tab |
| 5 | `GET` HTTP | `/api/runs?user_id=` | On page load and after each run, for history |
| 6 | `DELETE` HTTP | `/api/runs/{run_id}` | When user clears history |

**User ID handling:** The `getUserId()` function checks `localStorage` for a saved UUID. If none exists, it generates one using `window.crypto.randomUUID()` (browser's built-in secure random ID generator).

---

### Loading State

During execution:
- The screen switches to `AgentPipeline` immediately (even before the first agent runs)
- Agent cards pulse and glow as each agent becomes active
- Log messages appear in the terminal as they stream in from the WebSocket
- The progress bar moves from 0% to 100% as progress events arrive

### Error Handling

- If `POST /api/runs` returns an error (e.g., rate limit hit), `alert()` shows the error message and the screen returns to Landing
- If WebSocket fails, polling starts automatically
- If the QA agent fails inside the backend, it uses fallback data (the pipeline doesn't crash)
- If the Advisor API call fails, the chat shows an error message in the advisor's chat bubble

---

## 6. BACKEND

### Framework: FastAPI + Uvicorn

**FastAPI** is the web framework. **Uvicorn** is the ASGI server (the thing that actually listens for incoming HTTP connections and passes them to FastAPI). It runs with `--workers 1` — one worker process.

### API Endpoints (All Routes in `runs.py`)

| Method | Path | What it does |
|--------|------|-------------|
| `POST` | `/api/runs` | Submit idea, validate, trigger orchestration |
| `GET` | `/api/runs?user_id=` | Return all runs for a user |
| `GET` | `/api/runs/diag/check` | Verify Gemini API key is configured |
| `GET` | `/api/runs/{run_id}` | Return completed dashboard data |
| `DELETE` | `/api/runs/{run_id}` | Delete a run and all its data |
| `POST` | `/api/runs/{run_id}/advisor` | Boardroom advisor chat |
| `WS` | `/api/runs/{run_id}/stream` | Live WebSocket stream |
| `GET` | `/` | Root check (returns version info) |
| `GET` | `/health` | Health check for ALB/ECS |

### WebSocket Connection Manager

A `ConnectionManager` class in `runs.py` manages active WebSocket connections:
- `active_connections`: A dictionary mapping `run_id → list of WebSocket connections`
- Multiple browsers could watch the same run simultaneously
- `broadcast()` sends a JSON message to all connections for a specific run

### Pydantic Schemas

**Pydantic** is a Python library for data validation. We use it to define exactly what shape the AI's JSON output must be.

Every agent has a Pydantic model:
- `CEOOutput` — subject, businessModel, modelType, industry, industryType, location, audience, core_value_prop
- `ResearchOutput` — competitors (list), swot (SWOT object), marketAnalysis (string)
- `FinanceOutput` — metrics (FinanceMetrics object), financials (list of FinancialPeriod)
- `QARiskOutput` — trustScore (float 0–100), assumptions (list), risks (list of RiskItem), recommendations (list)
- `RunDashboardOutput` — the master schema containing all of the above plus roadmap and revenueModel

**Why Pydantic + JSON mode?** Because without forcing a specific JSON structure, the AI might return text in any format. By passing our Pydantic schema to Gemini's `response_schema` parameter, the AI is forced to return valid, structured JSON every time.

### Rate Limiting Details

Three layers of rate limiting (all in `runs.py`):

1. **Global daily cap:** `get_global_request_count_24h()` — counts rows in `run_agent_outputs`, `run_dashboard`, and `advisor_messages` tables created in the last 24 hours. Cap: 1,200.
2. **Per-user daily limit:** `get_user_run_count_24h()` — counts runs by user_id in last 24 hours. Cap: 10.
3. **Per-user hourly limit:** `get_runs_created_since()` — counts runs created in the last hour. Cap: 5.

### Background Tasks

When `POST /api/runs` is called, the orchestration is added as a `BackgroundTask` using FastAPI's built-in background task system:
```python
background_tasks.add_task(run_orchestration, run_id=run_id, idea=..., db=..., broadcast_callback=...)
```
This means the HTTP response goes back to the frontend immediately (with just the `run_id`), and the AI work happens asynchronously in the background. The WebSocket connection then carries the live updates.

---

## 7. THE 5 AI AGENTS — DETAILED

### Agent 1: CEO Agent

**System Prompt (what we tell Gemini to be):**
> "You are the CEO Agent, the chief strategist of AetherCOO. Your tone is blunt, pragmatic, and completely devoid of corporate buzzwords."

**Input:** Raw business idea text

**Output fields:**
- `subject` — clean name of the business (e.g., "Premium Organic Matcha Tea Subscription Box")
- `businessModel` — human-readable model type (e.g., "Subscription / Recurring Delivery")
- `modelType` — code-friendly type: one of `saas | subscription | marketplace | app | logistics | local | education`
- `industry` — human-readable industry (e.g., "Food & Beverage")
- `industryType` — code-friendly: one of `food | wellness | compliance | ai | edtech | fintech | tech`
- `location` — geographic scope (e.g., "Austin, TX" or "Online / Remote")
- `audience` — target demographic (e.g., "Gen-Z remote workers")
- `core_value_prop` — one sentence on what makes it unique

**Why it's first:** Everything else depends on knowing the business model and industry. Research can't find the right competitors without knowing if this is a SaaS vs. a local food business.

---

### Agent 2: Research Agent

**System Prompt:**
> "You are the Research Agent. Your tone is highly analytical, skeptical, and realistic. You see through market hype. If there is no direct competitor, call out the workarounds people use."

**Input:** Business idea + CEO output (subject, businessModel, industry, audience, location, core_value_prop)

**Output fields:**
- `competitors` — list of 3–4 top competitors (direct or indirect, like "manual spreadsheets" if no direct competitor)
- `swot` — SWOT analysis:
  - `strengths` — internal advantages (e.g., "agility, direct customer communication")
  - `weaknesses` — painful limitations (e.g., "zero brand recognition, tight runway")
  - `opportunities` — practical niches or channels
  - `threats` — real risks (e.g., "platforms cloning features, running out of capital")
- `marketAnalysis` — one raw, honest paragraph about market dynamics

---

### Agent 3: Finance Agent

**System Prompt:**
> "You are the Finance Agent. Your tone is quantitative, conservative, and realistic. You hate inflated forecasts. Currency: always INR (₹). Make sure LTV > CAC (aim for 3x–5x ratio)."

**Input:** Business idea + CEO output + Research output (competitors, SWOT opportunities)

**Output fields (FinanceMetrics):**
- `pricing` — initial product price (₹)
- `marginPct` — gross profit margin % (SaaS: 70–90%; physical: 30–50%)
- `cac` — Customer Acquisition Cost (₹) — "Do NOT set to zero; acquiring users costs money"
- `ltv` — Customer Lifetime Value (₹)
- `ltvCacRatio` — LTV/CAC ratio as a string (e.g., "3.5")
- `payback` — months to recover CAC
- `breakeven` — phrase like "Month 8–10"
- `totalBudget6mo` — total budget needed to survive 6 months (₹)

**Output fields (5 FinancialPeriods):**
- Periods: "Month 1–2", "Month 3–4", "Month 5–6", "Month 7–9", "Month 10–12"
- Each has: `revenue`, `expenses`, `profit` (profit = revenue - expenses)
- First 1–2 periods intentionally show negative profit (building phase)

---

### Agent 4: QA Risk Agent

**System Prompt:**
> "You are the QA Risk Agent. Your tone is cautious, risk-averse, and brutally honest. You are the checks-and-balances layer. Be conservative — most startups fail."

**Input:** Business idea + CEO (subject, value_prop) + Research (SWOT weaknesses + threats) + Finance (6mo budget, LTV/CAC ratio, break-even)

**Output fields:**
- `trustScore` — viability score 0.0–100.0 (conservative; most startups score 50–75)
- `assumptions` — list of conditions that must hold true (e.g., "Founder can work 4 hours/day")
- `risks` — list of 3–4 RiskItems: `{category, risk, severity (High/Medium/Low), mitigation}`
- `recommendations` — 3–4 direct next-step suggestions (e.g., "Don't quit your day job yet", "Talk to 20 users first")

**Graceful degradation:** If the QA agent API call fails, the system uses a default QA output with trustScore=75, generic assumptions, and one risk saying "Full audit temporarily offline." The pipeline continues to the Consolidator. This is a production-quality design decision.

---

### Agent 5: Consolidator (Final Synthesis)

**System Prompt:**
> "You are the Lead Consolidator for AetherCOO. Take outputs from all 4 agents and compile them into a unified final dashboard. Generate a 6-month roadmap and revenue model. Keep tone realistic and blunt."

**Input:** All 4 agents' outputs (compressed summaries)

**New output it generates:**
- `roadmap` — 6 `RoadmapMonth` objects, each with:
  - `month` — 1 to 6
  - `priority` — the primary focus of that month
  - `actions` — specific actionable tasks for the month
  - `budget` — budget allocated for that month (₹)
  - `realityCheck` — a condition like "If you don't have 5 paying customers by end of Month 2, reassess"
- `revenueModel` — `{primary, secondary, honestTruth}` — explains how money is made

**Why a separate Consolidator?** The 4 individual agents each focus on one domain. The Consolidator synthesizes them into a coherent, integrated output. It also ensures consistency (the roadmap budget lines up with what Finance calculated, the roadmap reality checks align with QA's risks).

---

## 8. DATABASE DESIGN

The SQLite database has **5 tables**:

```
runs
├── id (UUID, primary key)
├── user_id (anonymous UUID from browser)
├── idea_text (the raw idea)
├── status (pending | ceo_working | research_working | finance_working | qa_working | completed | failed)
├── viability_score (trust score from QA, filled at completion)
└── created_at

run_agent_outputs
├── id (UUID)
├── run_id → runs.id (CASCADE DELETE)
├── agent_name (ceo | research | finance | qa)
├── output_json (JSON blob of agent output)
└── created_at

run_dashboard
├── run_id → runs.id (PRIMARY KEY, CASCADE DELETE)
├── roadmap_json
├── revenue_json
├── risk_json
└── budget_json

advisor_messages
├── id (UUID)
├── run_id → runs.id (CASCADE DELETE)
├── role (user | assistant)
├── content
└── created_at

run_costs
├── id
├── run_id → runs.id
├── input_tokens
├── output_tokens
├── estimated_cost
└── created_at
```

**CASCADE DELETE** means: if you delete a run, all its agent outputs, dashboard data, advisor messages, and cost records are automatically deleted too.

---

## 9. SECURITY MEASURES

These are all **actually implemented** (confirmed from code):

| Security Control | How It's Implemented |
|-----------------|---------------------|
| **API Key Security** | Gemini key stored in AWS Secrets Manager, injected via ECS task definition at runtime |
| **CORS Locking** | `config.py` restricts allowed origins to specific S3 and ALB URLs — not wildcard `*` |
| **Security Headers** | `SecurityHeadersMiddleware` adds HSTS, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy to every response |
| **Input Validation** | Pydantic enforces: idea must be 10–2000 chars; user_id max 128 chars |
| **Rate Limiting** | 5 runs/hour/user, 10 runs/day/user, 1,200 global requests/day |
| **Non-root Docker** | Container runs as `appuser`, not root (security hardening) |
| **No hardcoded secrets** | `.gitignore` excludes `.env` files; Secrets Manager used in production |
| **No wildcard CORS** | `allow_credentials=False`, explicit allowed methods and headers only |

---

## 10. DEPLOYMENT

### What's Deployed on AWS

1. **S3 Bucket:** `aethercoo-frontend-724413959665` in `us-east-1` region
   - Configured as static website host
   - Contains the built React app (`dist/` folder output)
   - S3 bucket policy allows public read

2. **ECS Cluster + Fargate Service:**
   - Task family: `aethercoo-backend`
   - Container image: `724413959665.dkr.ecr.us-east-1.amazonaws.com/aethercoo:latest`
   - This means the Docker image is stored in **AWS ECR (Elastic Container Registry)** — like DockerHub but private and within AWS
   - Resources: 512 CPU units (0.5 vCPU), 1024 MB RAM
   - Network mode: `awsvpc` (each task gets its own network interface)
   - Runs as `appuser` (non-root)

3. **Application Load Balancer:** `aethercoo-alb-1943562157.us-east-1.elb.amazonaws.com`
   - Routes traffic to the ECS service
   - Performs health checks using `/health` endpoint

4. **AWS Secrets Manager:** Stores `GEMINI_API_KEY` at ARN `arn:aws:secretsmanager:us-east-1:724413959665:secret:aethercoo/gemini-eyg2q2`

5. **IAM Roles:**
   - `aethercoo-ecs-execution-role` — allows ECS to pull images from ECR and inject secrets from Secrets Manager
   - `aethercoo-ecs-task-role` — permissions the running container has

6. **CloudWatch Logs:** All container logs go to `/ecs/aethercoo-backend` log group in CloudWatch for monitoring

### Alternative/Local Deployment
The project also supports deployment on **Render.com** (backend Docker) + **Netlify** (frontend) as documented in `render.yaml` and `netlify.toml`. This was likely used for testing before AWS.

---

## 11. COMMON QUESTIONS & ANSWERS

**Q: Why did you choose sequential agents instead of parallel?**
> "Because each agent depends on the previous one's output. The Research Agent needs to know the industry and business model from the CEO Agent to search for the right competitors. The Finance Agent needs to know what competitors were found to estimate the correct CAC. Running them in parallel would mean they'd all be working on the raw idea without context from each other, which would produce disconnected, lower-quality outputs. The sequential design is intentional."

**Q: What happens if the Gemini API is down?**
> "We have two layers of protection. First, we have a model fallback chain — if `gemini-2.5-flash` fails, we try `gemini-2.0-flash`, then `gemini-1.5-flash`. Second, the QA Agent specifically has a graceful degradation path — if it fails, the system uses a default risk matrix and continues to the Consolidator. The only case where the entire run fails is if all three model fallbacks are exhausted for agents 1, 2, 3, or 5."

**Q: Why SQLite instead of a cloud database like PostgreSQL or DynamoDB?**
> "SQLite is a deliberate choice for the current scale. It requires zero configuration, no separate server, no additional cost, and is perfectly capable for this workload. The whole database is a single file — `aethercoo.db` — which runs inside the container. If we needed to scale to thousands of concurrent users, we'd migrate to a managed database service like AWS RDS. For a demo system with rate limiting at 1,200 requests/day, SQLite is more than sufficient."

**Q: How does the system guarantee the AI always returns valid JSON?**
> "We use Gemini's structured output feature — we pass `response_mime_type='application/json'` and `response_schema=<our Pydantic schema>`. This forces Gemini to produce output that strictly matches our defined schema. Then we additionally validate it with Pydantic's `model_validate_json()` before accepting it. So there are two layers: Gemini-level enforcement and Python-level validation."

**Q: How do you identify users without login/accounts?**
> "We generate a UUID (Universally Unique Identifier — a random 128-bit number, essentially impossible to guess) in the browser using `window.crypto.randomUUID()` the first time a user visits. This UUID is stored in `localStorage` — a browser storage area that persists across sessions. Every request includes this UUID as `user_id`. It's like a fingerprint for the browser. Users have no password, no email — just an anonymous ID."

**Q: What is a WebSocket and why use it instead of regular HTTP?**
> "A normal HTTP request is one-way: client asks, server answers, connection closes. A WebSocket is a persistent two-way connection — both the client and server can send messages at any time without the overhead of opening a new connection each time. We use it because the agent pipeline takes 1–2 minutes and we want to show the user live log messages as each agent finishes. If we used regular HTTP, the user would stare at a blank screen for 2 minutes and then suddenly see everything. WebSockets let us stream updates in real time."

**Q: What is AWS ECS Fargate and why not just use EC2?**
> "EC2 is a virtual machine — you'd have to choose the OS, manage patches, configure the web server, etc. Fargate is serverless containers — you just say 'run this Docker container' and AWS handles all the underlying infrastructure. You pay only for the CPU and memory while the container is running, and there's no server to maintain. For a focused project like this, Fargate dramatically reduces operational overhead."

**Q: How do you ensure the Gemini API key is never exposed?**
> "The key is stored in AWS Secrets Manager — an encrypted key-value store. The ECS task definition specifies the ARN (the address) of the secret, and when ECS starts the container, it fetches the key and injects it as an environment variable inside the container. The key never appears in source code, never appears in the Docker image, never appears in our Git repository. The only place it exists is inside AWS Secrets Manager and inside the running container's memory."

---

## 12. WHAT IS PLANNED / FUTURE SCOPE

*(These are NOT currently implemented — confirmed by absence in the code)*

- Supabase integration (referenced in `config.py` schema but credentials are `None` by default)
- A remote DBMS sync layer (code exists in `database.py` but `REMOTE_DBMS_URL` defaults to empty, so it's disabled)
- Multi-region deployment
- PDF export (currently only `.txt` download)
- User accounts and authentication

---

*This guide was built by reading every source file in the repository: `orchestrator.py`, `runs.py`, `main.py`, `database.py`, `schemas.py`, `config.py`, `Dockerfile`, `task-definition.json`, `App.jsx`, `GoalInput.jsx`, `AgentPipeline.jsx`, `FinalReport.jsx`, `HistoryView.jsx`, `package.json`, `requirements.txt`, and `README.md`.*
