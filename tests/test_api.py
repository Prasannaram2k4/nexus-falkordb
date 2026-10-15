"""API endpoint integration tests."""

import pytest
from starlette.testclient import TestClient
from nexus.api.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "FalkorDB"


def test_api_schema():
    res = client.get("/schema")
    assert res.status_code == 200
    data = res.json()
    assert "labels" in data
    assert "relationships" in data


def test_api_query():
    payload = {
        "query": "Why did we choose Kafka over RabbitMQ?",
        "user_id": "api_test_user",
        "session_id": "api_sess_1"
    }
    res = client.post("/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "reasoning_path" in data
    assert "cypher_query" in data


def test_api_cypher():
    payload = {
        "cypher": "MATCH (p:Person) RETURN p.name LIMIT 3",
        "read_only": True
    }
    res = client.post("/cypher", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["records"]) > 0


def test_api_graph_viz():
    res = client.get("/graph/viz")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["node_count"] > 0
