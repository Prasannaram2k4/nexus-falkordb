# 🌐 NEXUS Live Deployment & Visual Demo Guide

This guide explains how to run the **Live Visual Web UI**, connect to **FalkorDB Cloud**, and deploy the agent system for judges.

---

## 🖥 1. Run the Live Interactive Web UI (Instant Local Demo)

The codebase includes an interactive frontend dashboard with live graph physics and multi-agent chat:

```bash
# From the project directory:
./run.sh ui
```
Then open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

### What you see in the Web Dashboard:
1. **Interactive FalkorDB Graph Canvas (Vis.js physics)**:
   - Colored entity nodes: `Person` (cyan), `Decision` (emerald), `Project` (indigo), `Technology` (amber), `Document` (pink), `Memory` (purple).
   - Drag, zoom, and click any node to open its full properties inspector drawer.
2. **Multi-Agent Chat Studio**:
   - Ask any natural language question.
   - The agent retrieves the multi-hop Cypher path and displays the answer.
   - **Path Highlight**: The nodes and edges traversed by the agent light up in real time on the graph!
3. **Session & User Switcher (Track 02: Agent Memory)**:
   - Switch user between Alice, Bob, Carol, or Judge.
   - Switch sessions (Session #1 vs Session #2) to see cross-session episodic memory in action.
4. **Live Ingestion Studio (Track 03: Company Brain)**:
   - Click **"Ingest Doc"**, paste a new RFC or Slack postmortem, click **Ingest**, and watch new nodes dynamically appear on the graph.

---

## ☁️ 2. Connecting to FalkorDB Cloud (Free Tier)

If you want to run against a real cloud-hosted FalkorDB database instead of the embedded engine:

1. Sign up for free at **[https://app.falkordb.cloud/](https://app.falkordb.cloud/)**
2. Create a free database instance.
3. Copy your connection host, port, and password.
4. Set them in your `.env` file or export them:
   ```bash
   export FALKORDB_HOST="your-instance.falkordb.cloud"
   export FALKORDB_PORT=6379
   export FALKORDB_PASSWORD="your-cloud-password"
   export FALKORDB_GRAPH_NAME="company_brain"
   ```
5. Launch the app:
   ```bash
   ./run.sh ui
   ```
   The top badge will immediately display **"FalkorDB Online" (Connected to Live Cloud Instance)**.

---

## 🐳 3. Full Production Stack with Docker Compose

To run the complete server suite with the official FalkorDB engine, FalkorDB Browser UI, and NEXUS API:

```bash
docker compose up --build
```

Access services:
* **NEXUS Visual Web Dashboard & Chat**: `http://localhost:8000`
* **Swagger Interactive REST Documentation**: `http://localhost:8000/docs`
* **Official FalkorDB Graph Browser UI**: `http://localhost:3000`

---

## 🚀 4. One-Click Cloud Deployment (Render / Railway)

### Deploying to Render
1. Push this repository to GitHub.
2. In Render, click **New Web Service** and link your repo.
3. Configure:
   - **Runtime**: `Python 3` or `Docker`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn nexus.api.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `FALKORDB_HOST`: (Your FalkorDB Cloud host, or leave blank to use embedded engine)
   - `FALKORDB_PASSWORD`: (Your FalkorDB Cloud password)
   - `OPENAI_API_KEY`: (Optional, for dynamic LLM Cypher generation)

---

## 🎥 5. Recommended 3-Minute Demo Video Flow for Judges

1. **0:00 - 0:45 (The Problem & The Visual Graph)**:
   - Open `http://localhost:8000`.
   - Show the force-directed graph with people, projects, decisions, and tech.
   - Explain: *"Standard chatbots treat context as flat text chunks. NEXUS puts the entire company into FalkorDB so decisions and people are connected nodes."*
2. **0:45 - 1:45 (Track 01 & Track 03: Multi-Hop Reasoning)**:
   - Click the prompt: *"Why did we choose Kafka over RabbitMQ, and who worked on it?"*
   - Show the answer: Alice Chen, RFC-101 reference, Slack message postmortem.
   - Show the bottom **Active Cypher Traversal Path** and watch the graph highlight the 3-hop connection.
3. **1:45 - 2:30 (Track 02: Cross-Session Memory & Coordination)**:
   - Switch to **Session #2** in the top bar.
   - Ask: *"Who else worked with Alice?"*
   - Show the purple **Memory Recall badge**: *"💡 In a previous session, you asked about Kafka..."*
   - Open the Ingestion Modal, paste a new decision, and watch it wire into the graph.
4. **2:30 - 3:00 (Architecture & Conclusion)**:
   - Show the test results (`15/15 passed`) and Docker / FalkorDB Cloud connectivity.
