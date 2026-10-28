# 事件流信息完整性与运行预算

## Why

一次任务的 SOP 事件流本该能独立回答「跑了什么、为什么停」，实际有三类信息在写库前就丢了：SOP 步骤起点被当作无意义的自定义事件整体丢弃；模型推理轮次用尽与运行时注入的提醒没有对应记录，于是「模型为什么突然收尾」无从解释；事件行的用例名在整任务范围内只绑一次，一个任务按序跑多条用例时每行都写同一个值。同时单个任务没有总次数与总时长上限——单步最坏 460 次模型调用，没有兜底就会无限叠加；批量写库一旦整批失败，剩余事件会被一并丢掉。

## What Changes

- 事件表新增三类事件行：SOP 步骤起点、运行时注入提醒、模型推理轮次用尽。
- 事件行的用例名改为**每条用例开始时刷新**（此前整任务只有一个值）。
- 一个任务里的执行与验收角色改为**每条用例新建**（落实既有「后一条用例不得复用前一条对话」的要求，此前实现与要求不一致）。
- 新增**运行预算**：模型调用次数与运行时长两个上限，超限停止整轮任务，已完成的用例保留、已落库事件不丢。
- 事件写库加固：整批写入失败降级逐行；单批按字节上限分片；截图编码失败在行载荷上留标记。
- 报告补三类新事件的可读标题与明细，步骤起点也作为一轮的起点。
- 无破坏性变更：不新增列、不写迁移、不改接口形状。

## 关联文档

无关联 PRD：本次为运行可观测性与运行预算的修复，验收以「同一任务的事件流能自解释」「超预算时可预期地停止」为准。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-event-fold`: 步骤起点不再一律忽略；新增运行提醒与超轮次的记录；块类型扩展为含 `sop_step` 与 `hint`。
- `agent-events-show`: 动作表从九个扩展到十二个；新增运行预算的计数与中断信号。
- `agent-task-event-store`: 用例名按用例刷新；批量写入失败降级与按字节分片；坏图在载荷上留标记。
- `agent-task-flow-report`: 步骤起点开新轮；三类新事件给出可读标题与明细。
- `sop-task-run`: 新增运行预算超限时停止整轮。

## Impact

- 引擎：`engines/agents/event_sink.py`（用例名与预算）、`engines/agents/messaging/fold.py`（三类记录）、`engines/agents/messaging/messages.py`（预算中断）、`engines/agents/workflow/platform_run.py`（逐用例刷新与停止）、`engines/agents/workflow/ui_auto_workflow.py`（步骤号匹配）。
- 后端：`backend/apps/task_list/event_store.py`（用例名、降级写、坏图标记）、`backend/apps/task_list/task_reports.py`（新事件展示与分轮）。
- 前端：不改。时段前端不读 `event_type`，只渲染后端给出的 `label` 与 `detail`。
- 数据：不新增列、不写迁移；事件行数每步每次尝试 +1（步骤起点），增量行数不变；旧事件行保持原值。
- 测试：新增 `tests/graybox/unit/test_sop_event_stream.py`（11 条）与 `tests/graybox/unit/test_event_store_resilience.py`（3 条）。
- 运行配置：`SOP_MAX_MODEL_CALLS`（默认 600）、`SOP_MAX_RUN_SECONDS`（默认 7200），0 表示不限制。
