import pytest
from fastapi.testclient import TestClient
from glc_v3.gateway import app

client = TestClient(app)


def test_healthz_endpoint():
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert len(data["providers"]) == 5


def test_agent_card_endpoint():
    res = client.get("/.well-known/agent-card.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "glc_v3 Autonomous Gateway Agent"


def test_run_execution_endpoint():
    payload = {
        "prompt": "Search for 'Python asyncio best practices'",
        "tenant_id": "course",
        "project_id": "s13",
        "user_id": "student-01",
        "agent_id": "assistant"
    }
    res = client.post("/v1/agent/runs", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert data["snapshot"]["finished"] is True
