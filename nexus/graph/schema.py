"""Graph schema definition and introspection utilities."""

from typing import Dict, Any, List
from nexus.graph.client import get_graph


NODE_LABELS = {
    "Person": "An employee or team member with skills, team membership, and project roles.",
    "Team": "An organizational unit or department.",
    "Project": "An active or historical company initiative or product.",
    "Decision": "An Architectural Decision Record (ADR), product choice, or company policy.",
    "Technology": "A software library, database, protocol, or cloud service.",
    "Document": "A design doc, RFC, Slack conversation, or ticket.",
    "Session": "A conversational interaction session with an agent.",
    "Memory": "An episodic, semantic, or procedural memory item stored by agents.",
    "Handoff": "A stateful multi-agent delegation or transfer record."
}

EDGE_TYPES = {
    "WORKS_ON": "(Person)-[:WORKS_ON {role, since}]->(Project)",
    "MADE": "(Person)-[:MADE {date}]->(Decision)",
    "MEMBER_OF": "(Person)-[:MEMBER_OF]->(Team)",
    "KNOWS": "(Person)-[:KNOWS {strength, context}]->(Person)",
    "USES": "(Project)-[:USES {purpose, tier}]->(Technology)",
    "HAS_DECISION": "(Project)-[:HAS_DECISION]->(Decision)",
    "REFERENCES": "(Decision)-[:REFERENCES]->(Document)",
    "SUPERSEDES": "(Decision)-[:SUPERSEDES]->(Decision)",
    "AUTHORED_BY": "(Document)-[:AUTHORED_BY]->(Person)",
    "CONTAINS": "(Session)-[:CONTAINS]->(Memory)",
    "ABOUT": "(Memory)-[:ABOUT]->(AnyNode)",
    "HANDED_OFF_TO": "(Handoff)-[:HANDED_OFF_TO]->(AgentNode)"
}


def get_schema_summary() -> Dict[str, Any]:
    """Returns human and LLM readable schema representation."""
    return {
        "node_labels": NODE_LABELS,
        "relationship_types": EDGE_TYPES,
        "graph_name": "company_brain"
    }


def inspect_live_schema(graph=None) -> Dict[str, Any]:
    """Inspects the schema of the active graph database."""
    g = graph or get_graph()
    labels = []
    relationships = []

    try:
        res = g.query("CALL db.labels()")
        labels = [row[0] for row in res]
    except Exception:
        labels = list(NODE_LABELS.keys())

    try:
        res = g.query("CALL db.relationshipTypes()")
        relationships = [row[0] for row in res]
    except Exception:
        relationships = list(EDGE_TYPES.keys())

    return {
        "labels": labels,
        "relationships": relationships,
        "descriptions": NODE_LABELS,
        "edge_signatures": EDGE_TYPES
    }
