## Why

报告渲染目前把事件流折叠成自研的 `RunRecord.steps` 再拼 HTML，与 AgentScope 官方的「`Msg` → 内容块 → 事件」语义并行：同一轮运行有两套折叠、两种真相。日志侧已经产出 `aligned.json`，其 `replies[].msg` 由官方 `Msg.append_event()` 折叠而成，而报告仍读 `steps`，块顺序、思考与工具块的归属只能靠自研规则再复现一遍。把渲染切到 `replies[].msg` 之后，只剩一套语义可维护。

## What Changes

- 报告渲染器的数据源从 `RunRecord.steps` 切到对齐记录的 `replies[].msg.content`（官方内容块）。
- 新增「对齐运行记录」能力：`schema` 版本、`run` / `input` / `replies` / `observations` / `summary` / `events` 六段结构、按 `reply_id` 分组的多回复、媒体以 `URLSource` 落旁路且事件可被官方 schema 重新校验。
- 报告区块按内容块类型映射（`thinking` / `text` / `tool_call` / `tool_result` / `hint`）；未知块类型 MUST 降级展示，MUST NOT 丢弃或抛错。
- 报告的耗时与用量 SHALL 取自 `msg.usage` 与运行 summary，MUST NOT 再从 steps 重算。
- 保留 `ae-harness-report-render` 现有视觉契约（三层折叠、手绘序号、字号三档、左栏默认宽度）：只换数据源，不改视觉规则。
- 记录器与 `.jsonl` 继续产出，本次不删除（任务报告接口仍读它）。
- 非目标：任务报告接口（`agent-task-flow-report`）的数据源切换；SOP / goal / team 三条路径接入对齐记录。

## 关联文档

无关联 PRD 编号：本变更是引擎侧运行产物与报告渲染的数据源收敛，不新增产品能力、不改变用户可见的任务字段与接口契约。

## Capabilities

### New Capabilities

- `ae-harness-aligned-record`: 对齐 AgentScope 官方 Msg 结构的运行记录——六段结构、schema 版本、官方折叠、按 `reply_id` 分组、媒体 URL 源与事件可重校验。

### Modified Capabilities

- `ae-harness-report-render`: 报告渲染的数据源与块映射——新增「唯一数据源为 `replies[].msg`」与「按块类型映射、未知块降级」两条需求，其余视觉契约不变。

## Impact

- 代码：`engines/ae_harness/event/aligned.py`、`engines/ae_harness/event/render.py`、`engines/ae_harness/event/record.py`（渲染入参改为对齐记录）、`engines/backend_bridge/session.py`、`backend/apps/ai_assistant/services/assistant_threads.py`。
- 产物：`logs/agents/**/*.aligned.json`（新增）；现有 HTML 报告的视觉分区不变，区块内容改由内容块渲染。
- 测试：报告渲染用例按块视图断言；`tests/arch/unit` 可新增对齐记录 schema 的契约守护；`tests/ai_assistant` 的对话页不受影响。
