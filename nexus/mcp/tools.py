"""Model Context Protocol (MCP) tool implementations for FalkorDB."""

import json
import logging
from typing import Any, Dict, List, Optional
from nexus.graph.client import get_graph, QueryResult
from nexus.graph.schema import inspect_live_schema, NODE_LABELS, EDGE_TYPES

logger = logging.getLogger("nexus.mcp")


class FalkorDBMCPTools:
    """Implements FalkorDB MCP tools for agentic reasoning and memory."""

    def __init__(self, graph_name: Optional[str] = None):
        self.graph_name = graph_name
        self.graph = get_graph(graph_name)

    def get_graph_schema(self) -> Dict[str, Any]:
        """Tool: get_graph_schema - Discovers graph schema (nodes, edges, descriptions)."""
        schema = inspect_live_schema(self.graph)
        return {
            "status": "success",
            "graph_name": self.graph.name if hasattr(self.graph, "name") else "company_brain",
            "labels": schema["labels"],
            "relationships": schema["relationships"],
            "label_descriptions": schema["descriptions"],
            "edge_patterns": schema["edge_signatures"]
        }

    def get_node_schema(self, label: str) -> Dict[str, Any]:
        """Tool: get_node_schema - Returns properties and sample node for a specific label."""
        description = NODE_LABELS.get(label, "Custom entity node.")
        try:
            res = self.graph.query(f"MATCH (n:{label}) RETURN n LIMIT 1")
            sample = None
            if len(res) > 0 and len(res[0]) > 0:
                node = res[0][0]
                if hasattr(node, "to_dict"):
                    sample = node.to_dict()
                elif hasattr(node, "properties"):
                    sample = {"properties": node.properties}
            return {
                "label": label,
                "description": description,
                "sample_properties": sample
            }
        except Exception as e:
            return {"label": label, "description": description, "error": str(e)}

    def query_graph(self, cypher: str) -> Dict[str, Any]:
        """Tool: query_graph - Runs Cypher query, returns records, headers, and paths."""
        try:
            res = self.graph.query(cypher)
            rows = []
            paths = []
            for row in res:
                formatted_row = []
                for item in row:
                    if hasattr(item, "to_dict"):
                        formatted_row.append(item.to_dict())
                    elif hasattr(item, "properties"):
                        formatted_row.append(dict(item.properties))
                    else:
                        formatted_row.append(item)
                    if isinstance(item, str) and "-[:" in item and "]->" in item:
                        paths.append(item)
                rows.append(formatted_row)

            return {
                "status": "success",
                "cypher": cypher,
                "header": res.header,
                "count": len(rows),
                "records": rows,
                "paths": list(set(paths))
            }
        except Exception as e:
            logger.error(f"Error querying graph: {e}")
            return {"status": "error", "cypher": cypher, "error": str(e)}

    def query_graph_readonly(self, cypher: str) -> Dict[str, Any]:
        """Tool: query_graph_readonly - Read-only safe Cypher query."""
        clean = cypher.strip().upper()
        if any(keyword in clean for keyword in ["CREATE ", "MERGE ", "DELETE ", "SET ", "DROP "]):
            return {
                "status": "error",
                "error": "Mutation keywords (CREATE, MERGE, DELETE, SET, DROP) are disallowed in query_graph_readonly."
            }
        return self.query_graph(cypher)

    def execute_query(self, cypher: str) -> Dict[str, Any]:
        """Tool: execute_query - Executes a mutation (CREATE/MERGE/SET) to add facts to the graph."""
        try:
            res = self.graph.query(cypher)
            return {
                "status": "success",
                "cypher": cypher,
                "result": [list(r) for r in res]
            }
        except Exception as e:
            return {"status": "error", "cypher": cypher, "error": str(e)}

    def trace_connection(self, source_entity: str, target_entity: str) -> Dict[str, Any]:
        """Tool: trace_connection - Traces paths between two entities in the knowledge graph."""
        cypher = (
            f"MATCH (a), (b) "
            f"WHERE (a.name CONTAINS '{source_entity}' OR a.id CONTAINS '{source_entity}' OR a.title CONTAINS '{source_entity}') "
            f"AND (b.name CONTAINS '{target_entity}' OR b.id CONTAINS '{target_entity}' OR b.title CONTAINS '{target_entity}') "
            f"RETURN a, b"
        )
        try:
            nodes_res = self.graph.query(cypher)
            if not nodes_res or len(nodes_res) == 0:
                return {
                    "status": "not_found",
                    "message": f"Could not locate matching nodes for '{source_entity}' and '{target_entity}'"
                }
            src_node = nodes_res[0][0]
            tgt_node = nodes_res[0][1]
            
            if hasattr(self.graph, "find_path") and hasattr(src_node, "id") and hasattr(tgt_node, "id"):
                path_steps = self.graph.find_path(src_node.id, tgt_node.id)
                return {
                    "status": "success",
                    "source": src_node.to_dict() if hasattr(src_node, "to_dict") else str(src_node),
                    "target": tgt_node.to_dict() if hasattr(tgt_node, "to_dict") else str(tgt_node),
                    "path_steps": path_steps
                }
            return {"status": "success", "direct_match": True, "source": str(src_node), "target": str(tgt_node)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def blast_radius(self, entity_name: str) -> Dict[str, Any]:
        """Tool: blast_radius - Runs graph algorithm to compute impact of outage/change to an entity."""
        if hasattr(self.graph, "blast_radius"):
            res = self.graph.blast_radius(entity_name)
            return {"status": "success", **res}
        return {"status": "error", "message": "Graph engine does not support blast radius"}

    def get_centrality(self, top_k: int = 5) -> Dict[str, Any]:
        """Tool: get_centrality - Runs NetworkX centrality to find key decision makers & bottlenecks."""
        if hasattr(self.graph, "key_influencers"):
            leaders = self.graph.key_influencers(top_k=top_k)
            return {"status": "success", "key_influencers": leaders}
        return {"status": "error", "message": "Centrality algorithm not available"}

    def audit_graph_conflicts(self) -> Dict[str, Any]:
        """Tool: audit_graph_conflicts - Scans graph for superseded decisions, policy conflicts & risks."""
        if hasattr(self.graph, "audit_conflicts"):
            conflicts = self.graph.audit_conflicts()
            return {"status": "success", "conflict_count": len(conflicts), "conflicts": conflicts}
        return {"status": "error", "message": "Audit not supported on current graph"}


# Singleton MCP tools instance
mcp_tools = FalkorDBMCPTools()
