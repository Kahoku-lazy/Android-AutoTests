## Why

角色过程日志现在写进单个 `logs/agents.log` 且只追加：跑得越久文件越大，排查某一天的问题要在超大文件里翻。按天切分后，一天的记录落在一个小文件里，定位、查看与日后清理都直接可做。

## What Changes

- 过程日志改为**按天切分**：文件名形如 `agents-20261009.log`（基名 + 当天日期），仍为追加写。
- 同一次运行跨过零点时，后续记录自动落到新一天的文件里，MUST NOT 继续写旧文件。
- 落点注入契约不变：调用方仍注入基路径（如 `<BASE_DIR>/logs/agents.log`），按天命名由引擎侧派生。
- **不做**自动删除或保留期策略（旧文件按天保留，清理另行决定）。

## 关联文档

- 关联需求编号：`PRD-08-AI助手`（智能体管理 · 设备操控）。
- 说明：该子 PRD 文件尚未建立；本单需求来自使用反馈（单文件无界增长）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-agent-process-log`: 「过程日志的文件与自动创建」需求改为按天切分的命名与跨天切换，其余约束（追加写、自动创建、落点注入、并发不串行）不变。

## Impact

- **引擎**：`engines/ai/process_log.py`（文件名派生与跨天切换）、`engines/ai/agents/base.py` 无需改动（仍传基路径）。
- **平台后端**：`apps/ai_assistant/engine_adapter.py` 的注入点不变（仍是基路径），仅注释与文档口径同步。
- **测试**：`tests/graybox/unit/test_agent_process_log.py`（当日文件名、跨天切换、追加不覆盖）。
- **运维**：`logs/` 仍不入版本库；旧文件按天累积，清理策略另议。
