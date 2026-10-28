## Context

语音助手当前从 `backend/apps/knowledge_assistant` 同时承担引擎与接入两件事：`config.py` 直接依赖 AgentScope，`session.py` 直接使用 `RealtimeAgent`，`transport.py` 实现 `TransportBase`；这些都属于 `engines/agents` 的职责。后端真正需要保留的是 Channels consumer、HTTP 状态接口和本地 JSONL 日志。

## Goals / Non-Goals

**Goals:**

- AgentScope 相关代码全部落到 `engines/agents/realtime_vocie/`。
- 引擎不反向 import 后端 App；后端只做适配。
- 不改变任何外部契约：WS 路径、事件名、日志字段、页面文案。

**Non-Goals:**

- 不改模型、音色、VAD、页面 UI 或侧栏。
- 不把对话日志归档迁到引擎（它是平台本地档案，不是 AgentScope 能力）。
- 不新增抽象层或第二套配置来源。

## Decisions

### 1. 引擎包边界

`engines/agents/realtime_vocie/` 放：`config.py`（模型配置/工厂/环境读取）、`knowledge.py`（平台提示词）、`events.py`（AgentScope 事件 → 线格式）、`session.py`（`RealtimeAgent` 编排）、`transport.py`（`TransportBase` 浏览器实现）。

后端 `backend/apps/knowledge_assistant/` 只保留：`consumer.py`、`views.py`、`urls.py`、`runtime.py`、`transcript_log.py`、`apps.py`。

### 2. 引擎异常用内置类型

`engines/AGENTS.md` 禁止新增自定义异常。原 `ConfigError(RuntimeError)` 改为直接抛 `RuntimeError`，消息文本保持不变；后端 consumer 捕获 `RuntimeError` 并转成可读 WS 错误。

### 3. 日志用协议注入，引擎不 import 后端

`events.py` 定义 `VoiceLogSink` 协议（`message` / `event`）；后端 `DialogueLog` 结构化满足该协议。`session.py` 只依赖协议，不再 import `transcript_log`。

### 4. 日志目录与状态留在后端

`runtime.py` 读取 `KNOWLEDGE_ASSISTANT_LOG_DIR`、解析 `logs/knowledge_assistant` 并拼出状态接口的 `log_dir/log_file`；引擎只返回 `enabled/ready/reason/model/voice/agent_name`。

## 模块防火墙自检

- 引擎不 import `backend/apps/*`；后端可以 import `engines.agents.realtime_vocie`（引擎层被上层依赖）。
- 没有数据库写入、没有跨 App 内部实现 import、没有新增 WS 通道。
- 对话日志仍由后端 `DialogueLog` 写本地文件，引擎只调用协议。

## Risks / Trade-offs

- [import 路径迁移导致漏改] → 用 `grep` 扫 `backend.apps.knowledge_assistant.(config|knowledge|events|session|transport)`，并跑相关单测。
- [异常类型变化影响调用方] → 后端只在 consumer 捕获 `RuntimeError`；测试同步断言 `RuntimeError`。
- [两个相似目录 `realtime_voice` / `realtime_vocie` 混淆] → 以 `engines/agents/AGENTS.md` 登记的 `realtime_vocie` 为准，删除空目录 `realtime_voice`。
