# Community LLM Wiki Structure

## 目录结构（Obsidian Vault 兼容）

```
my-community/
├── .obsidian/              # Obsidian 配置（可选）
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
    ├── state.json
    └── graph.json
```

## 设计原则

1. **所有人类可读内容都是 Markdown** — 直接放入 Obsidian
2. **_data/ 目录存放机器生成的 JSON** — 脚本读取，人类通常不直接编辑
3. **Markdown 文件由脚本自动生成/刷新** — 保持与 _data/ 同步
4. **[[wikilinks]] 互相关联** — Obsidian Graph View 可视化
5. **YAML frontmatter** — 支持 Dataview 查询
6. **log.md append-only** — 记录所有变更
7. **Git 自动追踪** — 每次操作自动 commit，保留完整历史


## 刷新机制

当录入新 Event 后：
1. 更新 _data/ 中的 JSON
2. 重新计算 state.json + graph.json
3. 重新生成所有 Markdown 页面
4. 追加 log.md

## 与 llm-wiki 的关系

| 维度 | llm-wiki | community-llm-wiki |
|------|----------|-------------------|
| 核心单元 | Source（信息源） | Event（协作行动） |
| 页面类型 | entities / concepts / comparisons | people / events / graph |
| 连接逻辑 | 语义关联 | 关系（协作事实） |
| 时间性 | 静态积累 | Event 驱动，持续刷新 |
| 主体 | 知识（客观） | 人（在关系中生成） |
| 产出 | 理解、洞察 | 作品、项目、关系网络 |
| 哲学 | 认知论 | 存在论（因作而是） |
| 结构约束 | 较少 | 强（Event → Relationship → State） |
| 计算数据 | 无 | 有（密度、三指标） |
