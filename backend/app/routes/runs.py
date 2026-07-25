import logging
import json
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from typing import List

from app.schemas import RunCreate, RunDashboardOutput, AdvisorRequest
from app.database import get_db
from app.agents.orchestrator import run_orchestration, anthropic_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/runs", tags=["runs"])

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, run_id: str, websocket: WebSocket):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket connected for run {run_id}")

    def disconnect(self, run_id: str, websocket: WebSocket):
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        logger.info(f"WebSocket disconnected for run {run_id}")

    async def broadcast(self, run_id: str, message: dict):
        if run_id in self.active_connections:
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message to connection: {str(e)}")

manager = ConnectionManager()


@router.post("")
async def create_run(run_data: RunCreate, background_tasks: BackgroundTasks):
    """
    Submits a business idea. Enforces SQLite rate limits (5 runs/hour) and initiates the sequential pipeline.
    """
    db = get_db()
    
    # 1. Rate Limit Enforcement
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    try:
        past_runs = db.get_runs_created_since(run_data.user_id, one_hour_ago.isoformat() + "Z")
        if len(past_runs) >= 5:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Demo users are restricted to 5 business runs per hour."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting check database error: {str(e)}")

    # 2. Insert Run in 'pending' state
    try:
        run_record = db.create_run(run_data.user_id, run_data.idea)
        run_id = run_record['id']
    except Exception as e:
        logger.error(f"Database insertion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

    # 3. Define the asynchronous callback for broadcasting over Websocket
    async def broadcast_status(message: dict):
        await manager.broadcast(run_id, message)

    # 4. Trigger Orchestrator in background
    background_tasks.add_task(
        run_orchestration,
        run_id=run_id,
        idea=run_data.idea,
        db=db,
        broadcast_callback=broadcast_status
    )

    return {"run_id": run_id, "status": "pending"}


@router.get("")
async def list_runs(user_id: str = Query(..., description="The persistent client UUID")):
    """
    Lists the run history of a specific user.
    """
    db = get_db()
    try:
        runs = db.get_runs_by_user(user_id)
        return runs
    except Exception as e:
        logger.error(f"Failed to fetch runs list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}")
async def get_run(run_id: str):
    """
    Returns the consolidated final dashboard data for a completed run.
    """
    db = get_db()
    
    # Check if run exists and is completed
    run_record = db.get_run(run_id)
    if not run_record:
        raise HTTPException(status_code=404, detail="Business run not found.")
    
    # If not completed, return status metadata
    if run_record['status'] != 'completed':
        # Safely parse ISO format timestamp
        try:
            ts = int(datetime.fromisoformat(run_record['created_at'].replace('Z', '+00:00')).timestamp() * 1000)
        except Exception:
            ts = int(datetime.utcnow().timestamp() * 1000)
        return {
            "id": run_id,
            "goal": run_record['idea_text'],
            "status": run_record['status'],
            "timestamp": ts,
            "is_partial": True
        }

    # Fetch compiled dashboard
    dashboard = db.get_dashboard(run_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard contents not found. Run might have crashed.")
    
    # Fetch CEO properties from audit outputs
    ceo_data = db.get_agent_output(run_id, "ceo") or {}

    # Fetch Research properties
    res_data = db.get_agent_output(run_id, "research") or {}

    # Format output payload to mirror exact React state structure
    roadmap = dashboard['roadmap_json']
    revenue = dashboard['revenue_json']
    risk_info = dashboard['risk_json']
    budget_info = dashboard['budget_json']

    try:
        ts = int(datetime.fromisoformat(run_record['created_at'].replace('Z', '+00:00')).timestamp() * 1000)
    except Exception:
        ts = int(datetime.utcnow().timestamp() * 1000)

    return {
        "id": run_id,
        "timestamp": ts,
        "goal": run_record['idea_text'],
        "status": run_record['status'],
        "subject": ceo_data.get('subject', 'digital product'),
        "businessModel": ceo_data.get('businessModel', 'Software Tool'),
        "modelType": ceo_data.get('modelType', 'saas'),
        "industry": ceo_data.get('industry', 'Technology'),
        "industryType": ceo_data.get('industryType', 'tech'),
        "location": ceo_data.get('location', 'Online / Remote'),
        "audience": ceo_data.get('audience', 'general public'),
        "core_value_prop": ceo_data.get('core_value_prop', ''),
        
        "competitors": res_data.get('competitors', []),
        "swot": res_data.get('swot', {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}),
        "marketAnalysis": res_data.get('marketAnalysis', ''),
        
        "roadmap": roadmap,
        "revenueModel": revenue,
        "risks": risk_info.get('risks', []),
        "trustScore": risk_info.get('trustScore', 75.0),
        "assumptions": risk_info.get('assumptions', []),
        "recommendations": risk_info.get('recommendations', []),
        "financials": budget_info.get('financials', []),
        "metrics": budget_info.get('metrics', {})
    }


@router.delete("/{run_id}")
async def delete_run(run_id: str):
    """
    Deletes a run and cascades deletion of dashboards/agent outputs.
    """
    db = get_db()
    try:
        db.delete_run(run_id)
        return {"status": "deleted", "run_id": run_id}
    except Exception as e:
        logger.error(f"Failed to delete run {run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/advisor")
async def ask_advisor(run_id: str, request: AdvisorRequest):
    """
    Boardroom advisor conversation endpoint. Grounded in the run's compiled SQLite context.
    """
    db = get_db()
    
    # 1. Fetch dashboard context
    dashboard = db.get_dashboard(run_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not compiled yet. Complete the validation sprint first.")
    
    # Grab runs idea
    run_record = db.get_run(run_id)
    idea = run_record['idea_text'] if run_record else "General Startup Idea"

    # Assemble contextual grounding block
    context_str = json.dumps({
        "original_idea": idea,
        "roadmap": dashboard['roadmap_json'],
        "revenue_model": dashboard['revenue_json'],
        "risk_audit": dashboard['risk_json'],
        "financial_budget": dashboard['budget_json']
    }, indent=2)

    system_prompt = f"""You are the senior Boardroom Advisor for AetherCOO.
Your tone is blunt, pragmatic, and directly quantitative. You hate corporate fluff and will call out weak plans.
You are conversing with the founder. Your suggestions MUST be strictly grounded in the following compiled dashboard context:

---
DASHBOARD ANALYSIS CONTEXT:
{context_str}
---

Reference the specific calculated costs (INR/₹), competitor names, SWOT elements, and roadmap steps in your responses to keep recommendations realistic. Never promise success; highlight what needs testing first.
"""

    # Format previous message history for Claude API
    messages = []
    for msg in request.messages:
        role = "user" if msg.sender == "You" else "assistant"
        messages.append({"role": role, "content": msg.text})

    # Append new user question
    messages.append({"role": "user", "content": request.new_message})

    # Execute Claude Call
    try:
        def _call_claude():
            return anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )

        response = await asyncio.to_thread(_call_claude)
        response_text = response.content[0].text
        
        # Save messages to database
        db.save_advisor_messages(run_id, request.new_message, response_text)

        return {"text": response_text}

    except Exception as e:
        logger.error(f"Advisor API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Advisor service error: {str(e)}")


@router.websocket("/{run_id}/stream")
async def websocket_stream(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint streaming live logs and orchestrator status checks.
    """
    await manager.connect(run_id, websocket)
    db = get_db()

    try:
        # Check current run status
        run_record = db.get_run(run_id)
        if run_record:
            current_status = run_record['status']
            # If already finished, emit final state immediately
            if current_status == 'completed':
                # Load dashboard data
                dashboard = db.get_dashboard(run_id)
                if dashboard:
                    # Format standard layout
                    ceo_data = db.get_agent_output(run_id, "ceo") or {}
                    res_data = db.get_agent_output(run_id, "research") or {}
                    
                    try:
                        ts = int(datetime.fromisoformat(run_record['created_at'].replace('Z', '+00:00')).timestamp() * 1000)
                    except Exception:
                        ts = int(datetime.utcnow().timestamp() * 1000)

                    full_payload = {
                        "id": run_id,
                        "timestamp": ts,
                        "goal": run_record['idea_text'],
                        "status": "completed",
                        "subject": ceo_data.get('subject', 'digital product'),
                        "businessModel": ceo_data.get('businessModel', 'Software Tool'),
                        "modelType": ceo_data.get('modelType', 'saas'),
                        "industry": ceo_data.get('industry', 'Technology'),
                        "industryType": ceo_data.get('industryType', 'tech'),
                        "location": ceo_data.get('location', 'Online / Remote'),
                        "audience": ceo_data.get('audience', 'general public'),
                        "core_value_prop": ceo_data.get('core_value_prop', ''),
                        "competitors": res_data.get('competitors', []),
                        "swot": res_data.get('swot', {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}),
                        "marketAnalysis": res_data.get('marketAnalysis', ''),
                        "roadmap": dashboard['roadmap_json'],
                        "revenueModel": dashboard['revenue_json'],
                        "risks": dashboard['risk_json'].get('risks', []),
                        "trustScore": dashboard['risk_json'].get('trustScore', 75.0),
                        "assumptions": dashboard['risk_json'].get('assumptions', []),
                        "recommendations": dashboard['risk_json'].get('recommendations', []),
                        "financials": dashboard['budget_json'].get('financials', []),
                        "metrics": dashboard['budget_json'].get('metrics', {})
                    }
                    await websocket.send_json({
                        "type": "completed",
                        "dashboard": full_payload
                    })

        # Keep connection open for incoming pings or live updates
        while True:
            # We just wait for any message to keep WebSocket alive (ping/pong)
            data = await websocket.receive_text()
            # Send simple pong
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(run_id, websocket)
