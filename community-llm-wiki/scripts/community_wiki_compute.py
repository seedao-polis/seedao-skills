#!/usr/bin/env python3
"""
community_wiki_compute.py — 计算关系图谱与社区状态

计算内容：
  1. Relationship Density Graph（关系密度图）
  2. Community State（三指标：共在/涌现/逍遥）
  3. 个人逍遥指数

Usage:
    python community_wiki_compute.py --community ./my-community --output ./my-community/state
"""
import argparse
import json
import math
import os
from collections import defaultdict


# Relationship density contribution per role pair
CONTRIB = {
    ("initiator", "co_creator"): 3.0,
    ("co_creator", "initiator"): 3.0,
    ("co_creator", "co_creator"): 2.5,
    ("initiator", "participant"): 1.5,
    ("participant", "initiator"): 1.5,
    ("co_creator", "participant"): 1.2,
    ("participant", "co_creator"): 1.2,
    ("participant", "participant"): 1.0,
}


def load_events(events_dir: str) -> list[dict]:
    """Load all events from the events directory."""
    events = []
    if not os.path.isdir(events_dir):
        return events
    for fname in sorted(os.listdir(events_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(events_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            events.append(json.load(f))
    return events


def load_people(people_dir: str) -> dict[str, dict]:
    """Load all people from the people directory."""
    people = {}
    if not os.path.isdir(people_dir):
        return people
    for fname in os.listdir(people_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(people_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        people[data.get("id", fname[:-5])] = data
    return people


def compute_graph(events: list[dict]) -> dict:
    """Compute relationship density graph from events."""
    density = defaultdict(float)
    edge_events = defaultdict(list)

    for event in events:
        eid = event["id"]
        roles = {}
        if event.get("initiator"):
            roles[event["initiator"]] = "initiator"
        for cid in event.get("co_creators", []):
            roles[cid] = "co_creator"
        for pid in event.get("participants", []):
            if pid not in roles:
                roles[pid] = "participant"

        people_in_event = list(roles.keys())
        for i in range(len(people_in_event)):
            for j in range(i + 1, len(people_in_event)):
                a, b = people_in_event[i], people_in_event[j]
                role_a, role_b = roles[a], roles[b]
                contrib = CONTRIB.get((role_a, role_b), 0.5)
                pair = tuple(sorted([a, b]))
                density[pair] += contrib
                edge_events[pair].append(eid)

    nodes = set()
    edges = []
    for (a, b), d in density.items():
        nodes.add(a)
        nodes.add(b)
        rel_type = "weak" if d < 3 else ("normal" if d <= 10 else "strong")
        edges.append({
            "source": a,
            "target": b,
            "density": round(d, 2),
            "type": rel_type,
            "events": edge_events[(a, b)],
        })

    return {
        "nodes": [{"id": n} for n in sorted(nodes)],
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }


def compute_co_presence(graph: dict, people_count: int) -> float:
    """Compute co-presence metric."""
    if people_count == 0:
        return 0.0
    E = graph["stats"]["edge_count"]
    # Simple clustering: count connected components via union-find
    parent = {n["id"]: n["id"] for n in graph["nodes"]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for e in graph["edges"]:
        union(e["source"], e["target"])

    clusters = len(set(find(n["id"]) for n in graph["nodes"]))
    C = clusters / people_count if people_count else 0
    return round((E / people_count) + C, 4)


def compute_emergence(events: list[dict]) -> float:
    """Compute emergence metric: artifacts per event."""
    if not events:
        return 0.0
    total_artifacts = sum(len(e.get("artifacts", [])) for e in events)
    return round(total_artifacts / len(events), 4)


def compute_entropy(counts: list[int]) -> float:
    """Compute Shannon entropy for role distribution."""
    total = sum(counts)
    if total == 0:
        return 0.0
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return entropy


def compute_xiaoyao(person: dict) -> dict:
    """Compute individual xiaoyao (structural freedom) score."""
    refs = person.get("event_refs", [])
    if not refs:
        return {"ir": 0.0, "re": 0.0, "nr": 0.0, "score": 0.0}

    total = len(refs)
    initiator_count = sum(1 for r in refs if r["role"] == "initiator")
    co_count = sum(1 for r in refs if r["role"] == "co_creator")
    part_count = sum(1 for r in refs if r["role"] == "participant")

    IR = initiator_count / total
    RE = compute_entropy([initiator_count, co_count, part_count])
    # NR simplified: ratio of unique events to total (proxy for network reach)
    unique_events = len(set(r["event_id"] for r in refs))
    NR = unique_events / total if total else 0.0

    score = 0.4 * IR + 0.3 * RE + 0.3 * NR
    return {
        "ir": round(IR, 4),
        "re": round(RE, 4),
        "nr": round(NR, 4),
        "score": round(score, 4),
    }


def compute_community_state(graph: dict, events: list[dict], people: dict[str, dict]) -> dict:
    """Compute full community state with all three metrics."""
    people_count = len(people)
    co_presence = compute_co_presence(graph, people_count)
    emergence = compute_emergence(events)

    xiaoyao_scores = {}
    for pid, person in people.items():
        xiaoyao_scores[pid] = compute_xiaoyao(person)

    community_xiaoyao = (
        sum(x["score"] for x in xiaoyao_scores.values()) / len(xiaoyao_scores)
        if xiaoyao_scores else 0.0
    )

    return {
        "co_presence": co_presence,
        "emergence": emergence,
        "xiaoyao": round(community_xiaoyao, 4),
        "people_count": people_count,
        "event_count": len(events),
        "edge_count": graph["stats"]["edge_count"],
        "individual_xiaoyao": xiaoyao_scores,
    }


def main():
    parser = argparse.ArgumentParser(description="Compute graph and state for a Community Wiki")
    parser.add_argument("--community", required=True, help="Community directory path")
    parser.add_argument("--output", help="Output directory for state files (default: community/state)")
    args = parser.parse_args()

    output_dir = args.output or os.path.join(args.community, "state")
    os.makedirs(output_dir, exist_ok=True)

    events_dir = os.path.join(args.community, "events")
    people_dir = os.path.join(args.community, "people")

    events = load_events(events_dir)
    people = load_people(people_dir)

    print(f"Loaded {len(events)} events, {len(people)} people")

    graph = compute_graph(events)
    state = compute_community_state(graph, events, people)

    graph_path = os.path.join(output_dir, "graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"Graph saved: {graph_path}")

    state_path = os.path.join(output_dir, "state.json")
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"State saved: {state_path}")

    print(f"\nCommunity State:")
    print(f"  Co-presence:  {state['co_presence']}")
    print(f"  Emergence:    {state['emergence']}")
    print(f"  Xiaoyao:      {state['xiaoyao']}")
    print(f"  People:       {state['people_count']}")
    print(f"  Events:       {state['event_count']}")
    print(f"  Edges:        {state['edge_count']}")


if __name__ == "__main__":
    main()
