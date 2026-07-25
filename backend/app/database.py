import sqlite3
import json
import uuid
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class SQLiteDatabase:
    def __init__(self, db_path="aethercoo.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable CASCADE deletes in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        logger.info(f"Initializing SQLite database at: {os.path.abspath(self.db_path)}")
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                idea_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                viability_score REAL,
                created_at TEXT NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS run_agent_outputs (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                output_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(run_id, agent_name),
                FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS run_dashboard (
                run_id TEXT PRIMARY KEY,
                roadmap_json TEXT NOT NULL,
                revenue_json TEXT NOT NULL,
                risk_json TEXT NOT NULL,
                budget_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS advisor_messages (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS run_costs (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    def get_runs_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM runs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_runs_created_since(self, user_id: str, since_iso: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id FROM runs WHERE user_id = ? AND created_at >= ?", (user_id, since_iso))
            return [dict(r) for r in cursor.fetchall()]

    def create_run(self, user_id: str, idea_text: str) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, user_id, idea_text, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, user_id, idea_text, 'pending', created_at)
            )
            conn.commit()
            return {
                "id": run_id, 
                "user_id": user_id, 
                "idea_text": idea_text, 
                "status": "pending", 
                "created_at": created_at
            }

    def update_run_status(self, run_id: str, status: str, viability_score: float = None):
        with self._get_connection() as conn:
            if viability_score is not None:
                conn.execute(
                    "UPDATE runs SET status = ?, viability_score = ? WHERE id = ?", 
                    (status, viability_score, run_id)
                )
            else:
                conn.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))
            conn.commit()

    def delete_run(self, run_id: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            conn.commit()

    def save_agent_output(self, run_id: str, agent_name: str, output_dict: dict):
        out_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        output_json = json.dumps(output_dict)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO run_agent_outputs (id, run_id, agent_name, output_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (out_id, run_id, agent_name, output_json, created_at)
            )
            conn.commit()

    def get_agent_output(self, run_id: str, agent_name: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT output_json FROM run_agent_outputs WHERE run_id = ? AND agent_name = ?", (run_id, agent_name))
            row = cursor.fetchone()
            return json.loads(row['output_json']) if row else None

    def save_dashboard(self, run_id: str, roadmap: list, revenue: dict, risk: dict, budget: dict):
        created_at = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO run_dashboard (run_id, roadmap_json, revenue_json, risk_json, budget_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, json.dumps(roadmap), json.dumps(revenue), json.dumps(risk), json.dumps(budget), created_at)
            )
            conn.commit()

    def get_dashboard(self, run_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM run_dashboard WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "roadmap_json": json.loads(row['roadmap_json']),
                    "revenue_json": json.loads(row['revenue_json']),
                    "risk_json": json.loads(row['risk_json']),
                    "budget_json": json.loads(row['budget_json'])
                }
            return None

    def save_cost(self, run_id: str, input_tokens: int, output_tokens: int, cost: float):
        cost_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO run_costs (id, run_id, input_tokens, output_tokens, estimated_cost, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (cost_id, run_id, input_tokens, output_tokens, cost, created_at)
            )
            conn.commit()

    def save_advisor_messages(self, run_id: str, user_content: str, assistant_content: str):
        created_at = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO advisor_messages (id, run_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), run_id, 'user', user_content, created_at)
            )
            conn.execute(
                "INSERT INTO advisor_messages (id, run_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), run_id, 'assistant', assistant_content, created_at)
            )
            conn.commit()

db_instance = SQLiteDatabase()

def get_db() -> SQLiteDatabase:
    return db_instance
