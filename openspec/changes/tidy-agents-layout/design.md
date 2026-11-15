## Context

见 `proposal.md` 的 Why。现状是：`config.py` 已是 YAML 与密钥的唯一读取口，但 `role_sys_prompts.py`、`log_keywords.py`、`tools_config.py` 仍自己打开 `config/data` 下的文件。根上另有 `case_roles.py`、`event_log.py`、`event_sink.py`、`realtime_vocie_agent.py`。生产角色创建已走 `assistant.create_chat_agent`，`role_loader.py` 只服务测试与兼容工厂。

## Goals / Non-Goals

**Goals:**

- 配置文件只由 `config.py` 打开。
- 散文件回到已有包，旧导入路径继续可用。
- `agent_builders.py` 继续留在根上，作为 workflow 唯一工厂。

**Non-Goals:**

- 不删除 `role_loader.py`，不合并两套角色装载。
- 不改 `realtime_vocie` 拼写，不拆 `config/data/`。
- 不改角色行为、工具集合、事件协议、语音会话。
- 不接上 skills 的生产装配。

## Decisions

1. **读取与消费分开。** `config.py` 增加按 token / SKU 取正文的函数。`role_sys_prompts` 与 `log_keywords` 只做解析、降级和导出，不再调用 `read_text`。这样消费方的公开函数签名不变。
2. **搬家用再导出，不改调用方。** 新位置放实现，旧文件只 `from 新位置 import *` 并保持原 `__all__`。测试与 backend 的现有导入本期不批量改写。
3. **归属按已有职责，不新建包。** 成对角色装配进 `assistant/`，事件写入与接收方进 `messaging/`，语音演示进 `realtime_vocie/`。工具分配原计划进 `tools/`，但该目录强制 `tool_*.py`，分配模块不是工具实现，所以留在根上的 `tools_config.py`。
4. **`agent_builders` 留根。** workflow 不应自己读表、装工具、挂中间件。把它收进 `assistant` 会让编排层直接依赖创建细节。
5. **日志关键词的降级留在消费模块。** `config.py` 只负责「文件在不在、正文是什么」；型号非法或文件缺失返回空串的 SOP 语义留在 `log_keywords`。

备选：一次性改完全部导入并删除旧文件。拒绝，因为 backend、测试和文档同时改，回滚面太大。

## 模块防火墙自检

- 不新增跨 App import。engines 仍不 import `django`、`apps.*`、`backend.apps.*`。
- 不新增写库。事件仍只经 `event_sink` 协议交给接收方。
- 新依赖都在 `engines/agents` 内，方向仍是消费方依赖 `config`，`config` 不反向依赖装配层。
- 前端不涉及。

## Risks / Trade-offs

- [再导出掩盖真正落点] → AGENTS.md 写明新位置是主人，旧文件标注过渡；下一次变更再删旧路径。
- [循环导入] → 新模块只依赖 `config` 与原有同包模块；旧文件不做额外逻辑。
- [关键词降级行为变化] → 保持现有空串返回，并用现有 `test_log_keywords.py` 验证。

## Migration Plan

1. 先加 `config.py` 的正文读取函数，消费方改为调用它。
2. 再逐个搬家：tools、assistant、messaging、realtime_vocie。每步保留旧路径再导出。
3. 更新 AGENTS.md 的路径表，标出过渡入口。
4. 回滚按文件还原。旧路径未删，调用方不需要同步回滚。

## Open Questions

无。`agent_builders` 是否最终收进 `assistant` 已由本次方案定为留在根上，不在本变更内再讨论。
