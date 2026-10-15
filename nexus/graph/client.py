"""FalkorDB Graph Client with live connection and embedded fallback support."""

import re
import json
import socket
import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import networkx as nx

from nexus.config import settings

logger = logging.getLogger("nexus.graph")


class GraphNode:
    """Represents a graph node matching FalkorDB Node interface."""

    def __init__(self, node_id: int, labels: List[str] | str, properties: Dict[str, Any]):
        self.id = node_id
        if isinstance(labels, str):
            self.labels = [labels]
        else:
            self.labels = list(labels)
        self.properties = dict(properties)

    @property
    def label(self) -> str:
        return self.labels[0] if self.labels else ""

    def __getitem__(self, item: str) -> Any:
        return self.properties.get(item)

    def get(self, item: str, default: Any = None) -> Any:
        return self.properties.get(item, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
        }

    def __repr__(self) -> str:
        name = self.properties.get("name") or self.properties.get("title") or self.properties.get("id") or str(self.id)
        return f"(:{self.label} '{name}')"


class GraphEdge:
    """Represents a directed graph edge matching FalkorDB Edge interface."""

    def __init__(self, src_id: int, relation: str, dest_id: int, properties: Optional[Dict[str, Any]] = None):
        self.src_node = src_id
        self.relation = relation
        self.dest_node = dest_id
        self.properties = properties or {}

    def __getitem__(self, item: str) -> Any:
        return self.properties.get(item)

    def get(self, item: str, default: Any = None) -> Any:
        return self.properties.get(item, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src_node,
            "relation": self.relation,
            "dest": self.dest_node,
            "properties": self.properties,
        }

    def __repr__(self) -> str:
        return f"-[:{self.relation}]->"


class QueryResult:
    """QueryResult wrapper matching FalkorDB QueryResult."""

    def __init__(self, result_set: List[List[Any]], header: Optional[List[str]] = None, stats: Optional[Dict[str, Any]] = None):
        self.result_set = result_set
        self.header = header or []
        self.stats = stats or {}

    def __iter__(self):
        return iter(self.result_set)

    def __len__(self):
        return len(self.result_set)

    def __getitem__(self, index):
        return self.result_set[index]


class EmbeddedGraph:
    """Embedded high-performance graph database executing Cypher queries."""

    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[int, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._next_id = 1
        self._nx = nx.MultiDiGraph()
        self._label_index = defaultdict(set)
        self._prop_index = defaultdict(lambda: defaultdict(set))

    def _add_node(self, labels: List[str] | str, properties: Dict[str, Any]) -> GraphNode:
        node_id = self._next_id
        self._next_id += 1
        node = GraphNode(node_id, labels, properties)
        self.nodes[node_id] = node
        for lbl in node.labels:
            self._label_index[lbl].add(node_id)
        for k, v in properties.items():
            self._prop_index[k][str(v)].add(node_id)
        self._nx.add_node(node_id, labels=node.labels, **properties)
        return node

    def _add_edge(self, src_id: int, relation: str, dest_id: int, properties: Optional[Dict[str, Any]] = None) -> GraphEdge:
        edge = GraphEdge(src_id, relation, dest_id, properties or {})
        self.edges.append(edge)
        self._nx.add_edge(src_id, dest_id, key=relation, relation=relation, **(properties or {}))
        return edge

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Executes a Cypher query on the graph."""
        clean_cypher = cypher.strip().rstrip(";")
        logger.debug(f"Executing Cypher: {clean_cypher}")

        # Check for MATCH ... CREATE ... statements
        if clean_cypher.upper().startswith("MATCH") and " CREATE " in clean_cypher.upper():
            return self._execute_match_create(clean_cypher, params)

        # Check for CREATE statements
        if clean_cypher.upper().startswith("CREATE"):
            return self._execute_create(clean_cypher, params)

        # Check for MERGE statements
        if clean_cypher.upper().startswith("MERGE"):
            return self._execute_merge(clean_cypher, params)

        # Check for MATCH ... SET statements
        if clean_cypher.upper().startswith("MATCH") and " SET " in clean_cypher.upper():
            return self._execute_set(clean_cypher, params)

        # Check for MATCH statements
        if clean_cypher.upper().startswith("MATCH"):
            return self._execute_match(clean_cypher, params)

        # Schema introspection queries
        if "CALL db.labels" in clean_cypher or "CALL db.relationshipTypes" in clean_cypher:
            return self._execute_call(clean_cypher)

        return QueryResult([], header=[])

    def _parse_props_literal(self, props_str: str) -> Dict[str, Any]:
        """Parses a Cypher properties map literal like {id: 'u1', name: 'Alice'}."""
        props_str = props_str.strip()
        if not props_str or props_str == "{}":
            return {}
        if props_str.startswith("{") and props_str.endswith("}"):
            props_str = props_str[1:-1]
        
        result = {}
        parts = []
        current = []
        in_str = False
        quote_char = ""
        in_arr = False
        
        for ch in props_str:
            if ch in ("'", '"') and not in_str:
                in_str = True
                quote_char = ch
                current.append(ch)
            elif ch == quote_char and in_str:
                in_str = False
                current.append(ch)
            elif ch == "[" and not in_str:
                in_arr = True
                current.append(ch)
            elif ch == "]" and not in_str:
                in_arr = False
                current.append(ch)
            elif ch == "," and not in_str and not in_arr:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current).strip())

        for part in parts:
            if ":" not in part:
                continue
            k, v = part.split(":", 1)
            k = k.strip()
            v = v.strip()
            if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                result[k] = v[1:-1]
            elif v.lower() == "true":
                result[k] = True
            elif v.lower() == "false":
                result[k] = False
            elif v.startswith("[") and v.endswith("]"):
                items = [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip()]
                result[k] = items
            else:
                try:
                    if "." in v:
                        result[k] = float(v)
                    else:
                        result[k] = int(v)
                except ValueError:
                    result[k] = v
        return result

    def _extract_node_patterns(self, text: str) -> List[Tuple[str, str, str]]:
        """Extracts (var:Label {props}) handling nested braces and strings."""
        results = []
        i = 0
        n = len(text)
        while i < n:
            if text[i] == "(":
                i += 1
                var_start = i
                while i < n and text[i] not in (":", "{", ")", " ", "\t", "\n"):
                    i += 1
                var_name = text[var_start:i].strip()
                label = ""
                if i < n and text[i] == ":":
                    i += 1
                    lbl_start = i
                    while i < n and text[i] not in ("{", ")", " ", "\t", "\n"):
                        i += 1
                    label = text[lbl_start:i].strip()
                while i < n and text[i] in (" ", "\t", "\n"):
                    i += 1
                props_str = ""
                if i < n and text[i] == "{":
                    brace_start = i
                    brace_count = 0
                    in_quote = False
                    q_char = ""
                    while i < n:
                        ch = text[i]
                        if ch in ("'", '"') and not in_quote:
                            in_quote = True
                            q_char = ch
                        elif ch == q_char and in_quote:
                            in_quote = False
                        elif not in_quote:
                            if ch == "{":
                                brace_count += 1
                            elif ch == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    i += 1
                                    props_str = text[brace_start:i]
                                    break
                        i += 1
                while i < n and text[i] != ")":
                    i += 1
                if i < n and text[i] == ")":
                    i += 1
                if label or var_name:
                    results.append((var_name, label, props_str))
            else:
                i += 1
        return results

    def _execute_create(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        node_matches = self._extract_node_patterns(cypher)
        created_nodes = {}
        for var, label, props_str in node_matches:
            if not label:
                continue
            props = self._parse_props_literal(props_str) if props_str else {}
            node = self._add_node(label, props)
            if var:
                created_nodes[var] = node

        edge_matches = re.findall(r"\(([a-zA-Z0-9_]+)\)-\[:([a-zA-Z0-9_]+)\s*(\{[^}]*\})?\]->\(([a-zA-Z0-9_]+)\)", cypher)
        created_edges = []
        for src_var, rel, props_str, dest_var in edge_matches:
            src_node = created_nodes.get(src_var)
            dest_node = created_nodes.get(dest_var)
            if src_node and dest_node:
                edge_props = self._parse_props_literal(props_str) if props_str else {}
                edge = self._add_edge(src_node.id, rel, dest_node.id, edge_props)
                created_edges.append(edge)

        return QueryResult([[len(created_nodes), len(created_edges)]], header=["nodes_created", "edges_created"])

    def _execute_match_create(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Handles MATCH (a:L1 {p1}), (b:L2 {p2}) CREATE (a)-[:REL]->(b)"""
        match_part, create_part = re.split(r"\s+CREATE\s+", cypher, maxsplit=1, flags=re.IGNORECASE)
        
        # Match variables and target nodes
        bound_vars: Dict[str, GraphNode] = {}
        match_clauses = self._extract_node_patterns(match_part)
        for var, label, props_str in match_clauses:
            props = self._parse_props_literal(props_str) if props_str else {}
            candidates = list(self.nodes.values())
            if label:
                candidates = [self.nodes[nid] for nid in self._label_index.get(label, set())]
            
            for node in candidates:
                match = True
                for pk, pv in props.items():
                    if str(node.get(pk)) != str(pv):
                        match = False
                        break
                if match:
                    bound_vars[var] = node
                    break

        # Now create edges
        edge_matches = re.findall(r"\(([a-zA-Z0-9_]+)\)-\[:([a-zA-Z0-9_]+)\s*(\{[^}]*\})?\]->\(([a-zA-Z0-9_]+)\)", create_part)
        created = 0
        for src_var, rel, props_str, dest_var in edge_matches:
            src_node = bound_vars.get(src_var)
            dest_node = bound_vars.get(dest_var)
            if src_node and dest_node:
                props = self._parse_props_literal(props_str) if props_str else {}
                self._add_edge(src_node.id, rel, dest_node.id, props)
                created += 1

        return QueryResult([[created]], header=["edges_created"])

    def _execute_merge(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        node_match = re.search(r"MERGE\s*\(([a-zA-Z0-9_]*):([a-zA-Z0-9_]+)\s*(\{[^}]*\})?\)", cypher, re.IGNORECASE)
        if node_match:
            var, label, props_str = node_match.groups()
            props = self._parse_props_literal(props_str) if props_str else {}
            existing = None
            if "id" in props:
                for nid in self._label_index[label]:
                    if str(self.nodes[nid].get("id")) == str(props["id"]):
                        existing = self.nodes[nid]
                        break
            if not existing:
                existing = self._add_node(label, props)
            return QueryResult([[existing]], header=[var or "n"])

        return QueryResult([], header=[])

    def _execute_set(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Executes MATCH ... WHERE ... SET var.prop = val"""
        match_part, set_part = re.split(r"\s+SET\s+", cypher, maxsplit=1, flags=re.IGNORECASE)
        
        # Extract node pattern
        node_matches = self._extract_node_patterns(match_part)
        if not node_matches:
            return QueryResult([], header=["properties_set"])
        var_name, label, _ = node_matches[0]
        
        where_match = re.search(r"WHERE\s+(.*)$", match_part, re.IGNORECASE)
        where_str = where_match.group(1).strip() if where_match else None
        
        # Candidates
        candidates = list(self.nodes.values())
        if label:
            candidates = [self.nodes[nid] for nid in self._label_index.get(label, set())]
            
        matched_nodes = []
        for node in candidates:
            if self._eval_where(where_str, {var_name: node}):
                matched_nodes.append(node)
                
        # Parse assignments
        assignments = [a.strip() for a in set_part.split(",") if a.strip()]
        updated_count = 0
        for node in matched_nodes:
            for assignment in assignments:
                if "=" not in assignment:
                    continue
                left, right = assignment.split("=", 1)
                prop = left.split(".", 1)[-1].strip()
                val = right.strip().strip("'\"")
                node.properties[prop] = val
                self._prop_index[prop][str(val)].add(node.id)
                updated_count += 1
                
        return QueryResult([[updated_count]], header=["properties_set"])

    def _execute_call(self, cypher: str) -> QueryResult:
        if "db.labels" in cypher:
            labels = list(self._label_index.keys())
            return QueryResult([[lbl] for lbl in labels], header=["label"])
        if "db.relationshipTypes" in cypher:
            rels = list({e.relation for e in self.edges})
            return QueryResult([[r] for r in rels], header=["relationshipType"])
        return QueryResult([], header=[])

    def _execute_match(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Executes MATCH graph traversals."""
        return_match = re.search(r"RETURN\s+(.*)$", cypher, re.IGNORECASE)
        return_items = []
        if return_match:
            return_str = return_match.group(1).strip()
            return_str = re.split(r"\s+(?:ORDER\s+BY|LIMIT|SKIP)\s+", return_str, flags=re.IGNORECASE)[0]
            return_items = [x.strip() for x in return_str.split(",")]

        # Correct regex to capture everything between MATCH and WHERE / RETURN
        pattern_match = re.search(r"MATCH\s+(?:p\s*=\s*)?(.*?)(?:\s+WHERE|\s+RETURN|\s+ORDER|\s+LIMIT|$)", cypher, re.IGNORECASE)
        pattern_str = pattern_match.group(1).strip() if pattern_match else ""

        where_match = re.search(r"WHERE\s+(.*?)(?=\s+RETURN|\s+WITH|\s+ORDER|\s+LIMIT|$)", cypher, re.IGNORECASE)
        where_str = where_match.group(1).strip() if where_match else None

        results = []
        
        # Match chain nodes and edges
        chain_nodes = re.findall(r"\(([a-zA-Z0-9_]*)(?::([a-zA-Z0-9_]+))?\s*(\{[^}]*\})?\)", pattern_str)
        chain_edges = re.findall(r"-\[([a-zA-Z0-9_]*)(?::([a-zA-Z0-9_]+))?(\*[\d\.]*)?\s*(\{[^}]*\})?\]->", pattern_str)

        # Case 1: 1 node (e.g. MATCH (p:Person))
        if len(chain_nodes) == 1:
            var_name, label, props_str = chain_nodes[0]
            cand_nodes = list(self.nodes.values())
            if label:
                cand_nodes = [self.nodes[nid] for nid in self._label_index.get(label, set())]
            
            for node in cand_nodes:
                ctx = {var_name or "n": node}
                if self._eval_where(where_str, ctx):
                    row = self._format_return_row(return_items, ctx)
                    results.append(row)

        # Case 2: 1 hop (e.g. MATCH (a:Person)-[:MADE]->(d:Decision))
        elif len(chain_nodes) == 2 and len(chain_edges) == 1:
            src_var, src_lbl, _ = chain_nodes[0]
            edge_var, edge_rel, _, _ = chain_edges[0]
            dest_var, dest_lbl, _ = chain_nodes[1]

            for edge in self.edges:
                src_node = self.nodes.get(edge.src_node)
                dest_node = self.nodes.get(edge.dest_node)
                if not src_node or not dest_node:
                    continue
                if src_lbl and src_lbl not in src_node.labels:
                    continue
                if dest_lbl and dest_lbl not in dest_node.labels:
                    continue
                if edge_rel and edge.relation != edge_rel:
                    continue

                path_str = f"({src_node.label}: {src_node.get('name') or src_node.get('title')})-[:{edge.relation}]->({dest_node.label}: {dest_node.get('name') or dest_node.get('title')})"
                ctx = {
                    src_var or "a": src_node,
                    edge_var or "r": edge,
                    dest_var or "b": dest_node,
                    "_path": path_str,
                    "path": path_str
                }
                if (src_var or "a") != "p" and (dest_var or "b") != "p":
                    ctx["p"] = path_str
                if self._eval_where(where_str, ctx):
                    row = self._format_return_row(return_items, ctx)
                    results.append(row)

        # Case 3: 2 hops (e.g. MATCH (p:Person)-[:MADE]->(d:Decision)-[:REFERENCES]->(doc:Document))
        elif len(chain_nodes) == 3 and len(chain_edges) == 2:
            src_var, src_lbl, _ = chain_nodes[0]
            mid_var, mid_lbl, _ = chain_nodes[1]
            dest_var, dest_lbl, _ = chain_nodes[2]
            rel1 = chain_edges[0][1]
            rel2 = chain_edges[1][1]

            for edge1 in self.edges:
                if rel1 and edge1.relation != rel1:
                    continue
                n1 = self.nodes.get(edge1.src_node)
                n2 = self.nodes.get(edge1.dest_node)
                if not n1 or not n2:
                    continue
                if src_lbl and src_lbl not in n1.labels:
                    continue
                if mid_lbl and mid_lbl not in n2.labels:
                    continue

                for edge2 in self.edges:
                    if edge2.src_node != n2.id:
                        continue
                    if rel2 and edge2.relation != rel2:
                        continue
                    n3 = self.nodes.get(edge2.dest_node)
                    if not n3:
                        continue
                    if dest_lbl and dest_lbl not in n3.labels:
                        continue

                    path_str = (
                        f"({n1.label}: {n1.get('name') or n1.get('title')})"
                        f"-[:{edge1.relation}]->({n2.label}: {n2.get('name') or n2.get('title')})"
                        f"-[:{edge2.relation}]->({n3.label}: {n3.get('name') or n3.get('title')})"
                    )
                    ctx = {
                        src_var or "a": n1,
                        mid_var or "b": n2,
                        dest_var or "c": n3,
                        "_path": path_str,
                        "path": path_str
                    }
                    if "p" not in (src_var, mid_var, dest_var):
                        ctx["p"] = path_str
                    if self._eval_where(where_str, ctx):
                        row = self._format_return_row(return_items, ctx)
                        results.append(row)

        # Case 4: 3 hops (e.g. (p)-[:WORKS_ON]->(proj)-[:HAS_DECISION]->(d)-[:USES]->(tech))
        elif len(chain_nodes) == 4 and len(chain_edges) == 3:
            v1, l1, _ = chain_nodes[0]
            v2, l2, _ = chain_nodes[1]
            v3, l3, _ = chain_nodes[2]
            v4, l4, _ = chain_nodes[3]
            r1, r2, r3 = chain_edges[0][1], chain_edges[1][1], chain_edges[2][1]

            for e1 in self.edges:
                if r1 and e1.relation != r1:
                    continue
                n1 = self.nodes.get(e1.src_node)
                n2 = self.nodes.get(e1.dest_node)
                if not n1 or not n2 or (l1 and l1 not in n1.labels) or (l2 and l2 not in n2.labels):
                    continue
                for e2 in self.edges:
                    if e2.src_node != n2.id or (r2 and e2.relation != r2):
                        continue
                    n3 = self.nodes.get(e2.dest_node)
                    if not n3 or (l3 and l3 not in n3.labels):
                        continue
                    for e3 in self.edges:
                        if e3.src_node != n3.id or (r3 and e3.relation != r3):
                            continue
                        n4 = self.nodes.get(e3.dest_node)
                        if not n4 or (l4 and l4 not in n4.labels):
                            continue
                        path_str = f"({n1.get('name')})-[:{e1.relation}]->({n2.get('name')})-[:{e2.relation}]->({n3.get('title') or n3.get('name')})-[:{e3.relation}]->({n4.get('name')})"
                        ctx = {v1: n1, v2: n2, v3: n3, v4: n4, "_path": path_str, "path": path_str}
                        if "p" not in (v1, v2, v3, v4):
                            ctx["p"] = path_str
                        if self._eval_where(where_str, ctx):
                            results.append(self._format_return_row(return_items, ctx))
        else:
            # Generic fallback
            for nid, node in self.nodes.items():
                row = self._format_return_row(return_items, {"n": node})
                results.append(row)

        return QueryResult(results, header=return_items)

    def _eval_where(self, where_str: Optional[str], context: Dict[str, Any]) -> bool:
        """Evaluates a WHERE condition against the matched context."""
        if not where_str:
            return True
        try:
            expr = where_str
            for var_name, entity in context.items():
                if isinstance(entity, GraphNode):
                    for prop_k, prop_v in entity.properties.items():
                        placeholder = f"__VAL_{var_name}_{prop_k}__"
                        val_str = f"'{prop_v}'" if isinstance(prop_v, str) else str(prop_v)
                        expr = re.sub(rf"\b{var_name}\.{prop_k}\b", val_str, expr)
            
            # Split by AND
            sub_clauses = re.split(r"\s+AND\s+", expr, flags=re.IGNORECASE)
            for sub in sub_clauses:
                sub = sub.strip()
                if not sub:
                    continue
                if "CONTAINS" in sub:
                    left, right = sub.split("CONTAINS", 1)
                    if right.strip().strip("'\"").lower() not in left.strip().strip("'\"").lower():
                        return False
                elif "=" in sub:
                    left, right = [x.strip().strip("'\"") for x in sub.split("=", 1)]
                    if left.lower() != right.lower():
                        return False
            return True
        except Exception as e:
            logger.debug(f"WHERE eval exception: {e}")
            return True
        return True

    def _format_return_row(self, return_items: List[str], ctx: Dict[str, Any]) -> List[Any]:
        row = []
        for item in return_items:
            item = item.strip()
            if "." in item:
                var, prop = item.split(".", 1)
                entity = ctx.get(var)
                if isinstance(entity, GraphNode):
                    row.append(entity.get(prop))
                elif isinstance(entity, GraphEdge):
                    row.append(entity.get(prop))
                else:
                    row.append(None)
            elif item in ctx:
                row.append(ctx[item])
            else:
                row.append(None)
        return row

    def find_path(self, start_id: int, target_id: int, max_depth: int = 4) -> Optional[List[Dict[str, Any]]]:
        """Finds shortest path between two nodes in the graph."""
        try:
            path_ids = nx.shortest_path(self._nx.to_undirected(), source=start_id, target=target_id)
            path_steps = []
            for i in range(len(path_ids) - 1):
                u = path_ids[i]
                v = path_ids[i + 1]
                edge_data = self._nx.get_edge_data(u, v) or self._nx.get_edge_data(v, u)
                rel = "CONNECTED_TO"
                if edge_data:
                    first_edge = list(edge_data.values())[0]
                    rel = first_edge.get("relation", "CONNECTED_TO")
                path_steps.append({
                    "from": self.nodes[u].to_dict(),
                    "relation": rel,
                    "to": self.nodes[v].to_dict()
                })
            return path_steps
        except Exception:
            return None

    def blast_radius(self, target_name: str) -> Dict[str, Any]:
        """Calculates blast radius (impact analysis) if a technology or project fails or is modified."""
        target_node = None
        for n in self.nodes.values():
            name = str(n.get("name") or n.get("title") or n.get("id") or "").lower()
            if target_name.lower() in name or name in target_name.lower():
                target_node = n
                break
        if not target_node:
            return {"target": target_name, "found": False, "impacted_projects": [], "impacted_teams": [], "key_owners_to_notify": []}

        impacted_nodes = set()
        paths = []
        for edge in self.edges:
            if edge.dest_node == target_node.id:
                src = self.nodes.get(edge.src_node)
                if src:
                    impacted_nodes.add(src.id)
                    paths.append(f"({src.label}: {src.get('name') or src.get('title')})-[:{edge.relation}]->({target_node.label}: {target_node.get('name')})")
                    for e2 in self.edges:
                        if e2.dest_node == src.id and e2.relation in ("WORKS_ON", "MEMBER_OF", "MADE"):
                            person = self.nodes.get(e2.src_node)
                            if person:
                                impacted_nodes.add(person.id)
                                paths.append(f"({person.label}: {person.get('name')})-[:{e2.relation}]->({src.label}: {src.get('name')})")

        projects = [self.nodes[nid].get("name") for nid in impacted_nodes if "Project" in self.nodes[nid].labels]
        persons = [{"name": self.nodes[nid].get("name"), "email": self.nodes[nid].get("email")} for nid in impacted_nodes if "Person" in self.nodes[nid].labels]
        decisions = [self.nodes[nid].get("title") for nid in impacted_nodes if "Decision" in self.nodes[nid].labels]
        severity = "CRITICAL" if len(projects) > 1 else ("HIGH" if projects else "LOW")

        return {
            "target": target_node.get("name") or target_node.get("title") or target_node.id,
            "target_label": target_node.label,
            "found": True,
            "severity": severity,
            "impacted_projects": projects,
            "impacted_decisions": decisions,
            "key_owners_to_notify": persons,
            "traversal_paths": list(set(paths)),
            "total_impacted_entities": len(impacted_nodes)
        }

    def key_influencers(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Calculates graph centrality to identify key decision makers and critical dependencies."""
        if len(self.nodes) < 2:
            return []
        try:
            undir = self._nx.to_undirected()
            bet = nx.betweenness_centrality(undir)
            results = []
            for nid, score in sorted(bet.items(), key=lambda x: x[1], reverse=True)[:top_k]:
                node = self.nodes.get(nid)
                if node:
                    results.append({
                        "id": node.get("id") or str(nid),
                        "name": node.get("name") or node.get("title"),
                        "label": node.label,
                        "betweenness_centrality": round(score, 4),
                        "connections": len(list(undir.neighbors(nid)))
                    })
            return results
        except Exception as e:
            logger.error(f"Centrality calculation error: {e}")
            return []

    def audit_conflicts(self) -> List[Dict[str, Any]]:
        """Autonomously audits graph for superseded decisions still used in active projects or orphaned items."""
        conflicts = []
        superseded_ids = set()
        superseded_map = {}
        for edge in self.edges:
            if edge.relation == "SUPERSEDES":
                superseded_ids.add(edge.dest_node)
                superseded_map[edge.dest_node] = edge.src_node

        for sid in superseded_ids:
            old_dec = self.nodes.get(sid)
            new_dec = self.nodes.get(superseded_map[sid])
            if old_dec and new_dec:
                conflicts.append({
                    "type": "SUPERSEDED_DECISION_WARNING",
                    "severity": "MEDIUM",
                    "description": f"Active architectural pattern supersedes '{old_dec.get('title')}' with '{new_dec.get('title')}'. Verify all downstream deployments have completed migration.",
                    "old_decision": old_dec.get("title"),
                    "new_decision": new_dec.get("title"),
                    "action_required": f"Update project dependencies to use {new_dec.get('title')}"
                })
        return conflicts


class FalkorClientManager:
    """Manages connection to FalkorDB live instance or embedded fallback."""

    def __init__(self):
        self._live_client = None
        self._is_live = False
        self._embedded_graphs: Dict[str, EmbeddedGraph] = {}
        self._init_connection()

    def _init_connection(self):
        if settings.force_embedded:
            logger.info("FORCE_EMBEDDED enabled, using embedded graph engine.")
            self._is_live = False
            return

        try:
            with socket.create_connection((settings.falkordb_host, settings.falkordb_port), timeout=0.1):
                pass
        except Exception:
            self._is_live = False
            return

        try:
            from falkordb import FalkorDB
            client = FalkorDB(
                host=settings.falkordb_host,
                port=settings.falkordb_port,
                password=settings.falkordb_password,
            )
            client.connection.ping()
            self._live_client = client
            self._is_live = True
            logger.info(f"Connected to live FalkorDB instance at {settings.falkordb_host}:{settings.falkordb_port}")
        except Exception as e:
            logger.info(f"Live FalkorDB not reached ({e}). Using embedded high-performance graph engine.")
            self._is_live = False

    @property
    def is_live(self) -> bool:
        return self._is_live

    def select_graph(self, graph_name: Optional[str] = None):
        name = graph_name or settings.falkordb_graph_name
        if self._is_live and self._live_client:
            return self._live_client.select_graph(name)
        if name not in self._embedded_graphs:
            self._embedded_graphs[name] = EmbeddedGraph(name)
        return self._embedded_graphs[name]


# Global singleton instance
graph_manager = FalkorClientManager()


def get_graph(name: Optional[str] = None):
    return graph_manager.select_graph(name)
