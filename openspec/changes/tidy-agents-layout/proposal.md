## Why

`engines/agents/` 的分包边界已经清楚，但根上散落 7 个文件，`config/` 又把资产、读取口和各消费方的加载器放在一起。配置规则要求只有 `config.py` 读文件，代码还没做到。现在收拢，避免下一次改角色装配时继续在根目录找入口。

## What Changes

- 配置读取收口到 `config.py`：提示词、应用短卡、日志关键词正文不再由各自模块直接读文件。
- `tools_config.py` 迁入 `tools/`，仍是唯一工具分配入口；根路径保留再导出。
- `case_roles.py` 迁入 `assistant/`；`event_log.py` 与 `event_sink.py` 迁入 `messaging/`；`realtime_vocie_agent.py` 收成 `realtime_vocie` 的演示入口。旧路径均保留再导出。
- `agent_builders.py` 留在根上，继续作为 workflow 认识的唯一工厂。
- `role_loader.py` 本期不搬家、不删除。生产装配仍走 `assistant.loader`。
- 不改 `realtime_vocie` 拼写，不拆 `config/data/`，不改变角色、工具、提示词的对外行为。

## 关联文档

无独立需求编号。这是目录收拢，行为以现有 `agent-harness` 规格为准；需求入口仍是平台架构定位，不新增产品能力。

## Capabilities

### New Capabilities

### Modified Capabilities

- `agent-harness`: 提示词读取、工具分配、事件出口与语音演示入口的模块落点变化；对外行为与旧路径兼容不变。

## Impact

- 代码：`engines/agents/config/`、`tools/`、`assistant/`、`messaging/`、`realtime_vocie/`，以及根上对应旧文件。
- 文档：`engines/agents/AGENTS.md`、`config/AGENTS.md`、相关子目录 AGENTS。
- 测试：现有导入路径应继续可用；新增覆盖只验证读取收口与再导出，不改角色行为。
- 后端与前端调用不改。`backend/` 继续经现有 engines 入口使用。
