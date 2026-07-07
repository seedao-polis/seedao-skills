#!/usr/bin/env python3
"""
community_wiki_generate.py — 将社区数据生成为 Markdown Wiki

基于 Event 原始数据和计算出的图谱/状态，生成一组互相关联的 Markdown 文件，
形成完整的社区知识图谱 Wiki。兼容 Obsidian、GitHub、任何支持 [[wikilinks]] 的工具。

Usage:
    python community_wiki_generate.py --community ./my-community --output ./my-community/wiki
"""
import argparse
import json
import os
from datetime import datetime, timezone


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


def generate_index(wiki_dir: str, community: dict, people: dict[str, dict], events: dict[str, dict]):
    lines = [
        f"# {community['name']} - Community Wiki Index",
        "",
        f"> 最后更新: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"> 总页数: {len(people) + len(events) + 4}",
        "",
        "## 社区概览",
        "",
        "- [[community|社区主页]] - 价值观、状态指标、活跃成员",
        "",
        f"## 成员 ({len(people)})",
        "",
    ]
    for pid in sorted(people.keys()):
        p = people[pid]
        name = p.get("profile", {}).get("name", pid)
        event_count = len(p.get("event_refs", []))
        lines.append(f"- [[people/{pid}|{name}]] - 参与 {event_count} 个 Event")

    lines.extend([
        "",
        f"## Event 记录 ({len(events)})",
        "",
    ])
    for eid in sorted(events.keys(), key=lambda x: events[x]["timestamp"]):
        e = events[eid]
        title = e.get("metadata", {}).get("title", eid)
        date_str = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime('%Y-%m-%d')
        lines.append(f"- [[events/{eid}|{title}]] - {date_str}")

    lines.extend([
        "",
        "## 关系网络",
        "",
        "- [[graph|关系图谱]] - 社区关系密度可视化数据",
        "",
        "## 日志",
        "",
        "- [[log|操作日志]] - 社区变更记录",
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
        lines.append(f"- [[people/{pid}|{name}]] - 逍遥指数: {x['score']}")

    lines.extend([
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[graph|关系图谱]]",
        "- [[log|操作日志]]",
        "",
    ])

    with open(os.path.join(wiki_dir, "community.md"), "w", encoding="utf-8") as f:
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
            lines.append(f"- [[events/{eid}|{title}]] ({date_str}) - 角色: {role_cn}")

        if pid in adj and adj[pid]:
            lines.extend(["", "## 关系网络", ""])
            for target_id, density, rel_type in adj[pid]:
                target_name = people.get(target_id, {}).get("profile", {}).get("name", target_id)
                type_cn = type_map.get(rel_type, rel_type)
                lines.append(f"- [[people/{target_id}|{target_name}]] - 密度: {density} ({type_cn})")

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


def generate_log(wiki_dir: str, community_dir: str):
    log_src = os.path.join(community_dir, "log.md")
    if os.path.exists(log_src):
        with open(log_src, "r", encoding="utf-8") as f:
            log_content = f.read()
    else:
        log_content = "# 操作日志\n\n暂无记录。\n"

    lines = [
        "---",
        "title: 操作日志",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: log",
        "tags: []",
        "---",
        "",
        log_content,
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[community|社区主页]]",
        "",
    ]

    with open(os.path.join(wiki_dir, "log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown Wiki from Community Wiki data")
    parser.add_argument("--community", required=True, help="Community directory path")
    parser.add_argument("--output", help="Output wiki directory (default: community/wiki)")
    args = parser.parse_args()

    wiki_dir = args.output or os.path.join(args.community, "wiki")
    os.makedirs(wiki_dir, exist_ok=True)

    community = load_json(os.path.join(args.community, "community.json"))
    state = load_json(os.path.join(args.community, "state", "state.json"))
    graph = load_json(os.path.join(args.community, "state", "graph.json"))
    people = load_all_people(os.path.join(args.community, "people"))
    events = load_all_events(os.path.join(args.community, "events"))

    if not community:
        print("Error: community.json not found")
        return
    if not state or not graph:
        print("Error: state/graph not computed yet. Run community_wiki_compute.py first.")
        return

    adj = build_adjacency(graph)

    generate_index(wiki_dir, community, people, events)
    generate_community(wiki_dir, community, state, people)
    generate_people(wiki_dir, people, events, state, adj)
    generate_events(wiki_dir, events, people)
    generate_graph(wiki_dir, graph, people, events)
    generate_log(wiki_dir, args.community)

    # Count files
    file_count = 0
    for _, _, files in os.walk(wiki_dir):
        file_count += len(files)

    print(f"Wiki generated at: {wiki_dir}")
    print(f"  Total pages: {file_count}")
    print(f"  - index.md (索引)")
    print(f"  - community.md (社区主页)")
    print(f"  - graph.md (关系图谱)")
    print(f"  - log.md (操作日志)")
    print(f"  - people/ ({len(people)} 成员页)")
    print(f"  - events/ ({len(events)} Event 页)")


if __name__ == "__main__":
    main()
