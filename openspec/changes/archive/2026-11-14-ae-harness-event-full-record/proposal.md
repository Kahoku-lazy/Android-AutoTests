## Why

全量转储实验（`temps/event_dump/20261114_184043`，175 条事件）证明：框架每条事件都自带 `created_at`、`id`、`metadata`，`Reply` 事件带 `session_id`，`HintBlockEvent` 带 `source`。这些字段目前一个都没落盘，排查问题时只能拿到自己合成的时间与本方定义的 `event` 名。同时「思考过程」「工具输出」被硬截断（600 / 4000 字符），事后无法复核。

## What Changes

- 事件记录器增加**全量模式开关** `full`，**默认开启**。
- 全量模式下逐条补齐公共字段：`created_at`（框架绝对时间）、`event_id`、`metadata`（非空时）；`Reply` 事件补 `session_id`；`HintBlockEvent` 补 `source`；`TextBlockEndEvent` 补 `text`。
- 全量模式下取消三处硬截断：思考全文、工具输出全文、文本块全文。
- 全量模式仍**按块折叠**：`*DeltaEvent` 继续在内存累积、只落块级结果，不逐条落 delta（实测思考增量占全部事件的 80%）。
- 关闭全量模式（`full=False`）时，行结构与字段回到改造前，供仍想保持小体积的场景使用。

## 关联文档

- 需求来源：需求方直接决策——先补字段、加全量模式开关、按块级折叠、默认开启。
- 实验依据：`temps/event_dump/20261114_184043/`（17 类事件 × 字段清单，未入库）。
- 受影响主 spec：新建 `ae-harness-event-full-record`。
- 相关既有能力：`ae-harness-token-usage`（同一份 JSONL 与记录器）、`ae-harness-observe-hooks`（观测行不受本变更影响）。

## Capabilities

### New Capabilities

- `ae-harness-event-full-record`: 事件记录器的记录保真度——全量字段补齐、块级折叠、开关与默认行为。

### Modified Capabilities

无。`ae-harness-token-usage` 的用量记录需求不变（本变更只增字段，不改其字段语义）；`ae-harness-observe-hooks` 的观测行同样不受影响。

## Impact

- 代码：`engines/ae_harness/event/record.py`（新增 `full` 入参与字段补齐）、`event/AGENTS.md`；4 个入口无需改动（默认值生效）。
- 体积：全量模式默认开启后，思考与工具输出不再截断，单次运行 JSONL 会明显变大；`full=False` 可回到改造前体积。
- 兼容性：`full=False` 时段与字段与改造前一致；`RunRecord` 结构不变。
- 测试：扩展 `tests/engines/ae_harness/unit/test_record_usage.py`，新增全量/非全量两组断言。
