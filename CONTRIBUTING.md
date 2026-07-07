# Contributing · 贡献指南

Thanks for helping build SeeDAO Skills! This guide covers how to add a new skill, update an existing one, and follow the repository conventions.
感谢参与 SeeDAO Skills 的建设！本指南说明如何新增技能、更新现有技能，并遵循仓库约定。

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).
参与即表示你同意遵守我们的[行为准则](CODE_OF_CONDUCT.md)。

[中文](#中文) · [English](#english)

---

## Quick start · 快速开始

This repository is a collection of **Agent Skills**. Each skill lives in its own top-level folder and is described by two files:
本仓库是 **Agent Skill** 的集合。每个技能是一个顶层文件夹，由两个文件描述：

- `SKILL.md` — the instruction consumed by the agent / 供 Agent 读取的指令文件
- `README.md` — human-readable documentation / 面向人类读者的文档

No Node.js build, npm install, or backend setup is required to contribute.
贡献本仓库**不需要** Node.js 构建、npm install 或后端配置。

---

## 中文

### 提交新 Skill 的流程

1. Fork 本仓库，从 `main` 切出分支，例如 `feat/xxx-skill`。
2. 在仓库根目录创建 `{skill-name}/` 文件夹。
3. 编写 `SKILL.md`（供 Agent 使用）和 `README.md`（供人类阅读）。
4. 确认目录结构与元数据符合[下面的约定](#skill-目录结构)。
5. 提交 PR，填写 PR 模板。

### Skill 目录结构

```
{skill-name}/
├── SKILL.md        # 必填。Agent 读取的指令，含 YAML frontmatter
├── README.md       # 必填。面向使用者的说明文档
├── references/     # 可选。设计文档、参考材料
└── scripts/        # 可选。脚本、示例数据、辅助工具
```

### SKILL.md 格式

`SKILL.md` 必须包含 YAML frontmatter 和 Markdown 正文。推荐字段如下：

```yaml
---
name: skill-name                   # 必填。skill 的唯一标识，建议与文件夹同名
description: "一句话描述触发场景和作用" # 必填。Agent 靠它判断是否调用本 skill
version: 1.0.0                     # 可选。语义化版本
author: Your Name                  # 可选
license: MIT                       # 可选，但建议与仓库 LICENSE 保持一致
metadata:
  hermes:
    tags: [tag1, tag2]             # 可选。搜索/分类标签
    category: category-name        # 可选。所属分类
    related_skills: [other-skill]  # 可选。相关 skill
---
```

正文要求：
- 明确说明**触发条件**（什么场景下 Agent 应该使用本 skill）。
- 说明**输入**和**输出**。
- 给出清晰、可执行的步骤或命令示例。
- 如果包含脚本，说明安装和运行方式。
- 优先使用中文撰写，面向华人社区；如同时面向国际用户，可保留英文版本。

### README.md 格式

README.md 应面向人类使用者，包含：
- 技能一句话介绍
- 快速开始 / 安装步骤
- 使用示例
- 目录结构说明（如有脚本或数据）
- 依赖与前置条件
- 协议与许可证

### 必须遵守的项目约定

1. **每个 skill 一个顶层文件夹。** 不要在根目录直接放代码或脚本。
2. **`SKILL.md` 是 Agent 的唯一真源。** 行为描述、触发条件、命令示例都应放在 `SKILL.md`，不要把关键约定只写在 `README.md`。
3. **脚本放在 `scripts/` 下。** 使用相对路径引用，避免硬编码用户环境路径。
4. **数据/示例放在 `demo-*/` 或 `references/` 下。** 不要把大文件直接放在根目录。
5. **LICENSE 保持一致。** 若无特殊说明，采用仓库根目录 `LICENSE`（MIT）。

### 代码与文档风格

- 脚本优先使用 Python 或 Bash；如需其他语言，请在 README 中说明安装方式。
- 保持 Markdown 简洁、可执行命令可复制粘贴。
- 命令示例中的占位符使用清晰标识，如 `--community ./my-community`。
- 注释解释**为什么**，与现有文件风格保持一致。

### 提交与 PR

- 从 `main` 切分支（如 `feat/...`、`fix/...`）。
- 建议用约定式提交（Conventional Commits）：`feat:`、`fix:`、`docs:`、`refactor:`、`chore:`。
- 一个 PR 只做一件事：新增一个 skill、修复一个 skill 或改进文档。
- 填写 PR 模板，说明改动动机、受影响的 skill 和测试方式。
- 如新增或修改了 skill，建议在实际 Agent 中验证触发条件与执行步骤。

---

## English

### How to add a new Skill

1. Fork the repo and branch from `main`, e.g. `feat/xxx-skill`.
2. Create a top-level folder named `{skill-name}/`.
3. Write `SKILL.md` (for the agent) and `README.md` (for humans).
4. Make sure the folder structure and metadata follow the [conventions below](#skill-directory-structure).
5. Open a PR and fill in the PR template.

### Skill directory structure

```
{skill-name}/
├── SKILL.md        # Required. Agent-facing instructions with YAML frontmatter
├── README.md       # Required. Human-facing documentation
├── references/     # Optional. Design docs, reference materials
└── scripts/        # Optional. Scripts, sample data, helpers
```

### SKILL.md format

`SKILL.md` must contain YAML frontmatter followed by Markdown body. Recommended fields:

```yaml
---
name: skill-name                   # Required. Unique identifier, usually matches folder name
description: "One-sentence summary of when/why to use this skill" # Required. Agent uses this to decide invocation
version: 1.0.0                     # Optional. SemVer
author: Your Name                  # Optional
license: MIT                       # Optional, but should match repo LICENSE
metadata:
  hermes:
    tags: [tag1, tag2]             # Optional. Search / classification tags
    category: category-name        # Optional. Category this skill belongs to
    related_skills: [other-skill]  # Optional. Related skills
---
```

Body requirements:
- Clearly state the **trigger conditions** (when the agent should use this skill).
- Describe **inputs** and **outputs**.
- Provide clear, executable steps or command examples.
- If scripts are included, explain installation and how to run them.
- Prefer Chinese as the primary language for this community; include English if the skill targets international users too.

### README.md format

README.md should be human-readable and contain:
- One-sentence description of the skill
- Quick start / installation steps
- Usage examples
- Directory structure explanation (if scripts or data are present)
- Dependencies and prerequisites
- License

### Conventions you must follow

1. **One skill per top-level folder.** Do not put code or scripts directly in the repo root.
2. **`SKILL.md` is the single source of truth for the agent.** Behaviors, triggers, and command examples go there; do not leave critical instructions only in `README.md`.
3. **Scripts go under `scripts/`.** Use relative paths and avoid hard-coding user-specific paths.
4. **Data / examples go under `demo-*/` or `references/`.** Do not place large files directly in the root.
5. **Keep licensing consistent.** Unless stated otherwise, use the same license as the repo root `LICENSE` (MIT).

### Code and documentation style

- Prefer Python or Bash for scripts. If you use another language, document the installation steps in README.
- Keep Markdown simple and commands copy-pasteable.
- Use clear placeholders in examples, e.g. `--community ./my-community`.
- Comments explain **why**; match the density and voice of the surrounding file.

### Commits & PRs

- Branch from `main` (e.g. `feat/...`, `fix/...`).
- Conventional Commits are encouraged: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- Keep each PR focused on one thing: one new skill, one fix, or one documentation improvement.
- Fill in the PR template; explain the motivation, affected skills, and how you tested it.
- If you add or modify a skill, verify the trigger conditions and execution steps in an actual agent when possible.

---

## Reporting issues · 报告问题

Use the issue templates under [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE).
For security vulnerabilities, please **do not** open a public issue — contact a maintainer privately. 报告安全漏洞请勿公开提 issue，请私下联系维护者。
