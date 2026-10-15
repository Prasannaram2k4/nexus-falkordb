"""Ingestion Specialist Agent for turning docs, tickets, and chats into graph nodes (Track 03)."""

import re
import uuid
import logging
from typing import Any, Dict, List, Optional
from nexus.mcp.tools import mcp_tools

logger = logging.getLogger("nexus.ingestion_agent")


class IngestionAgent:
    """Specialist agent that converts unstructured docs, chats, and RFCs into FalkorDB graph nodes & edges."""

    def __init__(self, mcp=None):
        self.mcp = mcp or mcp_tools

    def ingest_document(
        self,
        title: str,
        content: str,
        author_email: str,
        doc_type: str = "RFC",
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingests a document, extracts decisions/technologies, and writes nodes and edges to FalkorDB."""
        doc_id = f"doc_{uuid.uuid4().hex[:6]}"
        clean_title = title.replace("'", "\\'")
        clean_url = (url or f"https://wiki.acme.corp/docs/{doc_id}").replace("'", "\\'")

        # 1. Create Document node
        create_doc = (
            f"CREATE (d:Document {{"
            f"id: '{doc_id}', "
            f"title: '{clean_title}', "
            f"type: '{doc_type}', "
            f"url: '{clean_url}'"
            f"}})"
        )
        self.mcp.execute_query(create_doc)

        # 2. Link Author if Person exists
        link_author = (
            f"MATCH (d:Document), (p:Person) "
            f"WHERE d.id = '{doc_id}' AND p.email = '{author_email}' "
            f"CREATE (d)-[:AUTHORED_BY]->(p)"
        )
        self.mcp.execute_query(link_author)

        # 3. Extract Decisions from content
        created_decisions = []
        decision_matches = re.findall(r"(?:Decision|Decided|Outcome):\s*([^\n\.]+)", content, re.IGNORECASE)
        for dec_text in decision_matches:
            dec_id = f"dec_{uuid.uuid4().hex[:6]}"
            clean_dec = dec_text.strip().replace("'", "\\'")
            create_dec = (
                f"CREATE (dec:Decision {{"
                f"id: '{dec_id}', "
                f"title: '{clean_dec}', "
                f"rationale: 'Extracted from {clean_title}', "
                f"outcome: 'Approved'"
                f"}})"
            )
            self.mcp.execute_query(create_dec)

            # Link Decision to Document
            link_dec_doc = (
                f"MATCH (dec:Decision), (d:Document) "
                f"WHERE dec.id = '{dec_id}' AND d.id = '{doc_id}' "
                f"CREATE (dec)-[:REFERENCES]->(d)"
            )
            self.mcp.execute_query(link_dec_doc)

            # Link Person to Decision
            link_dec_person = (
                f"MATCH (p:Person), (dec:Decision) "
                f"WHERE p.email = '{author_email}' AND dec.id = '{dec_id}' "
                f"CREATE (p)-[:MADE]->(dec)"
            )
            self.mcp.execute_query(link_dec_person)
            created_decisions.append(clean_dec)

        return {
            "status": "success",
            "document_id": doc_id,
            "title": title,
            "author": author_email,
            "decisions_extracted": created_decisions
        }

    def ingest_slack_thread(
        self,
        channel: str,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Ingests a Slack thread containing technical discussions or incident postmortems."""
        combined_text = "\n".join([f"{m.get('user', 'unknown')}: {m.get('text', '')}" for m in messages])
        first_user = messages[0].get("user", "engineer@acme.corp") if messages else "engineer@acme.corp"
        
        return self.ingest_document(
            title=f"Slack Thread #{channel}: Technical Discussion",
            content=combined_text,
            author_email=first_user if "@" in first_user else f"{first_user}@acme.corp",
            doc_type="Slack",
            url=f"slack://channels/{channel}"
        )
