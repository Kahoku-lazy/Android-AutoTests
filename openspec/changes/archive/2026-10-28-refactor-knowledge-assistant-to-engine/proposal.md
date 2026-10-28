## Why

`engines/agents/AGENTS.md` 已约定语音助手实现归 `engines/agents/realtime_vocie`，但当前 AgentScope 相关代码（实时模型配置、系统提示词、事件桥、`RealtimeAgent` 会话、浏览器传输）仍放在 `backend/apps/knowledge_assistant`，导致引擎层与接入层混在一起，后续复用与职责边界不清。

## What Changes

- 把 AgentScope 相关实现迁到 `engines/agents/realtime_vocie/`：实时语音配置与模型工厂、平台提示词、AgentScope 事件桥、`RealtimeAgent` 会话编排、`TransportBase` 浏览器音频传输。
- 后端 App 只保留接入职责：WS consumer、就绪状态 HTTP、本地对话日志 `DialogueLog` 与日志路径解析。
- 引擎层遵守 `engines/AGENTS.md`：不再新增 `ConfigError` 自定义异常，改用内置 `RuntimeError`；引擎不 import 后端 App，日志通过 `VoiceLogSink` 协议注入。
- 不改变 WS 路径、事件格式、日志字段、页面行为或侧栏入口。

## 关联文档

- 已归档变更 `2026-10-28-add-knowledge-assistant-voice` 与 `2026-10-28-add-knowledge-assistant-mic-diagnostics`
- `engines/agents/AGENTS.md`「realtime_vocie：语音助手功能相关代码」

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无（纯结构调整，外部行为不变，`skip_specs: true`）。

## Impact

- 新增 `engines/agents/realtime_vocie/` 包；删除后端 App 内的 `config.py`、`knowledge.py`、`events.py`、`session.py`、`transport.py`。
- 新增后端 `runtime.py`（日志目录解析 + 状态 payload）；`consumer.py`、`views.py`、测试 import 同步调整。
- 引擎层异常改为 `RuntimeError`；对话日志通过协议注入，引擎不再依赖 `backend.apps.knowledge_assistant`。
