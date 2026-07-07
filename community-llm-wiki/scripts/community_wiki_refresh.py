#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
community_wiki_refresh.py — 核心脚本：计算图谱状态 + 生成所有 Markdown

这是 community-llm-wiki 的核心刷新脚本。它会：
  1. 读取 _data/ 中的 JSON 数据
  2. 计算 graph.json + state.json
  3. 生成/更新所有 Markdown 页面
  4. 追加 log.md
  5. 输出更新摘要

Usage:
    python community_wiki_refresh.py --community ./my-community
"""
import argparse
import json
import math
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


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


def git_commit(repo_dir: str, message: str):
    """Stage all changes and commit if there are any."""
    git_dir = os.path.join(repo_dir, ".git")
    if not os.path.isdir(git_dir):
        return  # Not a git repo, skip silently
    try:
        # Check if there are any changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            return  # Nothing to commit

        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        print(f"Git commit: {message}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: git commit failed: {e}")


def load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_people(people_dir: str) -> dict[str, dict]:
    people = {}
    if not os.path.isdir(people_dir):
        return people
    for fname in sorted(os.listdir(people_dir)):
        if not fname.endswith(".json"):
            continue
        pid = fname[:-5]
        people[pid] = load_json(os.path.join(people_dir, fname))
    return people


def load_all_events(events_dir: str) -> dict[str, dict]:
    events = {}
    if not os.path.isdir(events_dir):
        return events
    for fname in sorted(os.listdir(events_dir)):
        if not fname.endswith(".json"):
            continue
        eid = fname[:-5]
        events[eid] = load_json(os.path.join(events_dir, fname))
    return events


def compute_graph(events: dict[str, dict]) -> dict:
    """Compute relationship density graph from events."""
    density = defaultdict(float)
    edge_events = defaultdict(list)

    for eid, event in events.items():
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
    if people_count == 0:
        return 0.0
    E = graph["stats"]["edge_count"]
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


def compute_emergence(events: dict[str, dict]) -> float:
    if not events:
        return 0.0
    total_artifacts = sum(len(e.get("artifacts", [])) for e in events.values())
    return round(total_artifacts / len(events), 4)


def compute_entropy(counts: list[int]) -> float:
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
    refs = person.get("event_refs", [])
    if not refs:
        return {"ir": 0.0, "re": 0.0, "nr": 0.0, "score": 0.0}

    total = len(refs)
    initiator_count = sum(1 for r in refs if r["role"] == "initiator")
    co_count = sum(1 for r in refs if r["role"] == "co_creator")
    part_count = sum(1 for r in refs if r["role"] == "participant")

    IR = initiator_count / total
    RE = compute_entropy([initiator_count, co_count, part_count])
    unique_events = len(set(r["event_id"] for r in refs))
    NR = unique_events / total if total else 0.0

    score = 0.4 * IR + 0.3 * RE + 0.3 * NR
    return {
        "ir": round(IR, 4),
        "re": round(RE, 4),
        "nr": round(NR, 4),
        "score": round(score, 4),
    }


def compute_community_state(graph: dict, events: dict[str, dict], people: dict[str, dict]) -> dict:
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


def build_adjacency(graph: dict) -> dict[str, list[tuple[str, float, str]]]:
    adj = {}
    for n in graph.get("nodes", []):
        adj[n["id"]] = []
    for e in graph.get("edges", []):
        adj[e["source"]].append((e["target"], e["density"], e["type"]))
        adj[e["target"]].append((e["source"], e["density"], e["type"]))
    for k in adj:
        adj[k].sort(key=lambda x: -x[1])
    return adj


# ===== Markdown Generation =====

def generate_index(wiki_dir: str, community: dict, people: dict[str, dict], events: dict[str, dict]):
    lines = [
        "---",
        "title: Wiki Index",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: index",
        "tags: []",
        "---",
        "",
        f"# {community['name']} — Community Wiki Index",
        "",
        "> Content catalog. Every page listed with a one-line summary.",
        "> Read this first to find relevant pages.",
        "",
        "## 社区概览",
        "",
        "- [[community|社区主页]] — 价值观、状态指标、活跃成员",
        "",
        f"## 成员 ({len(people)})",
        "",
    ]
    for pid in sorted(people.keys()):
        p = people[pid]
        name = p.get("profile", {}).get("name", pid)
        event_count = len(p.get("event_refs", []))
        lines.append(f"- [[people/{pid}|{name}]] — 参与 {event_count} 个 Event")

    lines.extend([
        "",
        f"## Event 记录 ({len(events)})",
        "",
    ])
    for eid in sorted(events.keys(), key=lambda x: events[x]["timestamp"]):
        e = events[eid]
        title = e.get("metadata", {}).get("title", eid)
        date_str = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime('%Y-%m-%d')
        lines.append(f"- [[events/{eid}|{title}]] — {date_str}")

    lines.extend([
        "",
        "## 关系网络",
        "",
        "- [[graph|关系图谱]] — 社区关系密度可视化",
        "",
        "## 状态历史",
        "",
        "- [[state|社区状态历史]] — 三指标时间序列",
        "",
        "## 日志",
        "",
        "- [[log|操作日志]] — 社区变更记录",
        "",
    ])

    with open(os.path.join(wiki_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_community(wiki_dir: str, community: dict, state: dict, people: dict[str, dict]):
    lines = [
        "---",
        f"title: {community['name']}",
        f"created: {datetime.fromtimestamp(community['created_at'], tz=timezone.utc).strftime('%Y-%m-%d')}",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: community",
        f"tags: [{', '.join(community.get('tags', []))}]",
        "---",
        "",
        f"# {community['name']}",
        "",
        "## 价值观",
        "",
    ]
    for v in community.get("values", []):
        lines.append(f"- {v}")

    if community.get("manifesto"):
        lines.extend(["", "## 宣言", "", community["manifesto"]])

    lines.extend([
        "",
        "## 社区状态指标",
        "",
        "| 指标 | 数值 | 含义 |",
        "|------|------|------|",
        f"| 共在 (Co-presence) | {state['co_presence']} | 社区是否『连起来了』 |",
        f"| 涌现 (Emergence) | {state['emergence']} | 社区是否『产生了东西』 |",
        f"| 逍遥 (Xiaoyao) | {state['xiaoyao']} | 个体能否自由生成关系 |",
        "",
        f"- 成员数: {state['people_count']}",
        f"- Event 数: {state['event_count']}",
        f"- 关系边数: {state['edge_count']}",
        "",
        "## 活跃成员",
        "",
    ])

    sorted_people = sorted(
        state.get("individual_xiaoyao", {}).items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )
    for pid, x in sorted_people:
        name = people.get(pid, {}).get("profile", {}).get("name", pid)
        lines.append(f"- [[people/{pid}|{name}]] — 逍遥指数: {x['score']}")

    lines.extend([
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[graph|关系图谱]]",
        "- [[state|状态历史]]",
        "- [[log|操作日志]]",
        "",
    ])

    with open(os.path.join(wiki_dir, "community.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_state(wiki_dir: str, state: dict):
    """Append current state to state.md history table."""
    state_path = os.path.join(wiki_dir, "state.md")
    
    # Read existing content
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# 社区状态历史\n\n> Append-only record of community state over time.\n\n| 日期 | 共在 | 涌现 | 逍遥 | 成员数 | Event数 |\n|------|------|------|------|--------|---------|\n"

    # Append new row
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    new_row = f"| {date_str} | {state['co_presence']} | {state['emergence']} | {state['xiaoyao']} | {state['people_count']} | {state['event_count']} |"
    
    # Insert before the last empty lines if any
    lines = content.rstrip().split("\n")
    lines.append(new_row)
    lines.append("")  # trailing newline
    
    with open(state_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_people(wiki_dir: str, people: dict[str, dict], events: dict[str, dict], state: dict, adj: dict):
    people_wiki_dir = os.path.join(wiki_dir, "people")
    os.makedirs(people_wiki_dir, exist_ok=True)

    role_map = {"initiator": "发起人", "co_creator": "共创人", "participant": "参与者"}
    type_map = {"strong": "强", "normal": "中", "weak": "弱"}

    for pid, p in people.items():
        name = p.get("profile", {}).get("name", pid)
        x = state.get("individual_xiaoyao", {}).get(pid, {})
        refs = p.get("event_refs", [])

        lines = [
            "---",
            f"title: {name}",
            "type: person",
            f"tags: [{', '.join(p.get('skills', []))}]",
            f"xiaoyao: {x.get('score', 0)}",
            f"events: {len(refs)}",
            "---",
            "",
            f"# {name}",
            "",
        ]

        if p.get("profile", {}).get("bio"):
            lines.extend([p["profile"]["bio"], ""])

        lines.extend([
            "## 逍遥指数 (Xiaoyao)",
            "",
            "| 维度 | 数值 |",
            "|------|------|",
            f"| 发起能力 (IR) | {x.get('ir', 0)} |",
            f"| 角色多样性 (RE) | {x.get('re', 0)} |",
            f"| 网络扩展 (NR) | {x.get('nr', 0)} |",
            f"| **总分** | **{x.get('score', 0)}** |",
            "",
        ])

        if p.get("skills"):
            lines.extend(["## 技能", "", ", ".join(p["skills"]), ""])
        if p.get("interests"):
            lines.extend(["## 兴趣", "", ", ".join(p["interests"]), ""])

        lines.extend(["## Event 参与记录", ""])
        for ref in sorted(refs, key=lambda r: r["timestamp"]):
            eid = ref["event_id"]
            e = events.get(eid, {})
            title = e.get("metadata", {}).get("title", eid)
            date_str = datetime.fromtimestamp(ref["timestamp"], tz=timezone.utc).strftime('%Y-%m-%d')
            role_cn = role_map.get(ref["role"], ref["role"])
            lines.append(f"- [[events/{eid}|{title}]] ({date_str}) — 角色: {role_cn}")

        if pid in adj and adj[pid]:
            lines.extend(["", "## 关系网络", ""])
            for target_id, density, rel_type in adj[pid]:
                target_name = people.get(target_id, {}).get("profile", {}).get("name", target_id)
                type_cn = type_map.get(rel_type, rel_type)
                lines.append(f"- [[people/{target_id}|{target_name}]] — 密度: {density} ({type_cn})")

        lines.extend([
            "",
            "## 相关页面",
            "",
            "- [[index|返回索引]]",
            "- [[community|社区主页]]",
            "",
        ])

        with open(os.path.join(people_wiki_dir, f"{pid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def generate_events(wiki_dir: str, events: dict[str, dict], people: dict[str, dict]):
    events_wiki_dir = os.path.join(wiki_dir, "events")
    os.makedirs(events_wiki_dir, exist_ok=True)

    for eid, e in events.items():
        title = e.get("metadata", {}).get("title", eid)
        date_str = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')

        lines = [
            "---",
            f"title: {title}",
            f"created: {date_str}",
            f"updated: {date_str}",
            f"type: {e.get('type', 'activity')}",
            "tags: []",
            "---",
            "",
            f"# {title}",
            "",
            f"- **类型**: {e.get('type', 'activity')}",
            f"- **时间**: {date_str}",
            "",
        ]

        if e.get("metadata", {}).get("description"):
            lines.extend([e["metadata"]["description"], ""])

        lines.extend(["## 参与者", ""])

        initiator = e.get("initiator")
        if initiator:
            name = people.get(initiator, {}).get("profile", {}).get("name", initiator)
            lines.append(f"- **发起人**: [[people/{initiator}|{name}]]")

        for cid in e.get("co_creators", []):
            name = people.get(cid, {}).get("profile", {}).get("name", cid)
            lines.append(f"- **共创人**: [[people/{cid}|{name}]]")

        for pid in e.get("participants", []):
            name = people.get(pid, {}).get("profile", {}).get("name", pid)
            lines.append(f"- **参与者**: [[people/{pid}|{name}]]")

        if e.get("artifacts"):
            lines.extend(["", "## 协作产出", ""])
            for a in e["artifacts"]:
                lines.append(f"- [{a.get('description', a.get('type', 'link'))}]({a['url']})")

        if e.get("external"):
            ext = e["external"]
            lines.extend(["", "## 外部来源", ""])
            if ext.get("source_name"):
                lines.append(f"- 来源: {ext['source_name']}")
            if ext.get("url"):
                lines.append(f"- 链接: {ext['url']}")

        lines.extend([
            "",
            "## 相关页面",
            "",
            "- [[index|返回索引]]",
            "- [[community|社区主页]]",
            "",
        ])

        with open(os.path.join(events_wiki_dir, f"{eid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def generate_graph(wiki_dir: str, graph: dict, people: dict[str, dict], events: dict[str, dict]):
    type_map = {"strong": "强", "normal": "中", "weak": "弱"}

    lines = [
        "---",
        "title: 关系图谱",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: graph",
        "tags: []",
        "---",
        "",
        "# 关系图谱",
        "",
        f"- 节点数: {graph['stats']['node_count']}",
        f"- 边数: {graph['stats']['edge_count']}",
        "",
        "## 关系列表",
        "",
        "| 成员 A | 成员 B | 密度 | 类型 | 共同 Event |",
        "|--------|--------|------|------|-----------|",
    ]

    for e in sorted(graph["edges"], key=lambda x: -x["density"]):
        a_name = people.get(e["source"], {}).get("profile", {}).get("name", e["source"])
        b_name = people.get(e["target"], {}).get("profile", {}).get("name", e["target"])
        type_cn = type_map.get(e["type"], e["type"])
        event_links = ", ".join([
            f"[[events/{ev}|{events.get(ev, {}).get('metadata', {}).get('title', ev)}]]"
            for ev in e.get("events", [])
        ])
        lines.append(
            f"| [[people/{e['source']}|{a_name}]] | [[people/{e['target']}|{b_name}]] | {e['density']} | {type_cn} | {event_links} |"
        )

    lines.extend([
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[community|社区主页]]",
        "",
    ])

    with open(os.path.join(wiki_dir, "graph.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_summary(community_dir: str, state: dict, graph: dict, people: dict[str, dict], events: dict[str, dict]) -> str:
    """Generate a human-readable summary of what changed."""
    lines = [
        "=== Community Wiki 更新摘要 ===",
        "",
        f"📊 社区状态（{datetime.now(timezone.utc).strftime('%Y-%m-%d')}）",
        f"  • 共在 (Co-presence): {state['co_presence']}",
        f"  • 涌现 (Emergence): {state['emergence']}",
        f"  • 逍遥 (Xiaoyao): {state['xiaoyao']}",
        "",
        f"👥 成员: {state['people_count']} 人",
        f"📅 Event: {state['event_count']} 个",
        f"🔗 关系边: {state['edge_count']} 条",
        "",
    ]

    # Top xiaoyao
    sorted_xiaoyao = sorted(
        state.get("individual_xiaoyao", {}).items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:3]
    if sorted_xiaoyao:
        lines.append("🏆 逍遥指数 Top 3:")
        for pid, x in sorted_xiaoyao:
            name = people.get(pid, {}).get("profile", {}).get("name", pid)
            lines.append(f"  • {name}: {x['score']} (IR:{x['ir']}, RE:{x['re']}, NR:{x['nr']})")
        lines.append("")

    # Strong relationships
    strong_edges = [e for e in graph["edges"] if e["type"] == "strong"]
    if strong_edges:
        lines.append(f"💪 强关系 ({len(strong_edges)} 对):")
        for e in strong_edges[:5]:
            a_name = people.get(e["source"], {}).get("profile", {}).get("name", e["source"])
            b_name = people.get(e["target"], {}).get("profile", {}).get("name", e["target"])
            lines.append(f"  • {a_name} ↔ {b_name} (密度: {e['density']})")
        lines.append("")

    # Recent events
    recent_events = sorted(events.values(), key=lambda x: -x["timestamp"])[:3]
    if recent_events:
        lines.append("📌 最近 Event:")
        for e in recent_events:
            title = e.get("metadata", {}).get("title", e["id"])
            date_str = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime('%Y-%m-%d')
            lines.append(f"  • {title} ({date_str})")
        lines.append("")

    # Files updated
    lines.append("📝 已更新文件:")
    lines.append("  • index.md — 总索引")
    lines.append("  • community.md — 社区主页")
    lines.append("  • state.md — 状态历史（新增一行）")
    lines.append("  • graph.md — 关系图谱")
    lines.append(f"  • people/*.md — {len(people)} 个成员页")
    lines.append(f"  • events/*.md — {len(events)} 个 Event 页")
    lines.append("")

    # Incomplete info reminder
    incomplete_people = []
    for pid, p in people.items():
        if not p.get("profile", {}).get("name") or not p.get("skills"):
            incomplete_people.append(pid)
    
    if incomplete_people:
        lines.append("⚠️ 信息待完善:")
        for pid in incomplete_people:
            lines.append(f"  • {pid} — 缺少姓名或技能信息")
        lines.append("  建议补充：编辑 _data/people/<id>.json 后重新运行 refresh")
        lines.append("")

    lines.append("✅ Wiki 已刷新，可直接在 Obsidian 中查看")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Refresh Community Wiki")
    parser.add_argument("--community", required=True, help="Community directory path")
    args = parser.parse_args()

    community_dir = args.community
    data_dir = os.path.join(community_dir, "_data")

    # Load data
    community = load_json(os.path.join(data_dir, "community.json"))
    people = load_all_people(os.path.join(data_dir, "people"))
    events = load_all_events(os.path.join(data_dir, "events"))

    if not community:
        print("Error: _data/community.json not found. Run community_wiki_init.py first.")
        return

    print(f"Loaded {len(events)} events, {len(people)} people")

    # Compute
    graph = compute_graph(events)
    state = compute_community_state(graph, events, people)

    # Save computed data
    os.makedirs(os.path.join(data_dir, "state"), exist_ok=True)
    with open(os.path.join(data_dir, "state", "graph.json"), "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "state", "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # Generate Markdown
    adj = build_adjacency(graph)
    generate_index(community_dir, community, people, events)
    generate_community(community_dir, community, state, people)
    generate_state(community_dir, state)
    generate_people(community_dir, people, events, state, adj)
    generate_events(community_dir, events, people)
    generate_graph(community_dir, graph, people, events)

    # Generate and print summary
    summary = generate_summary(community_dir, state, graph, people, events)
    print(summary)

    # Append to log
    log_path = os.path.join(community_dir, "log.md")
    log_entry = [
        "",
        f"## [{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] refresh | Wiki updated",
        f"- Events: {len(events)}, People: {len(people)}, Edges: {graph['stats']['edge_count']}",
        f"- State: co_presence={state['co_presence']}, emergence={state['emergence']}, xiaoyao={state['xiaoyao']}",
    ]
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(log_entry) + "\n")

    # Git commit
    git_commit(
        community_dir,
        f"refresh: {len(events)} events, {len(people)} people, "
        f"co_presence={state['co_presence']}, emergence={state['emergence']}, xiaoyao={state['xiaoyao']}"
    )


if __name__ == "__main__":
    main()
