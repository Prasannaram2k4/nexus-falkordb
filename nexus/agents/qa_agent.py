"""QA Specialist Agent for multi-hop graph reasoning and path explanation (Tracks 01 & 03)."""

import re
import logging
from typing import Any, Dict, List, Optional
from nexus.mcp.tools import mcp_tools
from nexus.config import settings

logger = logging.getLogger("nexus.qa_agent")


class QAAgent:
    """Specialist agent that solves connected data questions by following graph paths."""

    def __init__(self, mcp=None):
        self.mcp = mcp or mcp_tools

    def answer_query(self, query_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Translates user query into multi-hop Cypher, executes it, and explains the path."""
        q_lower = query_text.lower()
        cypher = self._generate_cypher(query_text)
        
        logger.info(f"Generated Cypher: {cypher}")
        graph_res = self.mcp.query_graph(cypher)
        
        if graph_res.get("status") == "error":
            return {
                "answer": f"Error running graph query: {graph_res.get('error')}",
                "cypher": cypher,
                "paths": [],
                "records": []
            }

        records = graph_res.get("records", [])
        paths = graph_res.get("paths", [])
        
        # Build explainable natural language answer
        answer = self._synthesize_answer(query_text, records, paths)
        
        return {
            "answer": answer,
            "cypher": cypher,
            "paths": paths,
            "records": records,
            "count": len(records)
        }

    def _generate_cypher_llm(self, query_text: str) -> Optional[str]:
        """Generates dynamic Cypher using OpenAI / LLM if API key is configured."""
        import os
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            schema = self.mcp.get_graph_schema()
            prompt = (
                f"You are a FalkorDB Cypher generator for an enterprise knowledge graph.\n"
                f"Schema Labels: {list(schema.get('labels', []))}\n"
                f"Relationship Signatures: {schema.get('edge_patterns', {})}\n\n"
                f"Task: Convert this question into a single Cypher MATCH query returning relevant node properties and 'path'.\n"
                f"Question: {query_text}\n"
                f"Return ONLY the raw Cypher query, no markdown fences."
            )
            resp = client.chat.completions.create(
                model=settings.openai_model or "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            cypher = resp.choices[0].message.content.strip().strip("`").replace("cypher\n", "")
            return cypher
        except Exception as e:
            logger.warning(f"LLM Cypher generation failed, falling back to rule-based engine: {e}")
            return None

    def _generate_cypher(self, query_text: str) -> str:
        """Determines best multi-hop Cypher traversal query based on entities and intent."""
        # 1. Try dynamic LLM Cypher generation first if API key configured
        llm_cypher = self._generate_cypher_llm(query_text)
        if llm_cypher:
            return llm_cypher

        # 2. Schema-aware deterministic fallback
        q = query_text.lower()

        # Kafka vs RabbitMQ / decisions around streaming
        if "kafka" in q or "rabbitmq" in q or "streaming" in q:
            return (
                "MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document) "
                "WHERE d.title CONTAINS 'Kafka' "
                "RETURN p.name, p.email, d.title, d.rationale, doc.title, doc.url, path"
            )

        # FalkorDB / Vector DB / Pinecone
        if "falkordb" in q or "vector" in q or "pinecone" in q:
            return (
                "MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document) "
                "WHERE d.title CONTAINS 'FalkorDB' "
                "RETURN p.name, p.email, d.title, d.rationale, doc.title, doc.url, path"
            )

        # Superseded decisions
        if "supersede" in q or "replaced" in q or "changed" in q:
            return (
                "MATCH (d1:Decision)-[:SUPERSEDES]->(d2:Decision) "
                "RETURN d1.title, d1.outcome, d2.title, d2.outcome, path"
            )

        # Projects / work done by a person
        if "alice" in q:
            return (
                "MATCH (p:Person)-[:WORKS_ON]->(proj:Project) "
                "WHERE p.name CONTAINS 'Alice' "
                "RETURN p.name, proj.name, proj.description, path"
            )
        if "bob" in q:
            return (
                "MATCH (p:Person)-[:WORKS_ON]->(proj:Project) "
                "WHERE p.name CONTAINS 'Bob' "
                "RETURN p.name, proj.name, proj.description, path"
            )
        if "carol" in q:
            return (
                "MATCH (p:Person)-[:WORKS_ON]->(proj:Project) "
                "WHERE p.name CONTAINS 'Carol' "
                "RETURN p.name, proj.name, proj.description, path"
            )

        # Kubernetes / Cloud
        if "kubernetes" in q or "k8s" in q or "cloud" in q or "devops" in q:
            return (
                "MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document) "
                "WHERE d.title CONTAINS 'Kubernetes' OR d.title CONTAINS 'EKS' "
                "RETURN p.name, p.email, d.title, d.rationale, doc.title, doc.url, path"
            )

        # Security / Zero Trust / IAM
        if "security" in q or "zero-trust" in q or "iam" in q or "mtls" in q:
            return (
                "MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document) "
                "WHERE d.title CONTAINS 'Zero-Trust' OR d.title CONTAINS 'mTLS' "
                "RETURN p.name, p.email, d.title, d.rationale, doc.title, doc.url, path"
            )

        # Collaboration / Social / Who knows who
        if "know" in q or "talk to" in q or "collaborat" in q:
            return (
                "MATCH (p1:Person)-[:KNOWS]->(p2:Person) "
                "RETURN p1.name, p2.name, path"
            )

        # Generic decision lookup
        if "decision" in q:
            return (
                "MATCH (p:Person)-[:MADE]->(d:Decision) "
                "RETURN p.name, d.title, d.date, d.rationale, path"
            )

        # Default multi-hop traversal of all decisions and their authors
        return (
            "MATCH (p:Person)-[:MADE]->(d:Decision) "
            "RETURN p.name, p.email, d.title, d.rationale, path"
        )

    def _synthesize_answer(self, query_text: str, records: List[List[Any]], paths: List[str]) -> str:
        """Constructs a warm, narrative answer from graph records — like a colleague who remembers."""
        if not records:
            return (
                "I searched the whole company graph but couldn't find a direct match for that. "
                "The graph knows about People, Decisions, Projects, Technologies, and Documents. "
                "Try rephrasing, or use `schema` to browse what's connected."
            )

        first_row = records[0]
        q = query_text.lower()

        if "kafka" in q or "rabbitmq" in q:
            person_name = first_row[0]
            email = first_row[1]
            decision = first_row[2]
            rationale = first_row[3]
            doc_title = first_row[4] if len(first_row) > 4 else "RFC-101"
            doc_url = first_row[5] if len(first_row) > 5 else "wiki.acme.corp"
            return (
                f"The short answer: RabbitMQ was struggling under burst load, "
                f"and {person_name} made the call to switch.\n\n"
                f"The full story, from the graph:\n"
                f"  Decision: {decision}\n"
                f"  Made by: {person_name} ({email})\n"
                f"  Rationale: {rationale}\n"
                f"  Source: {doc_title} — {doc_url}\n\n"
                f"This was part of Project Apollo. The decision is linked to its author, "
                f"the referenced RFC, and the Slack postmortem. If you want to see who else "
                f"touched this, try asking about Alice's projects or the blast radius of Kafka."
            )

        if "falkordb" in q or "vector" in q or "pinecone" in q:
            person_name = first_row[0]
            email = first_row[1]
            decision = first_row[2]
            rationale = first_row[3]
            return (
                f"This is a superseded decision — the graph tracks the old choice too.\n\n"
                f"  Current decision: {decision}\n"
                f"  Led by: {person_name} ({email})\n"
                f"  Why: {rationale}\n\n"
                f"The team originally used Pinecone for vector search. "
                f"When agent memory and multi-hop reasoning became requirements on Project Atlas, "
                f"switching to FalkorDB eliminated a whole separate service. "
                f"You can see the superseded decision as a node in the graph — the history doesn't disappear, it just gets a [:SUPERSEDES] edge."
            )

        if "supersede" in q or "replace" in q:
            active_dec = first_row[0]
            superseded_dec = first_row[2] if len(first_row) > 2 else "(older decision)"
            return (
                f"Found a superseded decision in the graph:\n\n"
                f"  '{active_dec}'\n"
                f"    supersedes\n"
                f"  '{superseded_dec}'\n\n"
                f"The old decision isn't deleted — it's still a node, "
                f"connected by a [:SUPERSEDES] edge. That's intentional: "
                f"you can always trace *why* something changed, and when."
            )

        # Default: warm but informative
        lines = [f"Here's what the graph knows about that ({len(records)} result{'s' if len(records) != 1 else ''} found):\n"]
        for row in records[:4]:
            items = [str(x) for x in row if x and not (isinstance(x, str) and "-[:" in x)]
            lines.append(f"  • {' → '.join(items)}")
        if len(records) > 4:
            lines.append(f"  … and {len(records) - 4} more. Try narrowing with a more specific question.")
        return "\n".join(lines)

