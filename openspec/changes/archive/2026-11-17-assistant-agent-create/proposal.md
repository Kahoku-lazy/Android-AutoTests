## Why

智能体创建仍散在 `agent_builders` 与两处 `RealtimeAgent(...)`：创建处自己读配置、自己选模型，语音创建还和使用写在一起。`models_new` 已经把「造模型」收成 config 传表、唯一出口只创建；智能体层还没有对称的一层，workflow 也无法只消费「已经造好的角色」。

## What Changes

- 新增 `engines/agents/assistant`：config 传入整张角色表与模型表，唯一出口按角色键创建 Agent；只创建，不 `reply`、不跑 SOP / GoalPipeline。
- 创建时用角色条目里的模型短名调用 `models_new.create_model`，不经旧包 `engines.agents.models`。
- 语音角色一并收入该出口：聊天角色造 `Agent`，Omni 角色造 `RealtimeAgent`；会话循环仍留在 `realtime_vocie`。
- 旧入口（`build_*`、`realtime_vocie_agent.build_realtime_vocie_agent`、`realtime_vocie/session.py` 内联构造）改为转调新出口，对外名字与返回实例类型不变。
- 本期不改 workflow 的编排方式，不删除旧模块，不改角色 YAML 字段。

## 关联文档

无关联 PRD。原因：这是智能体创建层的结构对齐（与 `models_new` 对称），不改变任务、用例或前端可观察行为。

## Capabilities

### New Capabilities

- `assistant-agent-create`: 由 config 传入的角色表与模型表，按角色键创建聊天或语音智能体；只创建不使用。

### Modified Capabilities

- `agent-harness`: 可运行角色的装配入口从「LLM 走 Factory、语音走 realtime_vocie_agent」改为「统一经 assistant 创建；旧入口只转调」。
- `agent-basic-role-create`: 基本 LLM 角色仍每次新实例、ModelConfig 不进入 Agent；创建实现改为 assistant，并允许同一出口创建 Omni 角色。

## Impact

- 代码：新增 `engines/agents/assistant/`；`agent_builders.py`、`realtime_vocie_agent.py`、`realtime_vocie/session.py` 改为转调。
- 依赖方向：assistant → config + models_new；MUST NOT 反向依赖 workflow / apps / django，也 MUST NOT import 旧包 `engines.agents.models`。
- 测试：新增 assistant 单测（不联网）；既有角色装配、workflow 边界、知识库与语音配置单测应保持通过。
- 非目标：不改 `workflow/` 的每步新建策略，不清理 `case_roles` 的运行时挂工具，不删除 `agent_builders.py`。
