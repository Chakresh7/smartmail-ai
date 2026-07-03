from typing import Dict, Any, List


def build_flow_data(state: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """Generate a simple nodes/edges representation from orchestrator state.

    Returns a dict with `nodes` and `edges`, where nodes have `id` and `label`.
    """
    steps = [
        ("classify", "Classification"),
        ("contexts", "RAG Contexts"),
        ("summary", "Summary"),
        ("reply", "Reply Draft"),
        ("events", "Calendar Events"),
        ("review", "Human Review"),
    ]

    nodes = []
    edges = []

    prev = None
    for key, label in steps:
        nid = key
        present = key in state and state.get(key) is not None
        nodes.append({"id": nid, "label": f"{label}{' ✓' if present else ''}"})
        if prev:
            edges.append({"from": prev, "to": nid})
        prev = nid

    return {"nodes": nodes, "edges": edges}


def build_flow_dot(state: Dict[str, Any]) -> str:
    data = build_flow_data(state)
    lines = ["digraph G {", "rankdir=LR;", "node [shape=box];"]
    for n in data["nodes"]:
        label = n["label"].replace('"', '\\"')
        lines.append(f'"{n["id"]}" [label="{label}"];')
    for e in data["edges"]:
        lines.append(f'"{e["from"]}" -> "{e["to"]}";')
    lines.append("}")
    return "\n".join(lines)
