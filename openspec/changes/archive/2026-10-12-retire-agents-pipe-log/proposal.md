## Why

`engines/agents` 里模型运行同时写两份日志：对话稿 JSONL，以及按天切分的管道过程日志。调试已经以对话稿为准，管道日志变成重复实现，还把角色启动绑在一份不再使用的文件上。

## What Changes

- `engines/agents` 的模型运行日志只保留对话稿（`logs/agent_logs/<run-id>.jsonl`）。助手、工具、用户、上下文、汇总仍按现有对话稿契约写入。
- **BREAKING**（仅 `engines/agents`）：去掉管道过程日志。不再创建 `AgentProcessLog`，不再用 `EventStreamRecorder` 把思考 / 工具调用 / 工具返回写成 `时间戳 | 角色 | 模型 | …` 行，也不再写出 `logs/sop-*.log` 这类按天文件。
- 角色 `start` 不再接收过程日志开关与基路径。SOP 运行不再把执行角色的过程日志对象传给 runner。
- HTML 不进入运行器。`temps/` 里的演示页保持原样，运行结束不生成 HTML。

## 关联文档

无关联 PRD。这是智能体运行日志的实现收敛，不改产品需求入口。

## Capabilities

### New Capabilities

### Modified Capabilities

- `agent-dialogue-log`: `engines/agents` 的模型运行信息只写入对话稿；该包不再写管道过程日志，运行器不生成 HTML。

## Impact

- 代码：`engines/agents/process_log.py`、`engines/agents/messaging/events.py` 删除；`engines/agents/role/base.py`、`engines/agents/role/sop.py`、`engines/agents/messaging/__init__.py` 去掉管道日志接线。`DialogueLog` 与 `messages.py` 保留。
- 不改：`engines/ai/process_log.py`、`engines/ai/messaging/events.py`、平台 `engine_adapter` 的按天过程日志，以及 `openspec/specs/ai-agent-process-log`。那条能力仍由平台引擎满足。
- 测试：调整依赖管道日志的 `engines/agents` 单测；对话稿单测保持通过。不跑全量回归。
- 演示：`temps/dialogue-log-demo.html` 不删、不改成运行产物。
