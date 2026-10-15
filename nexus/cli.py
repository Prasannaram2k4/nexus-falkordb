"""Interactive Rich CLI for NEXUS Company Brain."""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.tree import Tree

from nexus.graph.client import get_graph
from nexus.graph.seed import seed_company_graph
from nexus.graph.schema import inspect_live_schema
from nexus.agents.orchestrator import orchestrator
from nexus.mcp.tools import mcp_tools

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]🧠 NEXUS[/bold cyan] : [bold white]The FalkorDB Company Brain & Multi-Agent Context Engine[/bold white]\n"
        "[dim]Tracks: [cyan]01[/cyan] Connected Data  |  [green]02[/green] Agent Memory  |  [magenta]03[/magenta] Company Brain[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def cmd_seed():
    """Seeds the company knowledge graph."""
    print_banner()
    console.print("[bold yellow]⚡ Seeding FalkorDB Knowledge Graph with Acme Corp data...[/bold yellow]")
    g = get_graph()
    count = seed_company_graph(g)
    console.print(f"[bold green]✔ Graph seeded successfully with {count} statements![/bold green]")


def cmd_schema():
    """Displays the graph schema."""
    print_banner()
    schema = inspect_live_schema()
    
    table = Table(title="Knowledge Graph Schema (FalkorDB)", border_style="cyan")
    table.add_column("Node Label", style="bold cyan")
    table.add_column("Description", style="white")
    
    for lbl, desc in schema.get("descriptions", {}).items():
        table.add_row(f":{lbl}", desc)
    console.print(table)

    rel_table = Table(title="Relationship Signatures", border_style="green")
    rel_table.add_column("Relationship", style="bold green")
    rel_table.add_column("Cypher Pattern", style="white")

    for rel, pat in schema.get("edge_signatures", {}).items():
        rel_table.add_row(rel, pat)
    console.print(rel_table)


def cmd_query(query_text: str, explain: bool = True, user_id: str = "demo_engineer", session_id: str = "cli_session"):
    """Runs a single query with path explanation."""
    print_banner()
    g = get_graph()
    if hasattr(g, "nodes") and len(g.nodes) == 0:
        seed_company_graph(g)
    console.print(f"\n[bold yellow]User Query:[/bold yellow] [white]{query_text}[/white]\n")

    res = orchestrator.process_request(query_text, user_id=user_id, session_id=session_id)
    
    # Render answer
    console.print(Panel(Markdown(res["answer"]), title="[bold green]NEXUS Response[/bold green]", border_style="green"))

    if explain:
        # Show graph path behind answer
        path_panel = (
            f"[bold cyan]Executed Cypher Query:[/bold cyan]\n[dim]{res['cypher_query']}[/dim]\n\n"
            f"[bold magenta]Graph Traversal Path:[/bold magenta]\n[bold white]{res['reasoning_path']}[/bold white]"
        )
        console.print(Panel(path_panel, title="[bold magenta]🔍 Explainable Graph Trace (Track 01 & 03)[/bold magenta]", border_style="magenta"))


def cmd_demo():
    """Runs the judge-ready automated 3-track showcase."""
    print_banner()
    console.print("[bold magenta]🚀 Starting 3-Track Automated Walkthrough...[/bold magenta]\n")

    # Step 1: Ensure seeded
    g = get_graph()
    seed_company_graph(g)

    # Track 01 & 03 Showcase
    console.print(Panel("[bold cyan]TRACK 01 & 03: Multi-Hop Reasoning & Company Brain[/bold cyan]\n"
                        "Question: [italic]'Why did we choose Kafka over RabbitMQ, and who worked on it?'[/italic]", border_style="cyan"))
    
    res1 = orchestrator.process_request(
        "Why did we choose Kafka over RabbitMQ, and who worked on it?",
        user_id="judges_panel",
        session_id="session_day1"
    )
    console.print(Markdown(res1["answer"]))
    console.print(f"[bold magenta]Graph Path Explaining Answer:[/bold magenta] {res1['reasoning_path']}")
    console.print(f"[bold dim]Cypher:[/bold dim] {res1['cypher_query']}\n")

    # Track 02 Showcase: Persistent Cross-Session Memory
    console.print(Panel("[bold green]TRACK 02: Agent Memory Across Sessions & Multi-Agent Shared State[/bold green]\n"
                        "Same user returns in a NEW session: [italic]'Who else is connected to Alice or streaming?'[/italic]", border_style="green"))

    res2 = orchestrator.process_request(
        "Who else worked with Alice on Kafka or streaming?",
        user_id="judges_panel",
        session_id="session_day2"
    )
    console.print(Markdown(res2["answer"]))
    console.print(f"[bold magenta]Graph Path:[/bold magenta] {res2['reasoning_path']}\n")

    # Track 03: Document Ingestion into Graph
    console.print(Panel("[bold yellow]TRACK 03: Dynamic Knowledge Ingestion into Graph[/bold yellow]\n"
                        "Ingesting new Slack postmortem & decision...", border_style="yellow"))

    res3 = orchestrator.process_request(
        "Ingest RFC: Decision: Adopt gRPC for internal service-to-service communication to reduce serialization overhead.",
        user_id="judges_panel",
        session_id="session_day2"
    )
    console.print(Markdown(res3["answer"]))

    # Track 01 Showcase: Graph Algorithm (Blast Radius)
    console.print(Panel("[bold red]TRACK 01: Graph Algorithm Tool (Blast Radius & Outage Impact Analysis)[/bold red]\n"
                        "Running BFS impact calculation: [italic]'What is the blast radius if Kafka fails?'[/italic]", border_style="red"))
    res4 = orchestrator.process_request(
        "What is the blast radius if Kafka fails?",
        user_id="judges_panel",
        session_id="session_day2"
    )
    console.print(Markdown(res4["answer"]))

    # Track 01 & 02 Showcase: Autonomous Graph Actions & Multi-Agent Handoffs
    console.print(Panel("[bold green]TRACK 01 & 02: Autonomous Graph Action & Agent Handoffs[/bold green]\n"
                        "Scanning graph for conflicts and triggering automatic handoff...", border_style="green"))
    res5 = orchestrator.process_request(
        "Audit graph conflicts and trigger autonomous remediation handoff",
        user_id="judges_panel",
        session_id="session_day2"
    )
    console.print(Markdown(res5["answer"]))
    console.print("\n[bold green]✔ Full 5-Step Hackathon Walkthrough Completed Successfully![/bold green]")


def cmd_chat():
    """Starts interactive terminal chat with NEXUS."""
    print_banner()
    g = get_graph()
    seed_company_graph(g)
    
    console.print("[bold green]NEXUS Chat is ready! Type 'exit' or 'quit' to end session.[/bold green]\n")
    user_id = "cli_user"
    session_id = "session_live"

    while True:
        try:
            prompt = console.input("[bold cyan]You > [/bold cyan]").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit"]:
                console.print("[bold yellow]Goodbye![/bold yellow]")
                break
            if prompt.lower() == "schema":
                cmd_schema()
                continue
            
            res = orchestrator.process_request(prompt, user_id=user_id, session_id=session_id)
            console.print(Panel(Markdown(res["answer"]), title="[bold green]NEXUS[/bold green]", border_style="green"))
            console.print(f"[bold magenta]Path:[/bold magenta] [white]{res['reasoning_path']}[/white]\n")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Session ended.[/bold yellow]")
            break


def main():
    parser = argparse.ArgumentParser(description="NEXUS - FalkorDB-Powered Company Brain CLI")
    subparsers = parser.add_subparsers(dest="command")

    # seed
    subparsers.add_parser("seed", help="Seed knowledge graph")

    # schema
    subparsers.add_parser("schema", help="Show graph schema")

    # demo
    subparsers.add_parser("demo", help="Run automated 3-track showcase")

    # chat
    subparsers.add_parser("chat", help="Start interactive chat")

    # ui / serve
    ui_parser = subparsers.add_parser("ui", help="Launch interactive Web Dashboard & Graph UI")
    ui_parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    serve_parser = subparsers.add_parser("serve", help="Launch API & Web Dashboard")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on")

    # query
    query_parser = subparsers.add_parser("query", help="Query the graph")
    query_parser.add_argument("text", help="Query string")
    query_parser.add_argument("--user", default="demo_user", help="User ID")
    query_parser.add_argument("--explain", action="store_true", default=True, help="Show path explanation")

    args = parser.parse_args()

    if args.command == "seed":
        cmd_seed()
    elif args.command == "schema":
        cmd_schema()
    elif args.command == "demo":
        cmd_demo()
    elif args.command == "chat":
        cmd_chat()
    elif args.command in ("ui", "serve"):
        import uvicorn
        port = getattr(args, "port", 8000)
        console.print(f"[bold cyan]🚀 Starting NEXUS Interactive Web Dashboard at [bold underline green]http://localhost:{port}[/bold underline green][/bold cyan]")
        console.print("[dim]Opening interactive graph visualization, chat studio, and ingestion console...[/dim]")
        uvicorn.run("nexus.api.main:app", host="0.0.0.0", port=port, log_level="info")
    elif args.command == "query":
        cmd_query(args.text, explain=args.explain, user_id=args.user)
    else:
        cmd_demo()


if __name__ == "__main__":
    main()
