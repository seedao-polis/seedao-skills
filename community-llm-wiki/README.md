# Community LLM Wiki

基于「共在 / 涌现 / 逍遥 / 因作而是」哲学的关系网络型社区Wiki。

> 以 Event 为唯一事实源、以 Graph 为呈现方式、以 Person 为结构化节点，并通过 Agent 提供解释与导航。

## 快速开始

```bash
# 1. 初始化社区
python scripts/community_wiki_init.py --name "我的社区" --values "共在,涌现,逍遥" --output ./my-community

# 2. 录入 Event（单条或批量）
python scripts/community_wiki_ingest.py --community ./my-community --events-file events.jsonl

# 3. 一键刷新（计算图谱 + 生成 Markdown Wiki）
python scripts/community_wiki_refresh.py --community ./my-community

# 4. 从 URL 提取 Event（可选）
python scripts/community_wiki_extract.py --community ./my-community --url "https://..."

# 5. 查询与导航
python scripts/community_wiki_query.py --community ./my-community --query state

# 6. 导出数据（可选）
python scripts/community_wiki_export.py --community ./my-community --format markdown --output report.md
```

## 目录结构

```
my-community/
├── community.json          # Community 本体
├── events/                 # Event 原始数据（唯一事实源）
├── people/                 # Person 数据（含 event_refs）
├── asset/                  # 外部资料存档（URL获取的原文、截图等）
├── state/                  # 计算出的关系图谱 & 社区状态
│   ├── graph.json
│   └── state.json
├── log.md                  # 操作日志（append-only）
└── README.md
```

## 脚本工具

| 脚本 | 功能 |
|------|------|
| `community_wiki_init.py` | 初始化社区目录结构 |
| `community_wiki_ingest.py` | 导入 Event 数据，自动更新 Person event_refs |
| `community_wiki_compute.py` | 计算关系图谱（Graph）与社区三指标状态 |
| `community_wiki_generate.py` | **生成 Markdown Wiki**（核心输出） |
| `community_wiki_query.py` | 查询接口：state / person / graph / recommend |
| `community_wiki_extract.py` | 从 URL 获取内容，保存到 asset/，辅助提取 Event 信息 |
| `community_wiki_export.py` | 导出：GEXF / Cytoscape / Markdown / CSV |

## 设计文档

- [SKILL.md](SKILL.md) — 完整的 Skill 使用说明
- [references/DESIGN.md](references/DESIGN.md) — 原始设计文档参考

## 系统哲学

| 概念 | 含义 |
|------|------|
| **共在** | 社区的基础不是个体，而是关系 |
| **涌现** | 社区的价值来自协作，而非预设设计 |
| **逍遥** | 个体在网络中具备自由生成关系与切换角色的能力 |
| **因作而是** | 人不是身份，而是在持续行动（Event）中被生成的结构 |

## License

MIT
