"""Unit tests for agents (Orchestrator, QA, Ingestion)."""

import pytest
from nexus.graph.client import get_graph
from nexus.graph.seed import seed_company_graph
from nexus.agents.orchestrator import OrchestratorAgent
from nexus.agents.qa_agent import QAAgent
from nexus.agents.ingestion_agent import IngestionAgent


@pytest.fixture(scope="module")
def setup_env():
    g = get_graph()
    seed_company_graph(g)


def test_qa_agent_kafka(setup_env):
    qa = QAAgent()
    res = qa.answer_query("Why did we choose Kafka over RabbitMQ?")
    assert "Choose Kafka over RabbitMQ" in res["answer"]
    assert len(res["paths"]) > 0
    assert "Alice Chen" in res["answer"]


def test_ingestion_agent(setup_env):
    ingest = IngestionAgent()
    res = ingest.ingest_document(
        title="RFC-999: Adopt ClickHouse for Analytics",
        content="Decision: Choose ClickHouse for real-time analytics aggregation over Snowflake.",
        author_email="bob@acme.corp"
    )
    assert res["status"] == "success"
    assert len(res["decisions_extracted"]) == 1


def test_orchestrator_multi_turn_recall(setup_env):
    orch = OrchestratorAgent()
    
    # Session 1
    res1 = orch.process_request("What is Project Atlas about?", user_id="tester_1", session_id="s1")
    assert "answer" in res1
    assert "reasoning_path" in res1

    # Session 2 - check cross-session recall
    res2 = orch.process_request("Who works on Project Atlas?", user_id="tester_1", session_id="s2")
    assert "recalled_past_context" in res2


def test_orchestrator_blast_radius(setup_env):
    orch = OrchestratorAgent()
    res = orch.process_request("What is the blast radius if Kafka fails?")
    assert "Blast Radius" in res["answer"]
    assert "Project Apollo" in res["answer"]
    assert len(res["all_paths"]) > 0


def test_orchestrator_autonomous_audit(setup_env):
    orch = OrchestratorAgent()
    res = orch.process_request("Audit graph conflicts and trigger autonomous remediation")
    assert "Autonomous Graph Audit" in res["answer"]
    assert "Handoff" in res["answer"]
