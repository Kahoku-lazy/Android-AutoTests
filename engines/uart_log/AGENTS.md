# uart_log 模块 AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../AGENTS.md) → **本文件**。本文件只写串口日志采集领域增量；**冲突时本文件的领域规则优先**。

## 职责

设备串口 / TCP 日志采集：端口检测、按端口接收线程、落盘、开关。为验收证据与 Harness（如 `tool_serial`）提供日志数据面；**不**承担 Django 端口台账的最终真相（开关状态可与 `serial_log` App 配合，配置项以环境/设置为准）。

| 路径 | 职责 |
| --- | --- |
| `detect.py` | 端口检测 |
| `params.py` | 端口参数 |
| `receiver.py` | 单端口接收线程、按行切开 |
| `writer.py` | 采集写入 |
| `switch.py` | 按端口开关监听；同时打开上限 `MAX_PORTS`（当前 10） |
| `__init__.py` | 导出 `PortSwitch` / `get_port_switch` 等 |

## 红线（禁止）

1. **禁止**跳过本文件与上层流程直接改采集契约（行协议、落盘路径语义、开关上限行为）而不更新文档。
2. **零 Django**：禁止 `import apps.*` / `django.*` / `backend.apps.*`。
3. **并发上限**：尊重 `MAX_PORTS`；拒绝超限时必须可观测（日志），不得静默丢开关请求却假装成功（除非既有 API 已如此约定并写明）。
4. **重复打开**：同一端口重复 open 不得再起一份监听（见 `PortSwitch`）。
5. **不写业务库**：`sl_` 表与 API 在 backend；本包只做采集与文件/内存侧。
6. **日志**：用 `utils.logs.serial_log`；原文与采集通道日志分离（见 ARCH 可观测节）。

## AI 阅读与检查流程（必读）

1. 先读 [`engines/AGENTS.md`](../AGENTS.md)。
2. 改端口模型、接收/落盘、开关语义时再读**本文件**。
3. 写代码前读 style rules；自检：`--path engines/uart_log`。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层入口 | [`engines/AGENTS.md`](../AGENTS.md) |
| Agent 工具封装 | `engines/agents/tools/tool_serial.py` |
| 后端开关 API | `backend/apps/serial_log` |
| 风格检查 | [`.agents/skills/engines-agents-style-check/`](../../.agents/skills/engines-agents-style-check/) |