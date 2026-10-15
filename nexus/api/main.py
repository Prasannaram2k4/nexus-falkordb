"""FastAPI REST API for NEXUS Company Brain."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from nexus.graph.client import get_graph, graph_manager
from nexus.graph.schema import inspect_live_schema
from nexus.graph.seed import seed_company_graph
from nexus.mcp.tools import mcp_tools
from nexus.memory.memory_manager import memory_manager
from nexus.agents.orchestrator import orchestrator
from nexus.config import settings

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    g = get_graph()
    if hasattr(g, "nodes") and len(g.nodes) == 0:
        seed_company_graph(g)
    yield


app = FastAPI(
    title="NEXUS - FalkorDB Company Brain API",
    description="Context layer, agent memory, and explainable multi-hop reasoning over FalkorDB graph.",
    version="1.0.0",
    lifespan=lifespan
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query from user")
    user_id: str = Field(default="demo_user", description="User ID for isolated memory")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    tenant_id: str = Field(default="acme_corp", description="Tenant ID")


class CypherRequest(BaseModel):
    cypher: str = Field(..., description="Cypher query to execute")
    read_only: bool = Field(default=False, description="Enforce read-only")


class IngestRequest(BaseModel):
    title: str
    content: str
    author_email: str = "engineer@acme.corp"
    doc_type: str = "RFC"
    url: Optional[str] = None


class HandoffRequest(BaseModel):
    from_agent: str
    to_agent: str
    task: str
    state: Dict[str, Any]
    session_id: str = "global"


import os
from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
def root():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>NEXUS API</h1><p>Visit <a href='/docs'>API Docs</a></p>")


@app.get("/api/info")
def api_info():
    return {
        "service": "NEXUS Company Brain",
        "database": "FalkorDB",
        "live_connection": graph_manager.is_live,
        "tracks": ["01: Connected Data", "02: Agent Memory", "03: Company Brain"],
        "docs_url": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "FalkorDB",
        "is_live_server": graph_manager.is_live,
        "graph_name": settings.falkordb_graph_name
    }


@app.get("/schema")
def get_schema():
    return inspect_live_schema()


@app.post("/seed")
def seed_graph():
    g = get_graph()
    count = seed_company_graph(g)
    return {"status": "success", "statements_executed": count}


@app.post("/query")
def process_query(req: QueryRequest):
    try:
        result = orchestrator.process_request(
            query=req.query,
            user_id=req.user_id,
            session_id=req.session_id,
            tenant_id=req.tenant_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cypher")
def execute_cypher(req: CypherRequest):
    if req.read_only:
        return mcp_tools.query_graph_readonly(req.cypher)
    return mcp_tools.query_graph(req.cypher)


@app.post("/ingest")
def ingest_doc(req: IngestRequest):
    from nexus.agents.ingestion_agent import IngestionAgent
    agent = IngestionAgent(mcp_tools)
    return agent.ingest_document(
        title=req.title,
        content=req.content,
        author_email=req.author_email,
        doc_type=req.doc_type,
        url=req.url
    )


@app.get("/memory/{user_id}")
def get_user_memory(user_id: str, limit: int = 10):
    return {
        "user_id": user_id,
        "memories": memory_manager.recall_user_memories(user_id, limit=limit)
    }


@app.post("/handoff")
def create_handoff(req: HandoffRequest):
    handoff_id = memory_manager.create_agent_handoff(
        from_agent=req.from_agent,
        to_agent=req.to_agent,
        task_description=req.task,
        state=req.state,
        session_id=req.session_id
    )
    return {"status": "created", "handoff_id": handoff_id}


@app.get("/handoffs/{agent_name}")
def get_pending_handoffs(agent_name: str):
    return {
        "agent": agent_name,
        "pending_handoffs": memory_manager.get_pending_handoffs(agent_name)
    }


@app.get("/graph/viz")
def get_graph_viz():
    """Returns nodes and edges formatted for visual graph rendering."""
    g = get_graph()
    nodes_data = []
    edges_data = []

    if hasattr(g, "nodes") and hasattr(g, "edges"):
        for nid, node in g.nodes.items():
            nodes_data.append({
                "id": nid,
                "label": node.label,
                "name": node.get("name") or node.get("title") or node.get("id"),
                "properties": node.properties
            })
        for edge in g.edges:
            edges_data.append({
                "source": edge.src_node,
                "target": edge.dest_node,
                "relation": edge.relation,
                "properties": edge.properties
            })
    return {
        "node_count": len(nodes_data),
        "edge_count": len(edges_data),
        "nodes": nodes_data,
        "edges": edges_data
    }


@app.get("/blast-radius/{entity}")
def get_blast_radius(entity: str):
    return mcp_tools.blast_radius(entity)


@app.get("/centrality")
def get_centrality(top_k: int = 5):
    return mcp_tools.get_centrality(top_k=top_k)


@app.post("/audit")
def run_autonomous_audit():
    return orchestrator.process_request("audit graph conflicts")
