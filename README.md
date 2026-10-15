# 🧠 NEXUS — FalkorDB Company Brain & Multi-Agent Context Engine

> *"We've all been in that meeting where no one remembers why we chose Kafka. NEXUS was built so you never have to have that meeting again."*

[![FalkorDB](https://img.shields.io/badge/FalkorDB-Graph%20Engine-FF3366?style=flat-square&logo=redis&logoColor=white)](https://falkordb.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20%2B%20WebUI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tracks](https://img.shields.io/badge/Tracks-01%20%7C%2002%20%7C%2003-7928CA?style=flat-square)](#hackathon-tracks)
[![Tests](https://img.shields.io/badge/Tests-20%20passing-22c55e?style=flat-square)](#tests)

---

## 💡 The Story Behind NEXUS

Every engineering team has a graveyard of "why did we do this?" decisions buried in Confluence pages no one reads, Slack threads no one finds, and the institutional memory of people who left the company.

When a new engineer joins, they spend their first month asking "why is it set up this way?" When a post-mortem happens, half the meeting is archaeology. When an agent tries to help, it answers from hallucination, not from the actual reasoning that happened.

**NEXUS** solves this by putting your company's knowledge into a graph — where people, projects, decisions, and documents are nodes, and the relationships between them are edges. Then it hands that graph to a team of AI agents that can follow those relationships, remember what they learn across sessions, and show you exactly which path through the graph led to each answer.

The graph isn't decoration. Remove FalkorDB and NEXUS stops working. That's the point.

---

## 🏆 Hackathon Tracks

NEXUS enters **all three tracks**:

| Track | What NEXUS Does |
|:------|:----------------|
| **🕵️ Track 01: Agents on Connected Data** | Multi-hop Cypher traversals across Person → Decision → Document. Graph algorithms (blast radius, centrality) as MCP tools. Every answer includes the exact traversal path. |
| **🤖 Track 02: Agent Memory & Coordination** | Sessions and memories persist as `(:Session)-[:CONTAINS]->(:Memory)` nodes. Return users get context recalled from prior sessions. Multi-agent handoffs are graph nodes, not in-memory state. |
| **🧠 Track 03: Company Brain** | One graph connecting People, Teams, Projects, Decisions, Technologies, Documents. Ask why something was decided. Trace it back to the author, the RFC, the Slack thread. See what got superseded. |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│          Web UI (Vis.js live graph) · CLI · REST API            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │  Master Orchestrator  │  ← routes by intent
                └─┬──────────┬──────────┘
          ┌───────┘          │          └──────────┐
    ┌─────▼──────┐    ┌──────▼──────┐    ┌────────▼──────┐
    │  QA Agent  │    │ Coord Agent │    │ Ingest Agent  │
    │ Multi-hop  │    │ Memory +    │    │ Docs → Graph  │
    │  Cypher    │    │ Handoffs    │    │  Nodes        │
    └─────┬──────┘    └──────┬──────┘    └────────┬──────┘
          └──────────────────┼────────────────────┘
                    ┌────────▼────────┐
                    │   MCP Tools     │  ← get_schema, query_graph,
                    │   (8 tools)     │     blast_radius, centrality,
                    └────────┬────────┘     audit, trace, execute
                             │
                    ┌────────▼────────┐
                    │    FalkorDB     │  ← THE GRAPH IS THE STATE
                    │  Graph Engine   │
                    │                 │
                    │  (:Person)      │
                    │  (:Decision)    │
                    │  (:Project)     │
                    │  (:Technology)  │
                    │  (:Document)    │
                    │  (:Session)     │  ← Track 02: persistent memory
                    │  (:Memory)      │
                    │  (:Handoff)     │  ← Track 02: agent coordination
                    └─────────────────┘
```

---

## 📊 Graph Data Model

```cypher
// — People, teams, and org structure —
(:Person  {id, name, email, role, expertise[]})
(:Team    {id, name, lead})

// — What the company works on —
(:Project    {id, name, status, description})
(:Technology {id, name, category, version})
(:Document   {id, title, url, type})
(:Decision   {id, title, date, rationale, outcome})

// — How everything connects —
(Person)-[:WORKS_ON  {role, since}]  ->(Project)
(Person)-[:MADE      {date}]         ->(Decision)
(Person)-[:MEMBER_OF]                ->(Team)
(Person)-[:KNOWS     {strength}]     ->(Person)
(Project)-[:USES     {purpose}]      ->(Technology)
(Project)-[:HAS_DECISION]            ->(Decision)
(Decision)-[:REFERENCES]             ->(Document)
(Decision)-[:SUPERSEDES]             ->(Decision)   // ← decision archaeology
(Document)-[:AUTHORED_BY]            ->(Person)

// — Agent memory (Track 02) —
(:Session {id, user_id, tenant_id, created_at})
(:Memory  {id, type, user_query, agent_summary, reasoning_path, timestamp})
(:Handoff {id, from_agent, to_agent, task, state_payload, status})

(Session)-[:CONTAINS]->(Memory)
(Session)-[:CONTAINS]->(Handoff)
(Memory)-[:ABOUT]   ->(AnyEntity)
```

> **Why this model?** Decisions are first-class nodes, not JSON blobs in a document. Every decision links to its author, references the source RFC, and can be superseded by a newer decision — with the full history preserved as edges.

---

## 🚀 Quickstart

### Option A — Zero external setup (runs embedded)

NEXUS ships with an embedded Cypher engine. No Docker, no account, no API keys needed:

```bash
git clone https://github.com/YOUR_USERNAME/nexus-falkordb
cd nexus-falkordb

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full 3-track automated demo
python -m nexus.cli demo

# Start the web UI (open http://localhost:8000)
python -m nexus.cli ui
```

### Option B — With live FalkorDB (Docker)

```bash
docker compose up --build
```

- **NEXUS Web UI + API**: http://localhost:8000
- **Swagger / API Docs**: http://localhost:8000/docs
- **FalkorDB Browser**: http://localhost:3000

### Option C — FalkorDB Cloud

1. Create a free instance at [app.falkordb.cloud](https://app.falkordb.cloud)
2. Copy `.env.example` to `.env` and fill in `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_PASSWORD`
3. `python -m nexus.cli seed` then `python -m nexus.cli ui`

---

## 💻 CLI Commands

```bash
# Full 3-track showcase (best starting point for judges)
python -m nexus.cli demo

# Ask any question with full Cypher path explanation
python -m nexus.cli query "Why did we choose Kafka over RabbitMQ?" --explain

# Interactive chat (persistent cross-session memory)
python -m nexus.cli chat

# Inspect the live graph schema
python -m nexus.cli schema

# Re-seed the Acme Corp knowledge graph
python -m nexus.cli seed
```

---

## 🌐 REST API

| Method | Endpoint | What it does |
|:-------|:---------|:-------------|
| `GET`  | `/health` | FalkorDB connection status + graph mode |
| `GET`  | `/schema` | Node labels and relationship signatures |
| `POST` | `/query` | Natural language → multi-hop Cypher → human answer |
| `POST` | `/cypher` | Execute raw Cypher directly |
| `POST` | `/ingest` | Ingest an RFC/doc into the graph as linked nodes |
| `GET`  | `/memory/{user_id}` | All episodic memories for a user across sessions |
| `POST` | `/handoff` | Create a multi-agent coordination handoff node |
| `GET`  | `/handoffs/{agent}` | Pending handoffs for an agent |
| `GET`  | `/graph/viz` | JSON payload for the live graph visualizer |
| `GET`  | `/blast-radius/{entity}` | Graph algorithm: what does this node affect? |
| `GET`  | `/centrality` | Graph algorithm: who are the key influencers? |
| `GET`  | `/audit` | Autonomous audit: find conflicts, spawn handoff nodes |

---

## 🎬 Demo Walkthrough

### Track 01 — Multi-Hop Graph Reasoning

```
User: "Why did we choose Kafka over RabbitMQ?"

NEXUS Cypher:
  MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document)
  WHERE d.title CONTAINS 'Kafka'
  RETURN p.name, d.title, d.rationale, doc.title, path

Answer:
  Alice Chen made the decision to adopt Kafka after RabbitMQ hit
  memory limits during Black Friday. The reasoning lives in RFC-101.

Graph Path:
  (Alice Chen)-[:MADE]->(Choose Kafka over RabbitMQ)-[:REFERENCES]->(RFC-101)
```

### Track 02 — Memory Across Sessions

```
Session 1: User asks about Kafka → stored as (:Memory) node in FalkorDB

Session 2 (new browser tab, new day):
  User: "Who else worked with Alice on streaming?"

  NEXUS: "💡 In your previous session, you asked about Kafka vs RabbitMQ.
          Building on that context: Bob Miller collaborated with Alice on
          Project Apollo. Here's who's connected..."
```

### Track 03 — Decision Archaeology

```
User: "What vector database approach did we supersede?"

Graph Path:
  (Adopt FalkorDB as Graph+Memory Layer)-[:SUPERSEDES]->(Initial Vector Search with Pinecone)

Answer: In Q1, the team started with Pinecone for vector search. After
        discovering graph relationships were needed for agent reasoning,
        Bob led the switch to FalkorDB — which combined graph + vector
        in one store, eliminating the separate Pinecone dependency.
```

### Autonomous Agent Action (Tracks 01 + 02)

```
User: "Audit graph conflicts"

→ Agent finds: Dave Vance owns two conflicting security decisions
→ Agent WRITES a :Handoff node to FalkorDB (not just a text answer)
→ Another agent can PICK UP that handoff from the graph
→ The graph is the coordination layer, not just the answer layer
```

---

## 🧪 Tests

```bash
pytest -v
```

20 tests, all passing in < 0.5s:

- **`test_graph.py`** — Schema introspection, single/multi-hop traversals, SUPERSEDES path, blast_radius algorithm, centrality, audit
- **`test_memory.py`** — Session creation, episodic memory recall, agent handoff state machine
- **`test_agents.py`** — QA Kafka multi-hop, ingestion, orchestrator routing, blast radius, autonomous audit
- **`test_api.py`** — Health check, schema, query, Cypher execution, graph viz

---

## 📁 Repository Structure

```
nexus-falkordb/
├── nexus/
│   ├── config.py               # Settings: FalkorDB, OpenAI, graph name
│   ├── cli.py                  # Rich terminal CLI (demo, chat, query, seed, ui)
│   ├── graph/
│   │   ├── client.py           # FalkorDB client (live) + embedded Cypher fallback
│   │   ├── schema.py           # Node labels and relationship type definitions
│   │   └── seed.py             # Acme Corp synthetic dataset (62 Cypher statements)
│   ├── mcp/
│   │   └── tools.py            # 8 MCP tools (query, trace, blast_radius, centrality, audit...)
│   ├── memory/
│   │   └── memory_manager.py   # Episodic, semantic, procedural memory + agent handoffs
│   ├── agents/
│   │   ├── orchestrator.py     # Intent router: routes queries to the right specialist
│   │   ├── qa_agent.py         # Multi-hop Cypher Q&A + path explanation
│   │   ├── ingestion_agent.py  # Unstructured doc/Slack → graph nodes
│   │   └── coordination_agent.py # Cross-session recall + multi-agent handoffs
│   ├── api/
│   │   └── main.py             # FastAPI app (lifespan, all endpoints)
│   └── ui/
│       └── index.html          # Dark-mode web UI: Vis.js graph canvas + agent chat
├── tests/
│   ├── test_graph.py
│   ├── test_memory.py
│   ├── test_agents.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml          # FalkorDB + FalkorDB Browser + NEXUS API
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Environment Variables

```bash
# Copy and edit:
cp .env.example .env
```

| Variable | Default | Description |
|:---------|:--------|:------------|
| `FALKORDB_HOST` | `localhost` | FalkorDB server host |
| `FALKORDB_PORT` | `6379` | FalkorDB server port |
| `FALKORDB_PASSWORD` | *(empty)* | Password (FalkorDB Cloud needs this) |
| `GRAPH_NAME` | `nexus` | Graph name inside FalkorDB |
| `OPENAI_API_KEY` | *(optional)* | Enables LLM-generated Cypher; falls back to rule-based without it |
| `FORCE_EMBEDDED` | `false` | Force embedded engine even if FalkorDB server is available |

---

## 🤔 Why FalkorDB?

- **The graph IS the state** — agent memory, handoffs, company knowledge all live in the same graph. Pull FalkorDB out and the system doesn't work.
- **Sub-millisecond multi-hop traversals** — following Person → Decision → Document → RFC chains happens in one query, not a chain of API calls.
- **Cypher is the reasoning language** — MCP tools expose graph traversal as structured, auditable operations.
- **Graph algorithms as agent tools** — betweenness centrality and blast radius aren't bolted on; they run natively against the relationship graph.

---

*Built for the [FalkorDB Graph Hacks Hackathon](https://falkordb.com/hackathon/) — Oct 15–18, 2026*
*Synthetic data only. No private or proprietary information is loaded into any graph.*
