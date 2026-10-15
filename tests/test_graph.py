"""Unit tests for graph client and queries."""

import pytest
from nexus.graph.client import get_graph
from nexus.graph.seed import seed_company_graph
from nexus.graph.schema import inspect_live_schema


@pytest.fixture(scope="module")
def seeded_graph():
    g = get_graph("test_graph")
    seed_company_graph(g)
    return g


def test_schema_labels(seeded_graph):
    schema = inspect_live_schema(seeded_graph)
    assert "Person" in schema["labels"]
    assert "Decision" in schema["labels"]
    assert "Project" in schema["labels"]


def test_single_hop_query(seeded_graph):
    res = seeded_graph.query("MATCH (p:Person)-[:MADE]->(d:Decision) RETURN p.name, d.title")
    assert len(res) >= 5
    titles = [row[1] for row in res]
    assert any("Kafka" in str(t) for t in titles)


def test_multi_hop_query(seeded_graph):
    res = seeded_graph.query(
        "MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document) "
        "RETURN p.name, d.title, doc.title, path"
    )
    assert len(res) >= 2
    # Verify path was generated
    first_path = res[0][3]
    assert "-[:MADE]->" in first_path
    assert "-[:REFERENCES]->" in first_path


def test_supersedes_relationship(seeded_graph):
    res = seeded_graph.query("MATCH (d1:Decision)-[:SUPERSEDES]->(d2:Decision) RETURN d1.title, d2.title")
    assert len(res) >= 1
    assert "FalkorDB" in res[0][0]
    assert "Pinecone" in res[0][1]


def test_blast_radius(seeded_graph):
    res = seeded_graph.blast_radius("Kafka")
    assert res["found"] is True
    assert "Project Apollo" in res["impacted_projects"]
    assert any("Alice" in str(o) for o in res["key_owners_to_notify"])
    assert res["severity"] in ("CRITICAL", "HIGH")


def test_key_influencers(seeded_graph):
    influencers = seeded_graph.key_influencers(top_k=3)
    assert len(influencers) >= 1
    assert "betweenness_centrality" in influencers[0]


def test_audit_conflicts(seeded_graph):
    conflicts = seeded_graph.audit_conflicts()
    assert len(conflicts) >= 1
    assert any("FalkorDB" in c["new_decision"] for c in conflicts)
