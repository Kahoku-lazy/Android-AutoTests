## Context

见 proposal.md - Why。与本方案直接相关的现状：

- `assistant.create_agent` 先 `models_new.create_model`，再按实例是 `ChatModelBase` 还是 `RealtimeModelBase` 分支。门面只导出这一个出口。
- `agent_builders._build` 已转调 `create_agent`。workflow 只调用 `build_*` / `case_roles`，不直接创建。
- `realtime_vocie/session.py` 直接调用 `create_agent(..., "OMNI_ROLE_CONFIG")`，并自己持有传输。
- `models_new` 的族是 `chat` / `realtime` / `embedding` / `tts`。TTS 中间件仍走旧包 `get_tts_model`。
- 官方 2.0.9：聊天模型进 `Agent`，实时模型进 `RealtimeAgent`；TTS 是独立模型族，不是另一种智能体。级联方案尚未作为现成能力给出。

## Goals / Non-Goals

**Goals:**

- 两个出口在类型和参数上互斥，选错族在创建时失败。
- 旧名字继续可用：`build_*` 只转调聊天出口，语音会话只转调语音出口。
- 聊天模型仍按（短名, stream）复用；语音模型不复用。智能体每次新建。

**Non-Goals:**

- 不删 `agent_builders.py`，不改 workflow 每步新建，不改 `case_roles` 运行时挂工具。
- 不把 TTS 或嵌入收进 assistant，不迁移旧包 `models`。
- 不改事件落库，不把本地麦克风演示收进 assistant。

## Decisions

### 1. 两个具名出口，删除按类型分支的公共出口

门面导出 `create_chat_agent` 与 `create_voice_agent`，不再导出会按实例类型分支的 `create_agent`。

备选是保留 `create_agent` 作为内部转发。否决：只要公共名字还在，新调用方就会绕回混合出口，分流没有约束力。已持有聊天模型的 `create_from_model` 保留为聊天侧兼容函数，不接受实时模型。

### 2. 族校验放在创建前，不靠构造失败

聊天出口只接受 `family=chat`；语音出口只接受 `family=realtime`。错误类型仍是 `AgentConfigError`，消息带角色键和实际族。

备选是造完再 `isinstance` 拒绝。否决：那仍是现在的「先造再猜」，嵌入和 TTS 会先被实例化。

### 3. 语音出口的参数面更窄

语音出口只收工具包、提示词、名字。传入上下文、ReAct、中间件或 `stream` 即失败，不静默丢弃。

备选是忽略多余参数。否决：调用方会以为这些配置生效了。

### 4. 调用方只改转调目标

`agent_builders._build` 改调 `create_chat_agent`。`realtime_vocie/session.py` 与 `realtime_vocie_agent.py` 改调 `create_voice_agent`。workflow 的 import 不动。

### 5. TTS 留在中间件

聊天出口仍可用 `with_tts` 决定默认中间件是否包含语音合成。合成模型不经 assistant 创建。这样文字角色出声和端到端语音不会再合成一个出口。

## 模块防火墙自检

- 本变更只在 `engines/agents` 内。不新增跨 App import，不写库。
- assistant 继续 MUST NOT import `apps.*` / `django.*` / `workflow` / 旧包 `engines.agents.models`。
- 前端不涉及。仪表盘不涉及。

## Risks / Trade-offs

- [旧测试和文档仍写 `create_agent`] → 同一变更内改测试与包文档；不留兼容别名。
- [语音角色节里已有 context / react 字段] → 语音出口不读取这些字段；不要求本期改 YAML。只有调用方显式传入才拒绝。
- [旧包模型门面规格仍要求经 `engines.agents.models`] → 本期不改那条规格，也不迁移 RAG / TTS / 画廊。
