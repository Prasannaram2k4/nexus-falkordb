"""Seed script to populate the Acme Corp Company Knowledge Graph in FalkorDB."""

import logging
from typing import Optional
from nexus.graph.client import get_graph

logger = logging.getLogger("nexus.seed")


def seed_company_graph(graph=None) -> int:
    """Populates the company knowledge graph with realistic connected data."""
    g = graph or get_graph()
    
    # 1. Clear existing seed data if needed or initialize
    logger.info("Seeding company knowledge graph...")

    cypher_statements = [
        # Teams
        "CREATE (t1:Team {id: 'team_data', name: 'Data Infra', lead: 'Alice Chen'})",
        "CREATE (t2:Team {id: 'team_platform', name: 'Core Platform', lead: 'Bob Miller'})",
        "CREATE (t3:Team {id: 'team_infra', name: 'DevOps & SRE', lead: 'Carol Danvers'})",
        "CREATE (t4:Team {id: 'team_security', name: 'Security Engineering', lead: 'Dave Vance'})",
        "CREATE (t5:Team {id: 'team_leadership', name: 'Engineering Leadership', lead: 'Elena Rostova'})",

        # People
        "CREATE (p1:Person {id: 'p_alice', name: 'Alice Chen', email: 'alice@acme.corp', role: 'Staff Data Engineer', expertise: ['Streaming', 'Kafka', 'Distributed Systems']})",
        "CREATE (p2:Person {id: 'p_bob', name: 'Bob Miller', email: 'bob@acme.corp', role: 'Principal Architect', expertise: ['Databases', 'Graph Systems', 'Agent Memory', 'FalkorDB']})",
        "CREATE (p3:Person {id: 'p_carol', name: 'Carol Danvers', email: 'carol@acme.corp', role: 'Staff DevOps Engineer', expertise: ['Kubernetes', 'Cloud', 'Terraform', 'Observability']})",
        "CREATE (p4:Person {id: 'p_dave', name: 'Dave Vance', email: 'dave@acme.corp', role: 'Principal Security Architect', expertise: ['Zero-Trust', 'IAM', 'mTLS', 'Compliance']})",
        "CREATE (p5:Person {id: 'p_elena', name: 'Elena Rostova', email: 'elena@acme.corp', role: 'VP of Engineering', expertise: ['Strategy', 'Org Design', 'Architecture']})",
        "CREATE (p6:Person {id: 'p_frank', name: 'Frank Wright', email: 'frank@acme.corp', role: 'Senior Frontend Lead', expertise: ['React', 'Next.js', 'UI Extensions']})",

        # Technologies
        "CREATE (tech_kafka:Technology {id: 'tech_kafka', name: 'Apache Kafka', category: 'Event Streaming', version: '3.6'})",
        "CREATE (tech_rabbit:Technology {id: 'tech_rabbit', name: 'RabbitMQ', category: 'Message Broker', version: '3.12'})",
        "CREATE (tech_falkor:Technology {id: 'tech_falkordb', name: 'FalkorDB', category: 'Graph Database & Vector Store', version: 'latest'})",
        "CREATE (tech_redis:Technology {id: 'tech_redis', name: 'Redis', category: 'Cache & Key-Value', version: '7.2'})",
        "CREATE (tech_pinecone:Technology {id: 'tech_pinecone', name: 'Pinecone', category: 'Managed Vector DB', version: 'v2'})",
        "CREATE (tech_k8s:Technology {id: 'tech_k8s', name: 'Kubernetes', category: 'Container Orchestration', version: '1.29'})",
        "CREATE (tech_pg:Technology {id: 'tech_postgres', name: 'PostgreSQL', category: 'Relational DB', version: '16'})",

        # Projects
        "CREATE (proj_apollo:Project {id: 'proj_apollo', name: 'Project Apollo', status: 'Active', description: 'Enterprise real-time event pipeline'})",
        "CREATE (proj_atlas:Project {id: 'proj_atlas', name: 'Project Atlas', status: 'Active', description: 'Agentic memory & company knowledge graph platform'})",
        "CREATE (proj_sentinel:Project {id: 'proj_sentinel', name: 'Project Sentinel', status: 'Active', description: 'Zero-trust security and identity hardening'})",
        "CREATE (proj_phoenix:Project {id: 'proj_phoenix', name: 'Project Phoenix', status: 'Completed', description: 'Cloud migration to automated Kubernetes clusters'})",

        # Documents
        "CREATE (doc_rfc101:Document {id: 'doc_rfc101', title: 'RFC-101: Kafka vs RabbitMQ Streaming Evaluation', url: 'https://wiki.acme.corp/rfc/101', type: 'RFC'})",
        "CREATE (doc_adr104:Document {id: 'doc_adr104', title: 'ADR-104: Standalone Vector Database Selection', url: 'https://wiki.acme.corp/adr/104', type: 'ADR'})",
        "CREATE (doc_adr110:Document {id: 'doc_adr110', title: 'ADR-110: FalkorDB for Unified Graph & Agent Context', url: 'https://wiki.acme.corp/adr/110', type: 'ADR'})",
        "CREATE (doc_rfc108:Document {id: 'doc_rfc108', title: 'RFC-108: GitOps Multi-Cluster Kubernetes Deployment', url: 'https://wiki.acme.corp/rfc/108', type: 'RFC'})",
        "CREATE (doc_slack:Document {id: 'doc_slack_stream', title: 'Slack Thread #streaming-debates: Message Drop Postmortem', url: 'slack://channel/C0123/p1681123456', type: 'Slack'})",

        # Decisions
        "CREATE (dec_kafka:Decision {id: 'dec_kafka', title: 'Choose Kafka over RabbitMQ for Event Streaming', date: '2023-04-10', rationale: 'Kafka provides durable partitioned logging and higher throughput under burst load, resolving RabbitMQ memory pressure issues seen during Black Friday.', outcome: 'Adopted'})",
        "CREATE (dec_pinecone:Decision {id: 'dec_pinecone', title: 'Initial Vector Search with Pinecone', date: '2023-01-15', rationale: 'Quick managed setup for initial POC before graph relationships were needed.', outcome: 'Superseded'})",
        "CREATE (dec_falkor:Decision {id: 'dec_falkor', title: 'Adopt FalkorDB as Unified Graph & Agent Memory Layer', date: '2024-03-20', rationale: 'FalkorDB combines ultra-fast Cypher graph traversals with vector search, enabling explainable multi-hop reasoning and persistent agent memory in one engine.', outcome: 'Active'})",
        "CREATE (dec_k8s:Decision {id: 'dec_k8s', title: 'Standardize on EKS with ArgoCD GitOps', date: '2023-08-01', rationale: 'Automate zero-downtime rollouts across multi-region infrastructure.', outcome: 'Active'})",
        "CREATE (dec_sec:Decision {id: 'dec_sec', title: 'Mandate mTLS and SPIFFE across all microservices', date: '2023-11-12', rationale: 'Eliminate perimeter-only security assumptions to achieve SOC2 and ISO27001 compliance.', outcome: 'Active'})",

        # Edges - Member of Team
        "MATCH (p:Person {id: 'p_alice'}), (t:Team {id: 'team_data'}) CREATE (p)-[:MEMBER_OF]->(t)",
        "MATCH (p:Person {id: 'p_bob'}), (t:Team {id: 'team_platform'}) CREATE (p)-[:MEMBER_OF]->(t)",
        "MATCH (p:Person {id: 'p_carol'}), (t:Team {id: 'team_infra'}) CREATE (p)-[:MEMBER_OF]->(t)",
        "MATCH (p:Person {id: 'p_dave'}), (t:Team {id: 'team_security'}) CREATE (p)-[:MEMBER_OF]->(t)",
        "MATCH (p:Person {id: 'p_elena'}), (t:Team {id: 'team_leadership'}) CREATE (p)-[:MEMBER_OF]->(t)",

        # Edges - Works on Project
        "MATCH (p:Person {id: 'p_alice'}), (proj:Project {id: 'proj_apollo'}) CREATE (p)-[:WORKS_ON {role: 'Lead Architect', since: '2023'}]->(proj)",
        "MATCH (p:Person {id: 'p_alice'}), (proj:Project {id: 'proj_atlas'}) CREATE (p)-[:WORKS_ON {role: 'Graph Streaming Contributor', since: '2024'}]->(proj)",
        "MATCH (p:Person {id: 'p_bob'}), (proj:Project {id: 'proj_atlas'}) CREATE (p)-[:WORKS_ON {role: 'Platform Architect', since: '2024'}]->(proj)",
        "MATCH (p:Person {id: 'p_carol'}), (proj:Project {id: 'proj_phoenix'}) CREATE (p)-[:WORKS_ON {role: 'DevOps Lead', since: '2023'}]->(proj)",
        "MATCH (p:Person {id: 'p_dave'}), (proj:Project {id: 'proj_sentinel'}) CREATE (p)-[:WORKS_ON {role: 'Security Lead', since: '2023'}]->(proj)",

        # Edges - Project uses Technology
        "MATCH (proj:Project {id: 'proj_apollo'}), (tech:Technology {id: 'tech_kafka'}) CREATE (proj)-[:USES {purpose: 'High-throughput stream broker'}]->(tech)",
        "MATCH (proj:Project {id: 'proj_atlas'}), (tech:Technology {id: 'tech_falkordb'}) CREATE (proj)-[:USES {purpose: 'Graph Context & Memory Engine'}]->(tech)",
        "MATCH (proj:Project {id: 'proj_phoenix'}), (tech:Technology {id: 'tech_k8s'}) CREATE (proj)-[:USES {purpose: 'Container Orchestration'}]->(tech)",

        # Edges - Decisions made by Persons
        "MATCH (p:Person {id: 'p_alice'}), (dec:Decision {id: 'dec_kafka'}) CREATE (p)-[:MADE {date: '2023-04-10'}]->(dec)",
        "MATCH (p:Person {id: 'p_bob'}), (dec:Decision {id: 'dec_pinecone'}) CREATE (p)-[:MADE {date: '2023-01-15'}]->(dec)",
        "MATCH (p:Person {id: 'p_bob'}), (dec:Decision {id: 'dec_falkor'}) CREATE (p)-[:MADE {date: '2024-03-20'}]->(dec)",
        "MATCH (p:Person {id: 'p_carol'}), (dec:Decision {id: 'dec_k8s'}) CREATE (p)-[:MADE {date: '2023-08-01'}]->(dec)",
        "MATCH (p:Person {id: 'p_dave'}), (dec:Decision {id: 'dec_sec'}) CREATE (p)-[:MADE {date: '2023-11-12'}]->(dec)",

        # Edges - Project has Decision
        "MATCH (proj:Project {id: 'proj_apollo'}), (dec:Decision {id: 'dec_kafka'}) CREATE (proj)-[:HAS_DECISION]->(dec)",
        "MATCH (proj:Project {id: 'proj_atlas'}), (dec:Decision {id: 'dec_falkor'}) CREATE (proj)-[:HAS_DECISION]->(dec)",

        # Edges - Decision Supersedes Decision
        "MATCH (d1:Decision {id: 'dec_falkor'}), (d2:Decision {id: 'dec_pinecone'}) CREATE (d1)-[:SUPERSEDES]->(d2)",

        # Edges - Decision references Document
        "MATCH (dec:Decision {id: 'dec_kafka'}), (doc:Document {id: 'doc_rfc101'}) CREATE (dec)-[:REFERENCES]->(doc)",
        "MATCH (dec:Decision {id: 'dec_kafka'}), (doc:Document {id: 'doc_slack_stream'}) CREATE (dec)-[:REFERENCES]->(doc)",
        "MATCH (dec:Decision {id: 'dec_falkor'}), (doc:Document {id: 'doc_adr110'}) CREATE (dec)-[:REFERENCES]->(doc)",

        # Edges - Document Authored By Person
        "MATCH (doc:Document {id: 'doc_rfc101'}), (p:Person {id: 'p_alice'}) CREATE (doc)-[:AUTHORED_BY]->(p)",
        "MATCH (doc:Document {id: 'doc_adr110'}), (p:Person {id: 'p_bob'}) CREATE (doc)-[:AUTHORED_BY]->(p)",

        # Edges - Person KNOWS Person (Social / Collaboration Graph)
        "MATCH (p1:Person {id: 'p_alice'}), (p2:Person {id: 'p_bob'}) CREATE (p1)-[:KNOWS {strength: 'high', context: 'Co-designing Project Atlas'}]->(p2)",
        "MATCH (p2:Person {id: 'p_bob'}), (p1:Person {id: 'p_alice'}) CREATE (p2)-[:KNOWS {strength: 'high', context: 'Co-designing Project Atlas'}]->(p1)",
        "MATCH (p1:Person {id: 'p_bob'}), (p2:Person {id: 'p_carol'}) CREATE (p1)-[:KNOWS {strength: 'medium', context: 'Infra cluster provisioning'}]->(p2)",
        "MATCH (p1:Person {id: 'p_carol'}), (p2:Person {id: 'p_dave'}) CREATE (p1)-[:KNOWS {strength: 'high', context: 'Security compliance for clusters'}]->(p2)",
    ]

    count = 0
    for stmt in cypher_statements:
        try:
            g.query(stmt)
            count += 1
        except Exception as e:
            logger.error(f"Error executing seed Cypher '{stmt[:40]}...': {e}")

    logger.info(f"Successfully seeded company graph with {count} graph statements.")
    return count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_company_graph()
