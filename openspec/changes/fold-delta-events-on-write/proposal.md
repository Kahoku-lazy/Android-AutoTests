# 事件写库时折叠流式增量

## Why

`task_events` 里 95% 的行是流式增量片段：任务 142 共 174,098 行，其中 167,684 行是工具参数/结果增量的一个个片段；截图里一次工具调用就能写出 17,447 行。报告在读取时又把它们合并回一条并显示 `×N`，等于把同一个合并动作做两次，还让事件表背着 152 MB。

## What Changes

- 平台接收方在**写库前**折叠：连续且同类型、同步骤、同尝试次数的增量合并成一行，用新增列 `delta_count` 记录条数；行的展示时刻取该段第一条增量的时刻。
- 引擎与前端不变：实时流式显示仍逐片段推送，只有落库这一层折叠。
- 报告改为使用存储的 `delta_count`：`×N` 语义、顺序、时间、明细全部不变；旧数据（`delta_count=1`）逐条增量仍按原逻辑合并展示。
- 新增迁移加 `delta_count`；历史事件不回溯折叠（兼容即可）。

## 关联文档

无关联 PRD：本次为存储与取数结构优化，验收以「同一任务报告输出不变」「事件行数与体积显著下降」为准。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-event-store`: 写入要求新增「连续增量合并成一行并记录 `delta_count`」。
- `agent-task-flow-report`: 轮次里的 `count` 改为取该段增量的 `delta_count` 之和。

## Impact

- 后端：`backend/apps/task_list/event_store.py`（折叠）、`models.py`（`delta_count`）、`task_reports.py`（读取 count）、新增迁移。
- 引擎：不改（`engines/agents/messaging/fold.py` 继续逐片段产生记录供实时显示）。
- 前端：不改（仍展示 `×N`）。
- 数据：单任务事件行约 14.8 万 → 9,600（-93%），表体积预计 152 MB → 约 15 MB；历史数据保留原样。
