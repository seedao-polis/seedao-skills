#!/usr/bin/env python3
"""
community_wiki_init.py — 初始化 Community Wiki 目录结构

生成 Obsidian 兼容的 vault 结构：
  - 所有人类可读内容都是 Markdown
  - _data/ 存放机器生成的 JSON
  - Markdown 由脚本自动生成/刷新

Usage:
    python community_wiki_init.py --name "我的社区" --values "共在,涌现,逍遥" --output ./my-community
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone


def git_init_repo(repo_dir: str):
    """Initialize git repo if not already one."""
    git_dir = os.path.join(repo_dir, ".git")
    if os.path.isdir(git_dir):
        print("Git repo already exists, skipping git init")
        return
    try:
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        print("Git repo initialized")
    except subprocess.CalledProcessError as e:
        print(f"Warning: git init failed: {e}")


def git_commit(repo_dir: str, message: str):
    """Stage all changes and commit if there are any."""
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


def init_community(name: str, values: list[str], output_dir: str, founders: list[str] | None = None):
    """Initialize a new community directory with all required structure."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_data", "events"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_data", "people"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "people"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "events"), exist_ok=True)

    community = {
        "id": name.lower().replace(" ", "-").replace("_", "-"),
        "name": name,
        "values": values,
        "manifesto": "",
        "tags": [],
        "founders": founders or [],
        "admins": founders or [],
        "treasury": {"currency": "", "balance": 0.0, "policy": ""},
        "links": {},
        "created_at": int(datetime.now(timezone.utc).timestamp()),
    }

    # Save _data/community.json
    community_path = os.path.join(output_dir, "_data", "community.json")
    with open(community_path, "w", encoding="utf-8") as f:
        json.dump(community, f, ensure_ascii=False, indent=2)

    # Write SCHEMA.md
    schema_lines = [
        "# Community Schema",
        "",
        f"## Domain: {name}",
        "",
        "## Conventions",
        "- File names: lowercase, hyphens, no spaces",
        "- Every page starts with YAML frontmatter",
        "- Use [[wikilinks]] to link between pages",
        "- _data/ is machine-generated; edit Markdown files instead",
        "- log.md is append-only",
        "",
        "## Page Types",
        "- `community` — 社区主页",
        "- `person` — 成员页",
        "- `event` — Event 页",
        "- `graph` — 关系图谱",
        "- `state` — 状态记录",
        "- `log` — 操作日志",
        "",
    ]
    with open(os.path.join(output_dir, "SCHEMA.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(schema_lines) + "\n")

    # Write initial log.md
    log_lines = [
        "---",
        "title: 操作日志",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: log",
        "tags: []",
        "---",
        "",
        "# 操作日志",
        "",
        "> Chronological record of all community actions. Append-only.",
        "> Format: `## [YYYY-MM-DD] action | subject`",
        "",
        f"## [{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] create | Community initialized",
        f"- Name: {name}",
        f"- Values: {', '.join(values)}",
        f"- Founders: {', '.join(founders or [])}",
        "",
    ]
    with open(os.path.join(output_dir, "log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    # Write initial index.md
    index_lines = [
        "---",
        "title: Wiki Index",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: index",
        "tags: []",
        "---",
        "",
        f"# {name} — Community Wiki Index",
        "",
        "> Content catalog. Every page listed with a one-line summary.",
        "> Read this first to find relevant pages.",
        "",
        "## 社区概览",
        "",
        f"- [[community|社区主页]] — 价值观、状态指标、活跃成员",
        "",
        "## 成员",
        "",
        "## Event 记录",
        "",
        "## 关系网络",
        "",
        "- [[graph|关系图谱]] — 社区关系密度可视化",
        "",
        "## 日志",
        "",
        "- [[log|操作日志]] — 社区变更记录",
        "",
    ]
    with open(os.path.join(output_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

    # Write initial community.md
    community_md_lines = [
        "---",
        f"title: {name}",
        f"created: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: community",
        f"tags: [{', '.join(values)}]",
        "---",
        "",
        f"# {name}",
        "",
        "## 价值观",
        "",
    ]
    for v in values:
        community_md_lines.append(f"- {v}")
    community_md_lines.extend([
        "",
        "## 社区状态指标",
        "",
        "| 指标 | 数值 | 含义 |",
        "|------|------|------|",
        "| 共在 (Co-presence) | — | 社区是否『连起来了』 |",
        "| 涌现 (Emergence) | — | 社区是否『产生了东西』 |",
        "| 逍遥 (Xiaoyao) | — | 个体能否自由生成关系 |",
        "",
        "## 活跃成员",
        "",
        "（暂无成员）",
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[graph|关系图谱]]",
        "- [[log|操作日志]]",
        "",
    ])
    with open(os.path.join(output_dir, "community.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(community_md_lines) + "\n")

    # Write initial state.md
    state_lines = [
        "---",
        "title: 社区状态历史",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: state",
        "tags: []",
        "---",
        "",
        "# 社区状态历史",
        "",
        "> Append-only record of community state over time.",
        "",
        "| 日期 | 共在 | 涌现 | 逍遥 | 成员数 | Event数 |",
        "|------|------|------|------|--------|---------|",
        "",
    ]
    with open(os.path.join(output_dir, "state.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(state_lines) + "\n")

    # Write initial graph.md
    graph_lines = [
        "---",
        "title: 关系图谱",
        f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "type: graph",
        "tags: []",
        "---",
        "",
        "# 关系图谱",
        "",
        "- 节点数: 0",
        "- 边数: 0",
        "",
        "## 关系列表",
        "",
        "（暂无关系）",
        "",
        "## 相关页面",
        "",
        "- [[index|返回索引]]",
        "- [[community|社区主页]]",
        "",
    ]
    with open(os.path.join(output_dir, "graph.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(graph_lines) + "\n")

    # Git init and first commit
    git_init_repo(output_dir)
    git_commit(output_dir, f"init: Community '{name}' initialized")

    print(f"\nCommunity initialized at: {output_dir}")
    print(f"  - SCHEMA.md (社区约定)")
    print(f"  - index.md (总索引)")
    print(f"  - community.md (社区主页)")
    print(f"  - state.md (状态历史)")
    print(f"  - graph.md (关系图谱)")
    print(f"  - log.md (操作日志)")
    print(f"  - people/ (成员页)")
    print(f"  - events/ (Event页)")
    print(f"  - _data/ (机器生成的 JSON)")
    print(f"  - .git/ (版本追踪)")


def main():
    parser = argparse.ArgumentParser(description="Initialize a Community LLM Wiki")
    parser.add_argument("--name", required=True, help="Community name")
    parser.add_argument("--values", default="共在,涌现,逍遥", help="Comma-separated community values")
    parser.add_argument("--founders", default="", help="Comma-separated founder names")
    parser.add_argument("--output", default="./my-community", help="Output directory")
    args = parser.parse_args()

    values = [v.strip() for v in args.values.split(",") if v.strip()]
    founders = [f.strip() for f in args.founders.split(",") if f.strip()] if args.founders else []

    init_community(args.name, values, args.output, founders)


if __name__ == "__main__":
    main()
