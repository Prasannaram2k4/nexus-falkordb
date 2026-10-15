"""Agent Memory and Multi-Agent Coordination Layer in FalkorDB (Track 02)."""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from nexus.graph.client import get_graph

logger = logging.getLogger("nexus.memory")


class GraphMemoryManager:
    """Manages episodic, semantic, and procedural memory + agent coordination state in FalkorDB."""

    def __init__(self, graph=None):
        self.graph = graph or get_graph()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_or_create_session(self, session_id: str, user_id: str = "default_user", tenant_id: str = "acme_corp") -> Dict[str, Any]:
        """Creates or retrieves a persistent Session node in the graph."""
        clean_sid = session_id.replace("'", "")
        clean_uid = user_id.replace("'", "")
        clean_tid = tenant_id.replace("'", "")
        
        # Check if session exists
        check_cypher = f"MATCH (s:Session) WHERE s.id = '{clean_sid}' RETURN s"
        res = self.graph.query(check_cypher)
        if len(res) > 0 and len(res[0]) > 0:
            return {"session_id": clean_sid, "created": False}

        # Create session node
        ts = self._now_iso()
        create_cypher = (
            f"CREATE (s:Session {{"
            f"id: '{clean_sid}', "
            f"user_id: '{clean_uid}', "
            f"tenant_id: '{clean_tid}', "
            f"created_at: '{ts}', "
            f"interaction_count: 0"
            f"}})"
        )
        self.graph.query(create_cypher)
        
        # Link session to user person if exists
        link_user = f"MATCH (p:Person), (s:Session) WHERE p.id = '{clean_uid}' AND s.id = '{clean_sid}' CREATE (s)-[:BY]->(p)"
        self.graph.query(link_user)
        
        return {"session_id": clean_sid, "created": True}

    def record_interaction(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        agent_response: str,
        reasoning_path: Optional[str] = None,
        entities_referenced: Optional[List[str]] = None,
        tenant_id: str = "acme_corp"
    ) -> str:
        """Stores an episodic memory turn connected to the session."""
        self.get_or_create_session(session_id, user_id, tenant_id)
        
        mem_id = f"mem_{uuid.uuid4().hex[:8]}"
        ts = self._now_iso()
        clean_user_msg = user_message.replace("'", "\\'").replace("\n", " ")
        clean_agent_resp = agent_response[:300].replace("'", "\\'").replace("\n", " ")
        clean_path = (reasoning_path or "").replace("'", "\\'").replace("\n", " ")
        
        # Create Memory node
        create_mem = (
            f"CREATE (m:Memory {{"
            f"id: '{mem_id}', "
            f"type: 'episodic', "
            f"user_id: '{user_id}', "
            f"tenant_id: '{tenant_id}', "
            f"timestamp: '{ts}', "
            f"user_query: '{clean_user_msg}', "
            f"agent_summary: '{clean_agent_resp}', "
            f"reasoning_path: '{clean_path}'"
            f"}})"
        )
        self.graph.query(create_mem)

        # Link Session to Memory
        link_cypher = (
            f"MATCH (s:Session), (m:Memory) "
            f"WHERE s.id = '{session_id}' AND m.id = '{mem_id}' "
            f"CREATE (s)-[:CONTAINS]->(m)"
        )
        self.graph.query(link_cypher)

        # Connect memory to mentioned entities in the knowledge graph
        if entities_referenced:
            for ent in entities_referenced:
                clean_ent = ent.replace("'", "")
                link_ent = (
                    f"MATCH (m:Memory), (e) "
                    f"WHERE m.id = '{mem_id}' AND (e.name CONTAINS '{clean_ent}' OR e.title CONTAINS '{clean_ent}' OR e.id = '{clean_ent}') "
                    f"CREATE (m)-[:ABOUT]->(e)"
                )
                self.graph.query(link_ent)

        return mem_id

    def store_semantic_fact(
        self,
        user_id: str,
        subject: str,
        predicate: str,
        object_val: str,
        confidence: float = 1.0,
        tenant_id: str = "acme_corp"
    ) -> str:
        """Stores long-term semantic knowledge learned about a user or domain."""
        fact_id = f"fact_{uuid.uuid4().hex[:8]}"
        ts = self._now_iso()
        clean_subj = subject.replace("'", "\\'")
        clean_pred = predicate.replace("'", "\\'")
        clean_obj = object_val.replace("'", "\\'")

        create_fact = (
            f"CREATE (m:Memory {{"
            f"id: '{fact_id}', "
            f"type: 'semantic', "
            f"user_id: '{user_id}', "
            f"tenant_id: '{tenant_id}', "
            f"subject: '{clean_subj}', "
            f"predicate: '{clean_pred}', "
            f"object: '{clean_obj}', "
            f"confidence: {confidence}, "
            f"created_at: '{ts}'"
            f"}})"
        )
        self.graph.query(create_fact)
        return fact_id

    def store_procedural_pattern(
        self,
        query_pattern: str,
        cypher_template: str,
        notes: str = ""
    ) -> str:
        """Stores procedural memory: learned Cypher query templates that succeeded."""
        proc_id = f"proc_{uuid.uuid4().hex[:8]}"
        clean_pat = query_pattern.replace("'", "\\'")
        clean_tmpl = cypher_template.replace("'", "\\'")
        clean_notes = notes.replace("'", "\\'")
        
        stmt = (
            f"CREATE (m:Memory {{"
            f"id: '{proc_id}', "
            f"type: 'procedural', "
            f"pattern: '{clean_pat}', "
            f"cypher: '{clean_tmpl}', "
            f"notes: '{clean_notes}'"
            f"}})"
        )
        self.graph.query(stmt)
        return proc_id

    def recall_user_memories(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recalls past interactions, preferences, and facts for a user across sessions."""
        cypher = f"MATCH (m:Memory) WHERE m.user_id = '{user_id}' RETURN m"
        res = self.graph.query(cypher)
        memories = []
        for row in res:
            if len(row) > 0:
                item = row[0]
                if hasattr(item, "properties"):
                    memories.append(dict(item.properties))
                elif isinstance(item, dict):
                    memories.append(item)
        return memories[:limit]

    def create_agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        task_description: str,
        state: Dict[str, Any],
        session_id: str = "global"
    ) -> str:
        """Track 02: Multi-agent coordination and state handoff recorded in the graph."""
        handoff_id = f"ho_{uuid.uuid4().hex[:8]}"
        ts = self._now_iso()
        state_str = json.dumps(state).replace("'", "\\'")
        clean_task = task_description.replace("'", "\\'")

        create_cypher = (
            f"CREATE (h:Handoff {{"
            f"id: '{handoff_id}', "
            f"from_agent: '{from_agent}', "
            f"to_agent: '{to_agent}', "
            f"session_id: '{session_id}', "
            f"task: '{clean_task}', "
            f"state_payload: '{state_str}', "
            f"status: 'PENDING', "
            f"created_at: '{ts}'"
            f"}})"
        )
        self.graph.query(create_cypher)

        # Link handoff to session
        link_sess = f"MATCH (s:Session), (h:Handoff) WHERE s.id = '{session_id}' AND h.id = '{handoff_id}' CREATE (s)-[:CONTAINS]->(h)"
        self.graph.query(link_sess)

        return handoff_id

    def get_pending_handoffs(self, agent_name: str) -> List[Dict[str, Any]]:
        """Finds pending coordination handoffs for an agent."""
        cypher = f"MATCH (h:Handoff) WHERE h.to_agent = '{agent_name}' AND h.status = 'PENDING' RETURN h"
        res = self.graph.query(cypher)
        handoffs = []
        for row in res:
            if len(row) > 0:
                h = row[0]
                props = h.properties if hasattr(h, "properties") else h
                handoffs.append(dict(props))
        return handoffs

    def complete_handoff(self, handoff_id: str, result_summary: str) -> bool:
        """Marks an agent handoff completed with result."""
        clean_res = result_summary.replace("'", "\\'")
        cypher = f"MATCH (h:Handoff) WHERE h.id = '{handoff_id}' SET h.status = 'COMPLETED', h.result = '{clean_res}'"
        self.graph.query(cypher)
        return True


# Global memory manager
memory_manager = GraphMemoryManager()
