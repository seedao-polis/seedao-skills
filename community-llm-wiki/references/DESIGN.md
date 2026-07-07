# Community LLM Wiki 设计文档

一种使用 LLM 构建社区Wiki的模式。

这是一种社区治理模式，具体形式为 AI Agent 使用的 SKILL。

本文档只是这种模式的阐述，具体的SKILL的细节可以根据实际情况进行详细设计。

与 [Karpathy 的 LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 非常类似，但是面向社区场景。

## 核心思想

基于「共在 / 涌现 / 逍遥 / 因作而是」的个人和社区世界观。

以 Event 为唯一事实源，通过关系网络（Graph）呈现社区网络结构。

### 共在（Relation-first）
社区的基础不是个体，而是关系
- 人在关系中被定义
- 社区是关系网络，而非简单的人的集合

### 涌现（Emergence）
社区的价值来自协作，而非预设的目标
- 作品 / 项目 / 内容来自关系互动
- 系统不预设结果，只记录生成

### 逍遥（Structural Freedom）
个体在网络中具备自由生成关系与切换角色的能力

角色通常有：
- 发起人(initiator)
- 协作者(co_creator)
- 参与者（participant）

### 因作而是（Becoming-through-Action）
人不是身份，而是在持续行动（Event）中被生成的结构
- Event 先于身份
- 做什么，成为什么

## 与传统社区治理的差异

传统社区治理中，社区信息完全由主理人以及其团队进行发起，搜集和编辑整理。

比如，发起活动，进行一些项目，组织讨论，交流等等。

这种做法有以下缺点：
1. 活动发起比较中心化，效率比较低，无法激发大家的积极性。
2. 信息碎片化，搜集困难。
3. 编辑整理工作繁重，需要庞大的编辑团队，又造成信息同步的难题。
4. 信息结构易变，时间长了之后会产生信息腐坏。

新的方案：
1. 活动发起更去中心化，可以更轻量。比如几个人一起随性的讨论也可以算是活动。
2. 简化为只需要搜集事件（Event）信息，提升搜集的效率。
3. 信息搜集可以由社区成员一起贡献，也是一种社区共建活动。
4. AI Agent 相当于一个时刻在线的编辑团队，且没有信息同步的问题。
5. 借助 LLM 的语言理解和推理能力，它并不是机械的进行编辑和整理，它会真正的理解Wiki中的内容，逐步构建并维护一个持久化的 Wiki。
6. 扩展能力强，可以持续演进。

## 架构

有三层：

1. 事件来源。可能是一场活动，可能是一个项目，也可以是几个人简单的讨论，甚至是群聊里就一个话题产生的讨论。这些是社区所有信息的来源。

2. 社区状态。LLM 从事件信息中解析出参与活动的人，从而构建人与人之间的关系。进而在原有的社区状态上进行增量更新，刷新整个社区的图谱和一些状态指标。

3. Wiki。我们并没有把整个系统设计成一个数据库，而是由记录数据信息的json文件和展示社区状态的Markdown文件构成。因为我们希望整个系统是足够灵活，又是人类可读的。Wiki是Obsidian Vault 兼容的，可以很方便的进行图形化展示。


## 操作流程

```
输入（聊天记录/会议纪要/活动信息/社交媒体信息等）
    ↓
Event Parser  （数据清洗，解析，审查）
    ↓
Event  （结构化数据）
    ↓
Person + Relationship （由Event计算得到）
    ↓
Graph + State    （增量更新状态）
    ↓
Agent            （构建并维护）
    ↓
Text + Links      （Wiki格式） 
    ↓
用户
    ↓
Event（循环）
```

## 核心数据结构

### 本体层（Ontology）

只有三类实体：Community / Person / Event

- Community → 意义容器
- Person → 节点
- Event → 关系发生器

```
Community {
  // =========================
  // 基础信息
  // =========================
  id:string
  name:string
  logo?:string
  description?:string
  // =========================
  // 价值与文化（静态）
  // =========================
  values:string[]// e.g. 共在 / 涌现 / 逍遥
  manifesto?:string
  tags?:string[]
  // =========================
  // 组织结构（静态）
  // =========================
  founders:string[]// 主理人
  admins?:string[]
  // =========================
  // 资源信息（静态）
  // =========================
  treasury?: {
    currency?:string
    balance?:number
    policy?:string
  }
  // =========================
  // 外部入口
  // =========================
  links?: {
    website?:string
    docs?:string
    chat?:string
  }
  // =========================
  // 时间信息
  // =========================
  created_at:number
}

Person{
  // =========================
  // 基础身份
  // =========================
  id:string
  profile: {
    name?:string
    avatar?:string
    bio?:string
    location?:string
  }
  // =========================
  // 显式输入信息
  // =========================
  skills:string[]
  interests:string[]
  links: {
    github?:string
    twitter?:string
    website?:string
  }
  works_input: {
    title:string
    description?:string
    link?:string
  }[]
  // =========================
  // 参与事实（引用 Event，不存 Event 本体）
  // =========================
  event_refs: {
    event_id:string
    role:"initiator"|"co_creator"|"participant"
    type:"activity"|"project"
    timestamp:number
  }[]
  // =========================
  // 外部输入记录（非结构化）
  // =========================
  external_inputs?: {
    source:"h5"|"external_tool"|"manual"
    content:any
    timestamp:number
  }[]
}

Event{
  // =========================
  // 基础标识
  // =========================
  id:string
  timestamp:number
  type:"activity"|"project"
  // =========================
  // 语义信息（展示用）
  // =========================
  metadata?: {
    title?:string
    description?:string
  }
  // =========================
  // 核心协作结构（网络生成核心）
  // =========================
  initiator:string
  co_creators:string[]
  participants:string[]
  // =========================
  // 内部系统引用（可选）
  // =========================
  target_id?:string
  // =========================
  // 外部来源（开放系统）
  // =========================
  external?: {
    source_name?:string
    url?:string
    poster_url?:string
  }
  // =========================
  // 关系历史记录（协作产出）
  // =========================
  Artifact: {
    type:"photo"|"video"|"doc"|"report"|"link"
    url:string
    created_by?:string
    related_persons?:string[]
    timestamp?:number
  }[]
  // =========================
  // 数据来源
  // =========================
  source: {
    type:"h5"|"external"|"api"|"manual"
    tool_name?:string
  }
}
```

### 非本体层（非常重要）

以下全部不属于本体层，从本体层数据计算出来的：
- Relationship
- Graph
- State
- reputation
- cohesion

## 关系密度计算

| 关系类型 | 含义 | 单次 Event 贡献 |
|---------|------|----------------|
| initiator ↔ co_creator | 共同建构事件结构 | +3.0 |
| co_creator ↔ co_creator | 核心协作执行 | +2.5 |
| initiator ↔ participant | 场域创建 + 进入 | +1.5 |
| co_creator ↔ participant | 局部协作接触 | +1.2 |
| participant ↔ participant | 共在出现 | +1.0 |

累积规则：`density(A,B) = Σ(Event contribution)`

关系类型划分：
- < 3: weak
- 3–10: normal
- > 10: strong

## 社区状态指标

### 共在（Co-presence）

含义：社区中的人是否开始连接形成网络（只看结构连接，不看内容）？

```
co_presence = (E / N) + C

E = relationship edges 总数
N = person 数量
C = clustering_factor = number_of_clusters / N
```

### 涌现（Emergence）

含义：社区的生产率指标，关系到产出的转化率。

```
emergence = A / E
A = artifacts 数量
E = events 总数
```

### 逍遥（Xiaoyao）

含义：社区的结构自主性，即成员在网络中是否能自由的产生新的连接。

个体计算公式：
```
xiaoyao(person) = 0.4 * IR + 0.3 * RE + 0.3 * NR
IR = initiator_events / total_events
RE = entropy(initiator, co_creator, participant)
NR = new_connections / total_connections
```

社区计算公式：`community_xiaoyao = average(xiaoyao(person))`

## Wiki 结构

参见 [结构文档](./STRUCTURE.md)

## Agent

定位：Community LLM Wiki 的运行时。类比 AI Agent 是操作系统，SKILL是系统上的应用。

功能：
1. 录入信息时，对用户录入信息进行理解和推理。尝试理解用户录入的信息，有缺失时提醒用户完善。
2. 查询时，对用户的查询指令进行理解和推理。从Wiki中准确获取用户想要的信息，并给出一些推荐。
3. 日常维护，通过对整个Wiki的理解和推理，能主动发现当前wiki的问题，比如信息缺失，不同地方的内容有矛盾。

技术选型：只要支持SKILL就可以，用户可以结合其他方面的需求进行技术选型。

## 定位

- 不是社交媒体，活动系统、CRM、AI 运营工具
- 不运营社区
- 不决策
- 不控制系统
