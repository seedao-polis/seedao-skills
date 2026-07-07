#!/usr/bin/env python3
"""
community_wiki_query.py — 社区查询与导航接口

支持查询类型：
  - state      : 社区整体状态
  - person     : 个人档案与逍遥指数
  - graph      : 关系网络（支持深度过滤）
  - recommend  : 为指定用户推荐连接/活动

Usage:
    python community_wiki_query.py --community ./my-community --query state
    python community_wiki_query.py --community ./my-community --query person --id alice
    python community_wiki_query.py --community ./my-community --query graph --depth 2
    python community_wiki_query.py --community ./my-community --query recommend --for alice
"""
import argparse
import json
import os
from collections import defaultdict


def load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def query_state(community_dir: str):
    state = load_json(os.path.join(community_dir, "state", "state.json"))
    if not state:
        print("State not computed yet. Run community_wiki_compute.py first.")
        return
    print(json.dumps(state, ensure_ascii=False, indent=2))


def query_person(community_dir: str, person_id: str):
    person = load_json(os.path.join(community_dir, "people", f"{person_id}.json"))
    state = load_json(os.path.join(community_dir, "state", "state.json"))
    if not person:
        print(f"Person '{person_id}' not found.")
        return

    print(f"=== Person: {person_id} ===")
    print(json.dumps(person, ensure_ascii=False, indent=2))

    if state and "individual_xiaoyao" in state:
        x = state["individual_xiaoyao"].get(person_id)
        if x:
            print(f"\n=== Xiaoyao Score ===")
            print(f"  IR (Initiator Ratio):  {x['ir']}")
            print(f"  RE (Role Entropy):     {x['re']}")
            print(f"  NR (Network Reach):    {x['nr']}")
            print(f"  Score:                 {x['score']}")


def query_graph(community_dir: str, depth: int | None = None, center: str | None = None):
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))
    if not graph:
        print("Graph not computed yet. Run community_wiki_compute.py first.")
        return

    if not center:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
        return

    # BFS to find nodes within depth
    adj = defaultdict(list)
    for e in graph.get("edges", []):
        adj[e["source"]].append(e["target"])
        adj[e["target"]].append(e["source"])

    visited = {center}
    current = {center}
    for _ in range(depth or 1):
        nxt = set()
        for n in current:
            for neighbor in adj[n]:
                if neighbor not in visited:
                    nxt.add(neighbor)
        visited.update(nxt)
        current = nxt

    filtered_nodes = [n for n in graph["nodes"] if n["id"] in visited]
    filtered_edges = [e for e in graph["edges"] if e["source"] in visited and e["target"] in visited]

    result = {
        "center": center,
        "depth": depth,
        "nodes": filtered_nodes,
        "edges": filtered_edges,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def query_recommend(community_dir: str, person_id: str):
    """Recommend connections for a person based on graph structure."""
    graph = load_json(os.path.join(community_dir, "state", "graph.json"))
    people_dir = os.path.join(community_dir, "people")
    if not graph:
        print("Graph not computed yet. Run community_wiki_compute.py first.")
        return

    # Build adjacency
    adj = defaultdict(dict)
    for e in graph.get("edges", []):
        adj[e["source"]][e["target"]] = e["density"]
        adj[e["target"]][e["source"]] = e["density"]

    if person_id not in adj:
        print(f"Person '{person_id}' has no connections yet.")
        return

    # Friend-of-friend recommendation
    direct = set(adj[person_id].keys())
    scores = defaultdict(float)
    for friend in direct:
        for fof, density in adj[friend].items():
            if fof == person_id or fof in direct:
                continue
            scores[fof] += density

    recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

    print(f"=== Recommendations for {person_id} ===")
    if not recommendations:
        print("No friend-of-friend recommendations found.")
        return

    for rec_id, score in recommendations:
        person = load_json(os.path.join(people_dir, f"{rec_id}.json"))
        name = person.get("profile", {}).get("name", rec_id) if person else rec_id
        print(f"  - {name} ({rec_id}): score {round(score, 2)}")


def main():
    parser = argparse.ArgumentParser(description="Query a Community Wiki")
    parser.add_argument("--community", required=True, help="Community directory path")
    parser.add_argument("--query", required=True, choices=["state", "person", "graph", "recommend"], help="Query type")
    parser.add_argument("--id", help="Person ID (for person query)")
    parser.add_argument("--depth", type=int, help="Graph depth (for graph query)")
    parser.add_argument("--for", dest="for_person", help="Person ID (for recommend query)")
    parser.add_argument("--center", help="Center node (for graph query)")
    args = parser.parse_args()

    if args.query == "state":
        query_state(args.community)
    elif args.query == "person":
        if not args.id:
            parser.error("--id required for person query")
        query_person(args.community, args.id)
    elif args.query == "graph":
        query_graph(args.community, depth=args.depth, center=args.center)
    elif args.query == "recommend":
        if not args.for_person:
            parser.error("--for required for recommend query")
        query_recommend(args.community, args.for_person)


if __name__ == "__main__":
    main()
