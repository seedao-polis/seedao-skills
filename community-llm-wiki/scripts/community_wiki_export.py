#!/usr/bin/env python3
"""
community_wiki_export.py — 导出社区数据为多种格式

支持格式：
  - gexf     : GEXF 图格式（Gephi 兼容）
  - cytoscape: Cytoscape.js JSON
  - markdown : Markdown 报告
  - csv      : 节点/边 CSV

Usage:
    python community_wiki_export.py --community ./my-community --format gexf --output graph.gexf
    python community_wiki_export.py --community ./my-community --format markdown --output report.md
"""
import argparse
import json
import os
from datetime import datetime, timezone


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def export_gexf(community_dir: str, output_path: str):
    """Export graph to GEXF format for Gephi."""
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))
    people_dir = os.path.join(community_dir, "people")
    if not graph:
        raise ValueError("Graph not computed yet")

    node_attrs = {}
    for n in graph["nodes"]:
        pid = n["id"]
        person = load_json(os.path.join(people_dir, f"{pid}.json"))
        if person:
            node_attrs[pid] = person.get("profile", {})

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gexf xmlns="http://www.gexf.net/1.3" version="1.3">',
        '  <graph mode="static" defaultedgetype="undirected">',
        '    <nodes>',
    ]
    for n in graph["nodes"]:
        pid = n["id"]
        attrs = node_attrs.get(pid, {})
        label = attrs.get("name", pid)
        lines.append(f'      <node id="{pid}" label="{label}" />')
    lines.append('    </nodes>')
    lines.append('    <edges>')
    for i, e in enumerate(graph["edges"]):
        lines.append(
            f'      <edge id="{i}" source="{e["source"]}" target="{e["target"]}" weight="{e["density"]}" />'
        )
    lines.append('    </edges>')
    lines.append('  </graph>')
    lines.append('</gexf>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"GEXF exported: {output_path}")


def export_cytoscape(community_dir: str, output_path: str):
    """Export to Cytoscape.js JSON format."""
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))
    if not graph:
        raise ValueError("Graph not computed yet")

    elements = []
    for n in graph["nodes"]:
        elements.append({
            "data": {"id": n["id"], "label": n["id"]}
        })
    for e in graph["edges"]:
        elements.append({
            "data": {
                "id": f"{e['source']}-{e['target']}",
                "source": e["source"],
                "target": e["target"],
                "weight": e["density"],
                "type": e["type"],
            }
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    print(f"Cytoscape JSON exported: {output_path}")


def export_markdown(community_dir: str, output_path: str):
    """Export a Markdown community report."""
    community = load_json(os.path.join(community_dir, "community.json"))
    state = load_json(os.path.join(community_dir, "state", "state.json"))
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))

    lines = []
    lines.append(f"# {community.get('name', 'Community')} Report")
    lines.append(f"\nGenerated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"\n## Values\n")
    for v in community.get("values", []):
        lines.append(f"- {v}")

    if state:
        lines.append(f"\n## Community State\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Co-presence | {state['co_presence']} |")
        lines.append(f"| Emergence | {state['emergence']} |")
        lines.append(f"| Xiaoyao | {state['xiaoyao']} |")
        lines.append(f"| People | {state['people_count']} |")
        lines.append(f"| Events | {state['event_count']} |")
        lines.append(f"| Edges | {state['edge_count']} |")

    if state and "individual_xiaoyao" in state:
        lines.append(f"\n## Individual Xiaoyao\n")
        lines.append(f"| Person | IR | RE | NR | Score |")
        lines.append(f"|--------|----|----|----|-------|")
        for pid, x in sorted(state["individual_xiaoyao"].items(), key=lambda kv: kv[1]["score"], reverse=True):
            lines.append(f"| {pid} | {x['ir']} | {x['re']} | {x['nr']} | {x['score']} |")

    if graph:
        lines.append(f"\n## Network Stats\n")
        lines.append(f"- Nodes: {graph['stats']['node_count']}")
        lines.append(f"- Edges: {graph['stats']['edge_count']}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Markdown report exported: {output_path}")


def export_csv(community_dir: str, output_dir: str):
    """Export nodes and edges as CSV."""
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))
    if not graph:
        raise ValueError("Graph not computed yet")

    os.makedirs(output_dir, exist_ok=True)

    nodes_path = os.path.join(output_dir, "nodes.csv")
    with open(nodes_path, "w", encoding="utf-8") as f:
        f.write("id\n")
        for n in graph["nodes"]:
            f.write(f"{n['id']}\n")

    edges_path = os.path.join(output_dir, "edges.csv")
    with open(edges_path, "w", encoding="utf-8") as f:
        f.write("source,target,density,type\n")
        for e in graph["edges"]:
            f.write(f"{e['source']},{e['target']},{e['density']},{e['type']}\n")

    print(f"CSV exported: {nodes_path}, {edges_path}")


def main():
    parser = argparse.ArgumentParser(description="Export Community Wiki data")
    parser.add_argument("--community", required=True, help="Community directory path")
    parser.add_argument("--format", required=True, choices=["gexf", "cytoscape", "markdown", "csv"], help="Export format")
    parser.add_argument("--output", required=True, help="Output file or directory")
    args = parser.parse_args()

    if args.format == "gexf":
        export_gexf(args.community, args.output)
    elif args.format == "cytoscape":
        export_cytoscape(args.community, args.output)
    elif args.format == "markdown":
        export_markdown(args.community, args.output)
    elif args.format == "csv":
        export_csv(args.community, args.output)


if __name__ == "__main__":
    main()
