## Context

见 `proposal.md` 的 Why。govee 在 `engines/ae_harness/agents/models.py` 里用 `OpenAIChatModel`，没有传入 formatter，因此使用 AgentScope 2.0.9 默认的 `OpenAIChatFormatter`。该格式化器给每条消息都写 `name`。

## Goals / Non-Goals

**Goals:**

- 只在 govee 通道去掉非 user、非 tool 消息的 `name` 键。
- 不改 AgentScope 安装包，不按模型名维护名单。

**Non-Goals:**

- 不改 SOP 流程、提示词文件、运营配置表。
- 不改 `provider=deepseek` 现用的 `DeepSeekMultiAgentFormatter`。
- 不把 `name` 改成空字符串；空字符串仍是该字段存在。

## Decisions

1. 在 `models.py` 增加一个只做后处理的格式化器，继承 `OpenAIChatFormatter`。`format` 先调用父类，再删除 `role` 不是 `user` 且不是 `tool` 的消息上的 `name` 键。
   - 备选：按 `model_name` 是否以 `grok` 开头分支。否决，因为 govee 上的新模型名无法预先穷举，而 DeepSeek 走这条通道时也不依赖该字段。
   - 备选：改 Agent 的 `name`。否决，因为系统消息的 `name` 是框架写入的 `"system"`，与角色名无关。

2. 只在 `provider=govee` 的 `OpenAIChatModel(...)` 传入这个格式化器。其它厂商分支不动。

3. 测试用假消息调用格式化器，断言键是否存在。不访问网关，不读取密钥。

## 模块防火墙自检

- 改动只在 `engines/ae_harness/agents/models.py` 与对应单测。
- 不新增跨 App import，不写库，不改 API 契约。

## Risks / Trade-offs

- [多助手对话丢掉 assistant 名字] → 当前助手对话是单角色；需要区分多个 assistant 时再单独设计，不在本次用 `name` 字段表达。
- [网关以后开始要求 assistant.name] → 回退就是去掉这个格式化器，恢复默认 `OpenAIChatFormatter`。
