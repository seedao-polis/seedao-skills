---
name: community-llm-wiki
description: "使用 LLM 构建和维护社区 Wiki。记录社区成员之间的协作事件（Event）和关系，计算生成社区状态指标（共在、涌现、逍遥）以及关系图谱。触发：初始化社区、录入 Event、刷新 Wiki、查询社区状态/个人档案/关系网络、数据审计、或提及「社区 Wiki」「社区知识图谱」「SeeDAO」。"
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [community, knowledge-graph, event-driven, wiki, collaboration, social-network]
    category: community
    related_skills: [karpathy-llm-wiki, obsidian, notion]
---

# Community LLM Wiki

使用 LLM 构建和维护一个社区 Wiki。

社区 Wiki 是一个文件夹，包含 Markdown 文件和 JSON 数据，记录社区成员之间的协作事件（Event）和关系，并通过计算生成社区状态指标（共在、涌现、逍遥）以及关系图谱。最终输出一个基于 Obsidian 的 Markdown Wiki，供社区成员浏览和查询。

核心思想：
- **Event 是唯一事实源** — 一切从 Event 推导，不预设关系
- **人在行动中被定义** — 人不是身份，而是在持续 Event 中被生成的结构
- **Wiki 随关系涌现而累积** — 社区价值来自协作，而非预先设计

## 目录结构（Obsidian Vault + Git 追踪）

```
my-community/
├── .git/                   # Git 版本控制（自动初始化）
├── SCHEMA.md               # 社区约定与结构规则
├── index.md                # 总索引
├── community.md            # 社区主页（价值观 + 状态指标）
├── state.md                # 社区状态历史（时间序列）
├── graph.md                # 关系图谱（当前快照）
├── log.md                  # 操作日志（append-only）
├── people/
│   ├── alice.md            # 个人页（档案 + Event记录 + 关系网络 + 逍遥指数）
│   ├── bob.md
│   └── ...
├── events/
│   ├── evt_001.md          # Event页（参与者 + 角色 + 产出）
│   ├── evt_002.md
│   └── ...
├── asset/                  # 外部资料存档（原文、截图、PDF等原始素材）
│   ├── wechat-article-001.md
│   ├── screenshot-2026-01-01.png
│   └── ...
└── _data/                  # 机器生成的原始数据（JSON，供脚本读取）
    ├── community.json
    ├── events/
    ├── people/
    ├── state/
    │   ├── state.json
    │   └── graph.json
    └── ...
```

## 数据结构

### _data/ 层（机器数据）

**community.json** — 社区元数据
- `id`, `name`, `values[]`, `manifesto`, `tags[]`, `founders[]`, `links{}`

**events/** — 事件记录
- `id`, `timestamp`, `type` (activity|project)
- `initiator`, `co_creators[]`, `participants[]`
- `metadata{title, description}`
- `artifacts[]` — 协作产出（link, doc, photo, video）
- `source{}`, `external{}`

**people/** — 成员档案
- `id`, `profile{}`, `skills[]`, `interests[]`, `links{}`
- `event_refs[]` — 参与事实（引用 Event，不存 Event 本体）

**state/** — 计算生成
- `state.json` — 社区状态指标
- `graph.json` — 关系图谱

### Markdown 层（人类可读）

所有 Markdown 文件由脚本自动生成，保持与 _data/ 同步。人类可直接阅读，但修改后会被 refresh 覆盖。

## 设计原则

1. **所有人类可读内容都是 Markdown** — 直接放入 Obsidian
2. **_data/ 目录存放机器生成的 JSON** — 脚本读取，人类通常不直接编辑
3. **Markdown 文件由脚本自动生成/刷新** — 保持与 _data/ 同步
4. **[[wikilinks]] 互相关联** — Obsidian Graph View 可视化
5. **YAML frontmatter** — 支持 Dataview 查询
6. **log.md append-only** — 记录所有变更
7. **Git 自动追踪** — 每次操作自动 commit，保留完整历史

## 操作流程

```
输入（聊天记录/会议纪要/活动信息/社交媒体信息等）
    ↓
Event Parser（数据清洗，解析，审查）
    ↓
Event（结构化数据）
    ↓
Person + Relationship（由 Event 计算得到）
    ↓
Graph + State（增量更新状态）
    ↓
Agent（构建并维护）
    ↓
Text + Links（Wiki 格式）
    ↓
用户
    ↓
Event（循环）
```

## 使用方式

### 初始化社区

触发条件：用户要求创建新社区，或提及某个社区但该社区目录不存在。

首先查找是否有现成的社区目录，同一个社区只需要初始化一次。如果找到了就直接使用，如果没有则创建一个新的社区目录，并自动初始化 Git 仓库，进行首次 commit。

```bash
# 使用脚本初始化（会自动 git init + 首次 commit）
python scripts/community_wiki_init.py --name "我的社区" --values "共在,涌现,逍遥" --output ./my-community
```

### 录入 Event

触发条件：用户提及参与某个活动、项目、协作，或要求录入 Event。

用户应该明确指出录入的 Event 属于哪个社区，如果没有指定社区，LLM 根据上下文判断应该录入哪个社区，如果无法判断则进行交互式询问。

使用LLM的能力理解用户输入的事件信息，结构化为 Event 数据结构。如果有大量 Event，可以先准备一个 JSON 文件或 JSONL 文件批量导入。如果用户输入的信息不完整或有歧义，进行交互式询问，直到获得足够信息来构建 Event。

```bash
# 从 JSON 文件导入（单条）
python scripts/community_wiki_ingest.py --community ./my-community --event-file event.json

# 从 JSONL 文件批量导入
python scripts/community_wiki_ingest.py --community ./my-community --events events.jsonl
```

Event JSON 示例：
```json
{
  "type": "activity",
  "initiator": "alice",
  "co_creators": ["bob"],
  "participants": ["carol", "dave"],
  "metadata": {
    "title": "周末共创会",
    "description": "讨论社区土地神项目架构"
  },
  "artifacts": [
    {
      "type": "link",
      "url": "https://github.com/...",
      "description": "代码仓库"
    }
  ]
}
```

注意：artifacts 支持 `url` 字段，也兼容 `content` 字段（会自动转换）。

### 刷新 Wiki

触发条件：用户要求刷新 Wiki，或在录入 Event 后自动触发。

用户应该明确指出刷新哪个社区的 Wiki，如果没有指定社区，LLM 根据上下文判断应该刷新哪个社区，如果无法判断则进行交互式询问。

计算关系图谱和社区状态，并生成所有 Markdown 页面。刷新后自动 commit，包含状态指标。

```bash
# 一键刷新：计算图谱状态 + 生成所有 Markdown + 自动 commit
python scripts/community_wiki_refresh.py --community ./my-community
```

### 查询与导航

触发条件：用户想了解社区状态、个人档案、关系网络，或获取推荐连接。

示例：
- "查看 SeeDAO 社区当前的状态"
- "查看白鱼的档案"
- "查看关系网络"
- "我是 David，给我推荐一些连接"

用户应该明确指出查询哪个社区的 Wiki，如果没有指定社区，LLM 根据上下文判断应该查询哪个社区，如果无法判断则进行交互式询问。

```bash
# 查询社区状态
python scripts/community_wiki_query.py --community ./my-community --query state

# 查询个人档案
python scripts/community_wiki_query.py --community ./my-community --query person --id alice

# 查询关系网络
python scripts/community_wiki_query.py --community ./my-community --query graph

# 推荐连接
python scripts/community_wiki_query.py --community ./my-community --query recommend --for david
```

### 数据审计

触发条件：用户要求检查数据一致性，或提及数据有问题。

检查以下内容：
- JSON 与 Markdown 指标是否一致
- 成员档案是否完整（profile.name, profile.bio, skills, interests）
- 社区信息是否完整
- 链接是否正确
- 日期显示是否正确

数据审计为只读操作，过程中不要修改任何数据。

发现问题时报告给用户，并建议修正方式。

### 提取 Event（从链接）

触发条件：用户提供一个链接（微信公众号文章、活动页面、社交帖子等），要求提取 Event 信息。

**步骤：**

1. **获取内容** — 使用 extract 脚本下载 URL 内容并保存到社区目录的 `asset/` 下：
   ```bash
   python scripts/community_wiki_extract.py --community ./my-community --url "https://..."
   ```

2. **分析提取** — LLM 阅读保存的内容，从中提取 Event 结构化信息：
   - 识别活动/项目标题和描述
   - 识别发起人（initiator）、协作者（co_creators）、参与者（participants）
   - 识别时间、地点
   - 识别协作产出（artifacts）

3. **确认录入** — 将提取的 Event 信息展示给用户确认，补充缺失字段后录入：
   ```bash
   python scripts/community_wiki_ingest.py --community ./my-community --event-file temp_event.json
   ```

**示例**：用户提供一篇社区活动回顾文章链接，提取脚本从文章中识别出参与者、活动时间、产出等信息，结构化为 Event JSON 供用户确认后录入。

如果链接内容无法获取或无法有效提取，告知用户原因并建议手动提供 Event 信息。

## 脚本工具

| 脚本 | 功能 | Git 操作 |
|------|------|---------|
| `community_wiki_init.py` | 初始化社区目录结构 | `git init` + 首次 commit |
| `community_wiki_ingest.py` | 导入 Event 数据，自动更新 Person event_refs | 每条 event 自动 commit |
| `community_wiki_refresh.py` | **核心脚本**：计算图谱状态 + 生成所有 Markdown | 刷新后自动 commit（含状态指标） |
| `community_wiki_query.py` | 查询接口：state / person / graph / recommend | 只读，不操作 Git |
| `community_wiki_extract.py` | 从 URL 获取内容，保存到 asset/，辅助提取 Event 信息 | 新增 asset 文件时 commit |
| `community_wiki_export.py` | 导出：GEXF / Cytoscape / Markdown / CSV | 只读，不操作 Git |

详见各脚本的 `--help` 输出。

### Git 集成说明

**自动追踪**：
- `init.py` 初始化社区时自动运行 `git init`，创建 `.git/` 目录
- `ingest.py` 每次导入 event 后自动 `git add -A && git commit`
- `refresh.py` 刷新后自动 `git add -A && git commit`

**Commit 规范**：
- `init: Community 'xxx' initialized` — 初始化
- `ingest: Add event evt_xxx (activity)` — 导入 event
- `refresh: N events, M people, co_presence=X, emergence=Y, xiaoyao=Z` — 刷新

**手动 Push 到 GitHub**：
```bash
# 配置远程仓库（一次性）
git remote add origin https://github.com/username/community-wiki.git

# 推送
git push -u origin master

# 之后每次更新后
python scripts/community_wiki_refresh.py --community ./my-community
git push
```

## 生成的 Markdown 页面

`community_wiki_refresh.py` 是核心脚本，它将社区数据生成为一组互相关联的 **Markdown 文件**，形成完整的社区知识图谱 Wiki：

- **index.md** — 索引页（总目录，链接到所有页面）
- **community.md** — 社区主页（价值观 + 三指标 + 活跃成员排名）
- **state.md** — 状态历史（时间序列记录，append-only）
- **graph.md** — 关系图谱（所有关系边 + 密度 + 共同 Event）
- **log.md** — 操作日志（社区变更记录）
- **people/*.md** — 个人页（逍遥指数 + Event 记录 + 关系网络）
- **events/*.md** — Event 页（参与者 + 角色 + 协作产出）

### 特性

- **[[wikilinks]] 互相关联**：所有页面通过 `[[page|title]]` 互相链接
- **YAML frontmatter**：每页都有结构化元数据，支持 Obsidian Dataview 查询
- **表格化指标**：社区状态、个人逍遥指数、关系密度全部用表格呈现
- **Obsidian 原生兼容**：直接作为 Obsidian vault 打开，Graph View 可视化关系网络
- **GitHub 友好**：标准 Markdown，GitHub 可渲染
- **纯文本、无数据库**：任何文本编辑器均可阅读和编辑

## 社区状态指标

### 共在 (Co-presence) — 社区是否「连起来了」

```
co_presence = (E / N) + C

E = relationship edges 总数
N = person 数量
C = clustering_factor = number_of_clusters / N
```

### 涌现 (Emergence) — 社区是否「产生了东西」

```
emergence = A / E

A = artifacts 总数（来自 Event.artifacts）
E = events 总数
```

### 逍遥 (Xiaoyao) — 个体能否自由生成关系

个体级：
```
xiaoyao(person) = 0.4 * IR + 0.3 * RE + 0.3 * NR

IR = initiator_events / total_events（发起能力）
RE = entropy(initiator, co_creator, participant)（角色多样性）
NR = new_connections / total_connections（网络扩展）
```

社区级：`community_xiaoyao = average(xiaoyao(person))`

## 关系密度计算

### 单次 Event 贡献值

| 关系类型 | 含义 | 单次贡献 |
|---------|------|---------|
| initiator ↔ co_creator | 共同建构事件结构 | +3.0 |
| co_creator ↔ co_creator | 核心协作执行 | +2.5 |
| initiator ↔ participant | 场域创建 + 进入 | +1.5 |
| co_creator ↔ participant | 局部协作接触 | +1.2 |
| participant ↔ participant | 共在出现 | +1.0 |

### 累积规则

```
density(A, B) = Σ(Event contribution across all shared events)
```

### 关系类型划分

| density 区间 | 类型 |
|-------------|------|
| < 3 | weak |
| 3–10 | normal |
| > 10 | strong |

## 扩展建议

1. **数据源接入**：接入微信群聊、Discord、Notion、GitHub 等，结合其他 SKILL，通过 Webhook 或 API 自动解析为 Event
2. **可视化**：使用 D3.js / Cytoscape.js 渲染 Graph，颜色编码关系密度
3. **Agent 增强**：接入 LLM，实现自然语言查询、智能推荐、社区诊断

## 参考

- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [社区 Wiki 设计文档](./references/DESIGN.md)
