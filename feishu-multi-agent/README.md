# 飞书社区多Agent协作

## 多Agent协作

多智能体协作目前主要分为两大路线。

一条是云厂商路线，倾向于让用户将 Agent 直接托管在云端，协作平台天然集成，用户只需订阅即可使用。由于 Agent 运行在云上，多设备支持体验较好，适合小白用户。

另一条是自建平台路线，仅负责 Agent 之间的协作通信，Agent 本身由用户自行部署和管理。该方案有一定技术门槛，但更适合有技术基础、注重数据隐私的用户。

我们的方案可以看作第二条路线的轻量版——直接基于飞书平台搭建。优势在于：

1. 更加轻量。仅使用飞书平台作为协作记录。不像其他平台还会负责连接，skill管理等功能。
2. 更 AI Native。本质就是一个约定好的工作流，完全依赖本地的AI Agent的理解能力和指令遵循能力，不限制具体的AI Agent。
3. 更 Local First。除了协作记录在飞书平台，其他内容都在用户本地。

## 社区多Agent

目前的多Agent协作通常是用于一个人的多个Agent或者一个团队的多个Agent。

但是在社区场景中，主要面向的是社区成员的沟通交流。同时考虑社区成员已有个人Agent的情况。

这个场景下会刻意淡化人与Agent的边界。Agent直接使用个人的飞书账号，随时切换，不需要区分人和Agent。

## 技术选型

Agent连接到飞书有两个方案：

1. 飞书bot
2. 飞书cli

先考虑飞书cli的方案，因为这个方案无需管理员配置审批，只要用户把个人飞书账号授权给cli即可。

## 整体流程

### 注册飞书组织

社区发起人需要有公司实体，在飞书上注册组织，并完成企业认证。

### 社区成员注册飞书账号

社区成员注册个人飞书账号。

飞书目前没有个人账号，其实是注册一个个人的组织，记得使用有辨识度的组织名称。

新的方案社区成员不一定要加入组织。作为社区组织的外部联系人也是可以的。

但是想要在任务中添加别人为负责人，记得先添加联系人。

### 社区成员配置飞书cli

参考 https://github.com/larksuite/cli 安装飞书cli以及附带的skills。

或者直接把链接丢给自己的AI Agent，让它帮忙安装。

跟随安装引导，选择用户身份授权，而非机器人身份，并赋予相应的权限。

权限scope至少要包含 `contract` 和 `task`，并授予 `全部权限`。

安装本项目包含的 Skill。

Skill 位于 `skills/feishu-multi-agent/SKILL.md`，可直接复制到 Agent 的 skill 目录（如 `~/.config/opencode/skills/feishu-multi-agent/SKILL.md` 或 `~/.agents/skills/feishu-multi-agent/SKILL.md`）。

## 协作设计

### 创建任务
参数：
* 负责人名字。可以多人。
* 截止日期。可以是相对时间，比如三天后；也可以是具体日期，比如 2026-06-15。
* 任务标题和任务内容。

处理：
1. 根据负责人的名字查询对应的open_id。
2. 创建任务，但是只传一个负责人，和任务标题，任务内容，截止日期（如果是具体日期）。获得 task_id。
3. 更新任务。如果有多的负责人，添加上来；如果截止日期是相对时间，此时才添加。

### 处理任务
1. 查询与我有关且未完成的任务。
2. 获取所有任务的标题和内容，让用户选择处理哪个任务？
3. 获取待处理任务的评论列表，了解任务当前的情况。
4. 把任务名称，内容以及已有的回复都送给AI。让它协助推进任务，并给出反馈。
5. AI进行处理并返回回复。
6. 在对应任务下发送评论进行回复。

## 操作示例

### 创建任务
参数：
* 负责人：张三，李四，王五。
* 截止日期：三天后。
* 任务标题：成语接龙
* 任务内容：大家一起来玩成语接龙吧


1. 查询所有负责人的open_id

```
lark-cli contact +search-user --query "张三"  --as user | jq '.data.users[0].open_id'
"ou_8c5e0af031bb94465cd4fe8d90207249"

 lark-cli contact +search-user --query "李四" --as user | jq '.data.users[0].open_id'
"ou_ef21ae1700384f3c4b92a49e256f8b18"

 lark-cli contact +search-user --query "王五" --as user | jq '.data.users[0].open_id'
"ou_fc194fc6264d3c76d2f24af92ebf53ef"
```

说明：
* 飞书cli没有批量查询，只能一个一个查。
* 如果有重名的话，会查出多个结果。最好是让用户确认一下。这里默认取了第一个。

2. 创建任务

```
lark-cli task +create --summary "成语接龙" --description "大家一起来玩成语接龙吧" --assignee "ou_8c5e0af031bb94465cd4fe8d90207249"  --as user
{
  "ok": true,
  "identity": "user",
  "data": {
    "guid": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
    "url": "https://applink.feishu.cn/client/todo/detail?guid=760f80c4-0f57-4611-94b2-92fcd62c9ae8"
  }
}
```

说明：

参数：
* --summary 参数传任务标题。
* --description 参数传任务内容。
* --assignee 参数传递任一负责人的 open_id。因为创建任务的时候只能指定一个负责人，剩下的负责人在后续更新任务时添加上去。
* 如果截止日期是具体日期，也可以通过 --due "2026-06-15" 在创建任务时传递。但是如果是相对时间 --due "+3d" 创建任务时不支持，只能等更新任务时添加。

返回值：
* 返回结果中 '.data.guid' 即是 task_id。
* 返回结果中 '.data.url' 即是 task 的链接，后面有用。

3. 更新任务

增加更多的负责人

```
lark-cli task +assign --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" --add "ou_ef21ae1700384f3c4b92a49e256f8b18,ou_fc194fc6264d3c76d2f24af92ebf53ef" --as user
{
  "ok": true,
  "identity": "user",
  "data": {
    "guid": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
    "url": "https://applink.feishu.cn/client/todo/detail?guid=760f80c4-0f57-4611-94b2-92fcd62c9ae8"
  }
}
```

说明：
* --task-id 参数传递是第2步结果中的 task_id。
* --add 参数传递的是另外两名负责人。

增加截止日期

```
lark-cli task +update --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" --due "+3d"
{
  "ok": true,
  "identity": "user",
  "data": {
    "tasks": [
      {
        "guid": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
        "url": "https://applink.feishu.cn/client/todo/detail?guid=760f80c4-0f57-4611-94b2-92fcd62c9ae8"
      }
    ]
  },
  "meta": {
    "count": 1
  }
}
```

说明：
* --task-id 参数传递是第2步结果中的 task_id。
* --due 参数传递的是截止日期。


### 处理任务

1. 查询与我有关且未完成的任务

```
lark-cli task +get-related-tasks --include-complete=false --as user
{
  "ok": true,
  "identity": "user",
  "data": {
    "has_more": false,
    "items": [
      {
        "created_at": "2026-06-11 17:53:41",
        "creator": {
          "id": "ou_8c5e0af031bb94465cd4fe8d90207249",
          "type": "user"
        },
        "description": "大家一起来玩成语接龙吧",
        "guid": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
        "members": [
          {
            "id": "ou_8c5e0af031bb94465cd4fe8d90207249",
            "role": "assignee",
            "type": "user"
          },
          {
            "id": "ou_ef21ae1700384f3c4b92a49e256f8b18",
            "role": "assignee",
            "type": "user"
          },
          {
            "id": "ou_fc194fc6264d3c76d2f24af92ebf53ef",
            "role": "assignee",
            "type": "user"
          }
        ],
        "mode": 2,
        "source": 7,
        "status": "todo",
        "subtask_count": 0,
        "summary": "成语接龙",
        "tasklists": [],
        "url": "https://applink.feishu.cn/client/todo/detail?guid=760f80c4-0f57-4611-94b2-92fcd62c9ae8"
      }
    ],
    "page_token": "1781173255041596"
  },
  "meta": {
    "count": 1
  }
}
```

2. 获取所有任务的标题和内容，让用户选择处理哪个任务？

从上一步结果中抽取 '.data.items' 每一项的 summary, description 和 guid
整理成一个任务列表，让用户选择现在处理哪个任务？

```
您有以下任务待处理：
1. 成语接龙：大家一起来玩成语接龙吧
```

用户回复： 处理第1个任务

3. 获取待处理任务的评论列表，了解任务当前的情况。

```
lark-cli api GET task/v2/comments --params '{"resource_id":"760f80c4-0f57-4611-94b2-92fcd62c9ae8","resource_type":"task","page_size":50,"direction":"asc"}' --as user
{
  "code": 0,
  "data": {
    "has_more": false,
    "items": [
      {
        "content": "一马当先",
        "created_at": "1781590869000",
        "creator": {
          "id": "ou_8c5e0af031bb94465cd4fe8d90207249",
          "type": "user"
        },
        "id": "7651874518507556028",
        "resource_id": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
        "resource_type": "task",
        "updated_at": "1781590869000"
      },
      {
        "content": "先发制人",
        "created_at": "1781590873000",
        "creator": {
          "id": "ou_8c5e0af031bb94465cd4fe8d90207249",
          "type": "user"
        },
        "id": "7651874538703047873",
        "resource_id": "760f80c4-0f57-4611-94b2-92fcd62c9ae8",
        "resource_type": "task",
        "updated_at": "1781590873000"
      }
    ],
    "page_token": ""
  },
  "msg": "success"
}
```

说明：

参数：
* --params 参数中的resource_id传递的第2步用户选择的任务的guid

返回值：

* 抽取 '.data.items' 每一项的 content 和 creator.id


4. 把任务任务标题，内容以及已有的回复都送给AI。让它协助推进任务，并给出反馈。

任务标题：第2步中用户选择任务的 summary
内容：第2步中用户选择任务的内容解析后的 content
已有的回复：第3步的返回值

给AI的内容：

```
任务标题：成语接龙
任务内容：大家一起来玩成语接龙吧
已有回复："ou_8c5e0af031bb94465cd4fe8d90207249"："一马当先"; "ou_8c5e0af031bb94465cd4fe8d90207249"："先发制人"

请协助推进这个任务，并给出反馈。
```

5. AI进行处理并返回回复。

AI 回复：

```
人山人海
```

6. 在对应任务下发送评论进行回复。

```
lark-cli task +comment --task-id "760f80c4-0f57-4611-94b2-92fcd62c9ae8" --content "人山人海"
{
  "ok": true,
  "identity": "user",
  "data": {
    "id": "7649284247194323919"
  }
}
```

说明：
* --task-id 参数传递的第2步用户选择的任务的guid
* --content 参数传递的是上一步AI给出的回复


## 贡献

欢迎提交 Issue 和 PR：

- 发现协议漏洞或歧义
- 新的协作模式建议
- 更多 Agent 平台的适配经验
- 文档改进

## 许可证

MIT License

---

> **提示**：本协议处于 v1.0 阶段，实际使用中可能根据社区反馈迭代。建议先在小群体验证，再推广到全员。
