"""
AetherCOO Backend — Integration Tests
Tests critical API routes against a real FastAPI test client with an isolated SQLite DB.
Run: cd backend && pip install pytest httpx && pytest tests/ -v
"""
import os
import pytest
import tempfile
from fastapi.testclient import TestClient

# Point DB to a temp file so tests don't pollute production data
os.environ["AETHERCOO_DB_PATH"] = tempfile.mktemp(suffix=".test.db")
os.environ["GEMINI_API_KEY"] = ""  # Tests run without real API key

from app.main import app

client = TestClient(app, raise_server_exceptions=True)


# ── Health ──────────────────────────────────────────────────────────────────

def test_health_endpoint_returns_200():
    """The /health liveness probe must return 200 with correct payload."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "service" in body


# ── Security Headers ─────────────────────────────────────────────────────────

def test_security_headers_present():
    """Every response must include OWASP-recommended security headers."""
    response = client.get("/health")
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff", "Missing X-Content-Type-Options"
    assert headers.get("x-frame-options") == "DENY", "Missing X-Frame-Options"
    assert "x-xss-protection" in headers, "Missing X-XSS-Protection"
    assert "strict-transport-security" in headers, "Missing HSTS header"


# ── Run Creation ─────────────────────────────────────────────────────────────

def test_create_run_returns_run_id():
    """POST /api/runs should create a run and return a UUID run_id."""
    payload = {
        "idea": "A SaaS platform for small restaurant owners to manage reservations and walk-ins.",
        "user_id": "test-user-00000001"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "run_id" in body
    assert len(body["run_id"]) == 36  # UUID format


def test_create_run_idea_too_short_returns_422():
    """POST /api/runs with an idea < 10 chars should return 422 Unprocessable Entity."""
    payload = {"idea": "SaaS", "user_id": "test-user-00000001"}
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422


def test_create_run_idea_too_long_returns_422():
    """POST /api/runs with an idea > 2000 chars should return 422."""
    payload = {"idea": "x" * 2001, "user_id": "test-user-00000001"}
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422


def test_create_run_empty_user_id_returns_422():
    """POST /api/runs with empty user_id should be rejected."""
    payload = {"idea": "A valid idea that is long enough to pass validation.", "user_id": ""}
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422


def test_create_run_missing_fields_returns_422():
    """POST /api/runs with missing fields should fail validation."""
    response = client.post("/api/runs", json={"idea": "test idea here"})
    assert response.status_code == 422


# ── Run Retrieval ─────────────────────────────────────────────────────────────

def test_get_run_not_found_returns_404():
    """GET /api/runs/{non_existent_id} should return 404."""
    response = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_runs_by_user_returns_array():
    """GET /api/runs?user_id=... should return an array."""
    response = client.get("/api/runs?user_id=test-list-user-00001")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Diag Check ────────────────────────────────────────────────────────────────

def test_diag_check_no_api_key_returns_error_status():
    """GET /api/runs/diag/check without GEMINI_API_KEY should return error status (not 404!)."""
    response = client.get("/api/runs/diag/check")
    assert response.status_code == 200  # It's a 200 with error in body, not a 404
    body = response.json()
    assert body["status"] == "error"
    assert "GEMINI_API_KEY" in body["message"]


# ── Delete Run ────────────────────────────────────────────────────────────────

def test_delete_nonexistent_run_returns_200():
    """DELETE on a non-existent run_id should still return 200 (idempotent delete)."""
    response = client.delete("/api/runs/00000000-0000-0000-0000-999999999999")
    assert response.status_code == 200


# ── Rate Limiting ─────────────────────────────────────────────────────────────

def test_rate_limit_per_user():
    """A single user should be blocked after 5 runs in 1 hour."""
    user_id = "rate-limit-test-user-999"
    payload_template = {
        "user_id": user_id,
        "idea": "A delivery app for organic groceries targeting health-conscious millennials."
    }
    
    responses = []
    for _ in range(6):  # Submit 6 runs; 6th should hit hourly rate limit
        r = client.post("/api/runs", json=payload_template)
        responses.append(r.status_code)
    
    # At least one response should be 429 (rate limit hit)
    assert 429 in responses, f"Expected a 429, got statuses: {responses}"
