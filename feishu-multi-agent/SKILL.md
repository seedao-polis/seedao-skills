---
name: feishu-community-multi-agent
description: Use when 社区成员需要通过 lark-cli 基于飞书任务进行轻量多 Agent 协作，创建任务或处理未完成任务，且成员可以作为组织外部联系人参与。
---

# 飞书社区多 Agent 协作

## 概述

基于飞书 CLI 的轻量多 Agent 协作方案。社区成员以个人飞书账号授权 `lark-cli`，通过飞书任务（Task）完成创建、分发、回复和跟踪。协作记录保存在飞书任务及其评论中，不依赖话题群或通知群。

## 何时使用

- 需要在社区场景下让多个本地 Agent 协作
- 希望通过飞书任务+评论实现 Agent 间通信
- 社区成员可能未加入同一飞书组织，可作为外部联系人参与
- 已安装 `lark-cli` 并完成个人身份授权

## 前置条件

1. 社区发起人注册飞书组织并完成企业认证。
2. 社区成员注册个人飞书账号（可加入组织，也可作为外部联系人）。
3. 本地安装 `lark-cli`（参考 https://github.com/larksuite/cli）。
4. 授权 scope 至少包含 `contact`、`task`，并授予全部权限。

## 创建任务

### 输入

- 负责人名字（可多人）
- 截止日期（相对时间如 `+3d`，或具体日期如 `2026-06-15`）
- 任务标题和任务内容

### 流程

1. **搜索负责人 open_id**

   对每个负责人名字执行：

   ```bash
   lark-cli contact +search-user --query "张三" --as user | jq '.data.users[0].open_id'
   ```

   说明：
   - 默认同时搜索内部成员和外部联系人。
   - 若确定只搜组织内成员，可加上 `--exclude-external-users`。
   - 没有批量查询，需逐个搜索。
   - 如果有重名的话，会查出多个结果。最好是让用户确认一下。示例里是默认取了第一个。

2. **创建任务**

   ```bash
   lark-cli task +create \
     --summary "成语接龙" \
     --description "大家一起来玩成语接龙吧" \
     --assignee "ou_8c5e0af031bb94465cd4fe8d90207249" \
     --due "2026-06-15" \
     --as user
   ```

   说明：
   - `--summary` 传任务标题。
   - `--description` 传任务内容。
   - `--assignee` 只能指定一个负责人，剩余负责人在下一步添加。
   - 若截止日期是相对时间（如 `+3d`），创建时不能传，需在下一步更新。
   - 返回 `.data.guid` 即 `task_id`，`.data.url` 即任务链接。

3. **更新任务**

   添加其余负责人：

   ```bash
   lark-cli task +assign \
     --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" \
     --add "ou_ef21ae1700384f3c4b92a49e256f8b18,ou_fc194fc6264d3c76d2f24af92ebf53ef" \
     --as user
   ```

   添加截止日期（如果是相对时间）：

   ```bash
   lark-cli task +update \
     --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" \
     --due "+3d" \
     --as user
   ```

## 处理任务

### 流程

1. **查询与我有关且未完成的任务**

   ```bash
   lark-cli task +get-related-tasks --include-complete=false --as user
   ```

   从结果中抽取 `.data.items` 每项的 `summary`、`description`、`guid`，整理成列表让用户选择。

2. **获取任务评论**

   ```bash
   lark-cli api GET task/v2/comments \
     --params '{"resource_id":"760f80c4-0f57-4611-94b2-92fcd62c9ae8","resource_type":"task","page_size":50,"direction":"asc"}' \
     --as user
   ```

   从 `.data.items` 抽取每项的 `content` 和 `creator.id`。

3. **交给 AI 生成回复**

   将任务标题、内容、已有回复组装后交给 AI：

   ```
   任务标题：成语接龙
   任务内容：大家一起来玩成语接龙吧
   已有回复："ou_8c5e0af031bb94465cd4fe8d90207249"："一马当先"; "ou_ef21ae1700384f3c4b92a49e256f8b18"："先发制人"

   请协助推进这个任务，并给出反馈。
   ```

4. **在任务下发表评论**

   ```bash
   lark-cli task +comment \
     --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" \
     --content "人山人海" \
     --as user
   ```

## 命令速查

| 目的 | 命令 |
|---|---|
| 搜索用户 open_id | `lark-cli contact +search-user --query "名字" --as user |
| 创建任务 | `lark-cli task +create --summary "标题" --description "内容" --assignee "ou_xxx" --as user` |
| 添加负责人 | `lark-cli task +assign --task-id "guid" --add "ou_xxx,ou_yyy" --as user` |
| 设置截止日期 | `lark-cli task +update --task-id "guid" --due "+3d" --as user` |
| 列出未完成任务 | `lark-cli task +get-related-tasks --include-complete=false --as user` |
| 获取任务评论 | `lark-cli api GET task/v2/comments --params '{"resource_id":"guid","resource_type":"task","page_size":50,"direction":"asc"}' --as user` |
| 发表评论 | `lark-cli task +comment --task-id "guid" --content "回复内容" --as user` |

## 常见错误

| 现象 | 可能原因 | 解决 |
|---|---|---|
| 找不到用户 | 名字拼写错误，或搜索范围排除了外部联系人 | 核对名字；移除 `--exclude-external-users` |
| 创建任务失败 | 未授权 `task` scope | 重新授权 `lark-cli`，确保包含 `task` 全部权限 |
| 无法添加多个负责人 | 创建时传了多个 `--assignee` | 创建时只传一个，其余用 `task +assign --add` |
| 相对截止日期未生效 | 创建时直接传了 `+3d` | 创建时不支持相对时间，创建后用 `task +update --due` |
| 获取评论失败 | `resource_id` 或 `resource_type` 错误 | `resource_id` 为任务 `guid`，`resource_type` 固定为 `task` |
| 发表评论失败 | `task-id` 不是有效 guid | 使用创建任务返回的 `.data.guid` |

## 权限要求

`lark-cli` 授权时至少勾选：

- `contact`（查询用户 open_id）
- `task`（创建、更新、查询任务及评论）

并授予这些 scope 的**全部权限**。

## 协议版本

v1.0。建议先在小群体验证，再推广到全员。
