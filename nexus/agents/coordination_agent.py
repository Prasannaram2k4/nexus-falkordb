"""Multi-Agent Coordination & Memory Agent (Track 02)."""

import json
import logging
from typing import Any, Dict, List, Optional
from nexus.memory.memory_manager import memory_manager

logger = logging.getLogger("nexus.coordination_agent")


class CoordinationAgent:
    """Specialist agent managing multi-agent handoffs, state transfers, and cross-session memory recall."""

    def __init__(self, memory=None):
        self.memory = memory or memory_manager

    def recall_context_for_query(self, user_id: str, current_query: str) -> Dict[str, Any]:
        """Recalls past interactions relevant to the user across previous sessions."""
        memories = self.memory.recall_user_memories(user_id=user_id, limit=5)
        if not memories:
            return {"has_history": False, "summary": "No prior conversation history found for this user."}

        past_queries = []
        for m in memories:
            if m.get("type") == "episodic":
                past_queries.append(m.get("user_query", ""))

        relevance_notes = []
        q_lower = current_query.lower()
        for pq in past_queries:
            common_words = set(pq.lower().split()) & set(q_lower.split()) - {"what", "who", "why", "how", "the", "a", "is", "we", "did"}
            if common_words:
                relevance_notes.append(f"In a previous session, you asked about: '{pq}'")

        return {
            "has_history": True,
            "session_count": len(memories),
            "past_memories": memories,
            "relevant_past_queries": relevance_notes,
            "context_prompt": " | ".join(relevance_notes) if relevance_notes else None
        }

    def handoff_task(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        state: Dict[str, Any],
        session_id: str = "global"
    ) -> Dict[str, Any]:
        """Transfers task and state from one agent to another, persisting handoff node in the graph."""
        handoff_id = self.memory.create_agent_handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            task_description=task,
            state=state,
            session_id=session_id
        )
        logger.info(f"Agent handoff created in graph: {handoff_id} from {from_agent} to {to_agent}")
        return {
            "handoff_id": handoff_id,
            "status": "PENDING",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "task": task
        }

    def process_pending_handoffs(self, agent_name: str) -> List[Dict[str, Any]]:
        """Processes and marks pending handoffs for an agent."""
        pending = self.memory.get_pending_handoffs(agent_name)
        for h in pending:
            self.memory.complete_handoff(h.get("id"), "Handoff successfully acknowledged and executed.")
        return pending
