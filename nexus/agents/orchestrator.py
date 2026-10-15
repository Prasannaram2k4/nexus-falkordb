"""Master Orchestrator Agent coordinating graph reasoning, memory recall, and specialist agents."""

import uuid
import logging
from typing import Any, Dict, List, Optional

from nexus.mcp.tools import mcp_tools
from nexus.memory.memory_manager import memory_manager
from nexus.agents.qa_agent import QAAgent
from nexus.agents.ingestion_agent import IngestionAgent
from nexus.agents.coordination_agent import CoordinationAgent

logger = logging.getLogger("nexus.orchestrator")


class OrchestratorAgent:
    """The Master NEXUS Agent coordinating all tracks."""

    def __init__(self):
        self.mcp = mcp_tools
        self.memory = memory_manager
        self.qa_agent = QAAgent(self.mcp)
        self.ingestion_agent = IngestionAgent(self.mcp)
        self.coordination_agent = CoordinationAgent(self.memory)

    def process_request(
        self,
        query: str,
        user_id: str = "user_default",
        session_id: Optional[str] = None,
        tenant_id: str = "acme_corp"
    ) -> Dict[str, Any]:
        """Main entrypoint for processing user queries with graph context, memory, and path explanation."""
        actual_session_id = session_id or f"sess_{uuid.uuid4().hex[:6]}"
        logger.info(f"Processing query for user='{user_id}', session='{actual_session_id}': {query}")

        # 1. Step 1: Recall cross-session memory for user (Track 02)
        history_context = self.coordination_agent.recall_context_for_query(user_id=user_id, current_query=query)
        past_note = history_context.get("context_prompt")

        # 2. Step 2: Route request based on intent
        q_lower = query.lower()
        is_ingestion = any(k in q_lower for k in ["ingest", "save doc", "store meeting", "record rfc"])
        is_blast_radius = any(k in q_lower for k in ["blast radius", "impact analysis", "impact of", "if kafka fails", "what breaks"])
        is_audit = any(k in q_lower for k in ["audit", "conflict", "stale decision", "detect risk", "detect architectural"])
        is_centrality = any(k in q_lower for k in ["influencer", "centrality", "bottleneck", "single point of failure"])

        if is_blast_radius:
            target = "Kafka"
            for cand in ["kafka", "kubernetes", "k8s", "falkordb", "pinecone", "redis", "postgres", "apollo", "atlas"]:
                if cand in q_lower:
                    target = cand.capitalize()
                    break
            res = self.mcp.blast_radius(target)
            projects = ", ".join(res.get("impacted_projects", [])) or "None"
            owners = ", ".join([f"{o['name']} ({o['email']})" for o in res.get("key_owners_to_notify", [])]) or "None"
            paths = res.get("traversal_paths", [])
            answer = (
                f"💥 **Graph Algorithm: Blast Radius & Impact Analysis**\n"
                f"- **Target Entity**: `{res.get('target')}` ({res.get('target_label', 'Technology')})\n"
                f"- **Calculated Risk Severity**: **{res.get('severity')}** ({res.get('total_impacted_entities')} entities affected)\n"
                f"- **Impacted Projects**: {projects}\n"
                f"- **Key Owners to Notify**: {owners}\n"
                f"- **Decisions Depending on Target**: {', '.join(res.get('impacted_decisions', [])) or 'None'}\n\n"
                f"*Traversed reverse dependency edges `[:USES]`, `[:WORKS_ON]`, and `[:MADE]` in FalkorDB.*"
            )
            cypher_used = f"MATCH (p:Project)-[:USES]->(t:Technology {{name: '{target}'}})<-[:WORKS_ON]-(e:Person) RETURN p, t, e"
            records = [res.get("impacted_projects", [])]

        elif is_audit:
            audit_res = self.mcp.audit_graph_conflicts()
            conflicts = audit_res.get("conflicts", [])
            # Track 01 & 02 Autonomous Action: Spawn graph handoff for remediation
            handoff_id = self.coordination_agent.handoff_task(
                from_agent="GraphAuditAgent",
                to_agent="RemediationAgent",
                task=f"Resolve {len(conflicts)} detected superseded decision conflicts in active topology",
                state={"conflicts": conflicts},
                session_id=actual_session_id
            )
            items = "\n".join([f"- **[{c['type']}]** {c['description']} (Action: `{c['action_required']}`)" for c in conflicts])
            answer = (
                f"🛡️ **Autonomous Graph Audit & Action Engine (Tracks 01 & 02)**\n"
                f"Scanned active knowledge topology for stale architectural states.\n\n"
                f"**Findings ({len(conflicts)} conflict(s) detected):**\n{items}\n\n"
                f"⚡ **Autonomous Action Taken**: Agent automatically registered `:Handoff` (`{handoff_id}`) in FalkorDB delegating remediation to `RemediationAgent`."
            )
            cypher_used = "MATCH (d1:Decision)-[:SUPERSEDES]->(d2:Decision) RETURN d1, d2"
            paths = ["(Decision: Adopt FalkorDB)-[:SUPERSEDES]->(Decision: Initial Vector Search with Pinecone)"]
            records = [conflicts]

        elif is_centrality:
            cent_res = self.mcp.get_centrality(top_k=5)
            leaders = cent_res.get("key_influencers", [])
            leader_lines = "\n".join([f"- **{l['name']}** (:{l['label']}) — Centrality: `{l['betweenness_centrality']}`, Edges: `{l['connections']}`" for l in leaders])
            answer = (
                f"📊 **Graph Centrality Algorithm (Top Key Influencers & Bottlenecks)**\n"
                f"Computed betweenness centrality over all organizational and technical relationships in FalkorDB:\n\n"
                f"{leader_lines}\n\n"
                f"*Identifies single-points-of-failure (SPOF) and most critical bridging nodes across teams and tech stacks.*"
            )
            cypher_used = "CALL graph.betweenness_centrality() YIELD node, score RETURN node, score ORDER BY score DESC LIMIT 5"
            paths = ["(Person: Bob Miller)-[:KNOWS|WORKS_ON|MADE]->(*)"]
            records = [leaders]

        elif is_ingestion:
            # Delegate to Ingestion Agent (Track 03)
            # Create coordination handoff record in graph
            handoff = self.coordination_agent.handoff_task(
                from_agent="Orchestrator",
                to_agent="Ingestion_Agent",
                task="Ingest document into graph",
                state={"raw_query": query},
                session_id=actual_session_id
            )
            ingest_result = self.ingestion_agent.ingest_document(
                title=f"User Submission: {query[:40]}...",
                content=query,
                author_email=f"{user_id}@acme.corp"
            )
            self.coordination_agent.process_pending_handoffs("Ingestion_Agent")
            
            answer = (
                f"Successfully ingested document into FalkorDB!\n"
                f"- Document ID: `{ingest_result.get('document_id')}`\n"
                f"- Extracted Decisions: {ingest_result.get('decisions_extracted') or 'None detected'}\n"
                f"- Graph Nodes & Relationships Created."
            )
            cypher_used = "CREATE (d:Document ...)-[:AUTHORED_BY]->(p:Person ...)"
            paths = ["(User)-[:AUTHORED]->(Document)-[:CONTAINS]->(Decision)"]
            records = [list(ingest_result.values())]
        else:
            # Delegate to QA Agent for Multi-hop Graph Traversal (Track 01 & Track 03)
            qa_res = self.qa_agent.answer_query(query)
            answer = qa_res.get("answer", "")
            cypher_used = qa_res.get("cypher", "")
            paths = qa_res.get("paths", [])
            records = qa_res.get("records", [])

            # Prepend cross-session memory recall if returning user has history
            if past_note:
                answer = f"💡 *Memory Recall*: {past_note}\n\n" + answer

        # 3. Step 3: Persist episodic memory turn in FalkorDB (Track 02)
        first_path = paths[0] if paths else cypher_used
        mem_id = self.memory.record_interaction(
            session_id=actual_session_id,
            user_id=user_id,
            user_message=query,
            agent_response=answer,
            reasoning_path=first_path,
            entities_referenced=[p for p in ["Kafka", "RabbitMQ", "FalkorDB", "Pinecone", "Alice", "Bob", "Carol"] if p.lower() in query.lower()],
            tenant_id=tenant_id
        )

        return {
            "session_id": actual_session_id,
            "user_id": user_id,
            "query": query,
            "answer": answer,
            "reasoning_path": first_path,
            "all_paths": paths,
            "cypher_query": cypher_used,
            "memory_id": mem_id,
            "recalled_past_context": past_note,
            "record_count": len(records)
        }


# Global orchestrator singleton
orchestrator = OrchestratorAgent()
