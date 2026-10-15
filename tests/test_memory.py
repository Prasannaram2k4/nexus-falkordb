"""Unit tests for agent memory and coordination (Track 02)."""

import pytest
from nexus.graph.client import get_graph
from nexus.memory.memory_manager import GraphMemoryManager


@pytest.fixture
def memory():
    g = get_graph("test_mem_graph")
    return GraphMemoryManager(g)


def test_session_creation(memory):
    sess = memory.get_or_create_session("sess_test_1", user_id="test_user")
    assert sess["session_id"] == "sess_test_1"
    assert sess["created"] is True

    # Idempotent retrieval
    sess_again = memory.get_or_create_session("sess_test_1", user_id="test_user")
    assert sess_again["created"] is False


def test_record_interaction_and_recall(memory):
    memory.record_interaction(
        session_id="sess_100",
        user_id="user_charlie",
        user_message="Why did we choose Kafka?",
        agent_response="Because of throughput.",
        reasoning_path="(Person)-[:MADE]->(Decision)",
        entities_referenced=["Kafka"]
    )

    memories = memory.recall_user_memories("user_charlie")
    assert len(memories) >= 1
    assert memories[0]["user_query"] == "Why did we choose Kafka?"
    assert memories[0]["type"] == "episodic"


def test_agent_handoff_flow(memory):
    ho_id = memory.create_agent_handoff(
        from_agent="Planner",
        to_agent="QA_Agent",
        task_description="Traverse security cluster dependencies",
        state={"cluster_id": "eks-prod-1"}
    )
    assert ho_id.startswith("ho_")

    pending = memory.get_pending_handoffs("QA_Agent")
    assert len(pending) >= 1
    assert pending[0]["id"] == ho_id
    assert pending[0]["status"] == "PENDING"

    memory.complete_handoff(ho_id, "Completed analysis.")
    # Verify no longer pending
    pending_after = memory.get_pending_handoffs("QA_Agent")
    assert all(h["id"] != ho_id for h in pending_after)
