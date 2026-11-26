## Why

SOP 与单角色执行器共用同一条 AgentScope 事件与观测管线，但运行产物与报告口径已经分叉：SOP 仍走旧的四段式渲染，既不渲染已采集的观测，也不落对齐记录与原始事件流。`logs/agents/backend_bridge` 里 25 次 SOP 运行只有 12 份 HTML、0 份 aligned，报告正文里搜不到「系统提示」「model_call」（实测命中 0 次，而同目录单角色记录 145 条观测全部可见）。设备契约与运行参数也弱一档：SOP 只把 serial 拼进任务文本，没有在线校验与运行期独占，图像保留与推理上限走框架默认值（5 张 / 50000 token / 50 轮）。

## What Changes

- SOP 运行产物补齐：对齐记录（`run` / `input` / `replies` / `observations` / `summary` / `events`）、原始事件流（逐事件实时写）与媒体目录，与单角色执行器同目录、同命名规则。
- SOP 观测补齐全量上下文：每轮模型真实收到的消息 MUST 入观测；执行者与验收者共用同一中间件，按角色名区分，不重复实例化。
- SOP 报告改用对齐记录渲染：五页签（报告 / 概览 / 阶段 / 事件流 / 原始记录）；「阶段」按 SOP 步骤切分，每步展示执行者与验收者两个角色块、该步验证结论与尝试次数。
- SOP 运行入口补齐设备契约：平台传入 serial，装配任何模型之前校验在线且状态可用，运行全程独占；MUST NOT 由模型或工具自行枚举、切换设备。
- SOP 运行参数与单角色执行器对齐：图像保留数、工具结果上限、最大推理轮次取同一组值。
- **BREAKING**（对本能力 spec 而言）：`backend-bridge-sop` 现有「本变更 MUST NOT 修改 `engines/ae_harness` 下任何代码」的条款被本轮推翻——对齐记录、观测采集与报告渲染的契约都在 `ae_harness`，SOP 侧只做接线；编排抽象（`load_spec` / `run_sop`）仍不得另写一套。
- 非目标：`goal` / `team` 两条路径接入对齐记录；报告视觉契约（三层折叠、手绘序号、字号三档、左栏默认宽度）不变；前端报告查看器、任务字段与接口契约不改。

## 关联文档

无关联 PRD 编号：本变更是引擎侧 SOP 运行产物与报告口径收敛，不新增产品能力、不改变用户可见的任务字段与接口契约。

## Capabilities

### New Capabilities

- `ae-harness-sop-report`: SOP 报告契约——五页签、按步阶段、双角色块、每步验证结论，以及 SOP 对齐记录与原始事件流的落盘契约与可复现要求。

### Modified Capabilities

- `backend-bridge-sop`: 「SOP 只装配不自创」的 ae_harness 零改动条款、「报告与用量落在平台目录」的报告口径；新增设备前置校验与运行参数对齐。
- `agent-sop-runner`: 「运行时按角色实时写过程日志」扩展为同时产出对齐记录与原始事件流，报告渲染交由调用方决定。

## Impact

- 代码：`engines/ae_harness/event/aligned.py`、`engines/ae_harness/event/render_aligned.py`、`engines/ae_harness/workflow/sop/runner.py`、`engines/backend_bridge/workflow/bound_sop.py`、`engines/backend_bridge/workflow/bound_roles.py`。
- 产物：`logs/agents/backend_bridge/<时间戳>/` 新增 `<时间戳>_sop_bound.aligned.json`、`.raw.jsonl`、`.media/`；`_sop_bound.html` 由四段式变为五页签。
- 兼容：单角色执行器与 AI 助手对话栏报告行为不变；`goal` / `team` 继续用旧渲染器；平台 SOP 任务提交处已强制选设备，故新增设备校验对既有可达入口无行为回退。
- 测试：`tests/arch/unit` 增加 SOP 报告契约守卫与阶段切分单测；验收需一次真实 SOP 任务（真机 + 已发布 SOP 工作流）。
- 文档：`.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md`、`.agents/docs/engines/ae_harness_workflow/ae_harness_workflow_sop_abstraction.md`、`.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md`。
