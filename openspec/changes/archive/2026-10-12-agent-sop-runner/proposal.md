## Why

`engines/agents` 里已经有执行角色与验收角色，但两者只能被逐句手工驱动：没有「多步任务按里程碑逐个验收」的编排，跑完一次多步任务后也拿不到整次运行的用量与费用，只能事后翻日志。现在补上这层编排与汇总，让设备多步检查能一次跑完，并留下可核对的费用结论。

## What Changes

- 新增 SOP 装配：把已 `start()` 的执行角色与验收角色，按「步骤名 + 这一步必须达成的结果」列表装成标准作业流程；步骤可增删，顺序即执行顺序。
- 新增 SOP 运行器：按顺序推进流程、事件实时上屏、按角色把事件写进过程日志，并把步骤名与第几次尝试写进日志的阶段列。
- 新增运行级用量与费用汇总：每次模型调用按**该次调用自己的时刻与模型名**分别计费后求和，给出合计与分角色分项；不写入平台用量表。
- 新增 SOP 专用系统提示词，并允许角色在构造时覆盖系统提示词与角色名（既有默认提示词与输出契约不变）。
- 不修改平台 `engines/ai` 的任何行为。

## 关联文档

无关联 PRD 编号：本次变更只覆盖 `engines/agents` 独立脚手架（当前 git 未跟踪、不在平台 PRD 范围内）的编排与汇总能力，不改变平台任何对外可见行为。

## Capabilities

### New Capabilities
- `agent-sop-runner`: 用执行/验收角色装配并驱动标准作业流程，按角色实时写过程日志，并给出整次运行的用量与费用汇总。

### Modified Capabilities
（无）

## Impact

- 代码：`engines/agents/role/sop.py`（新增）、`engines/agents/role/executor.py`（角色构造参数扩展）、`engines/agents/prompt_config.py`（新增 SOP 提示词）。
- 依赖：`agentscope.sop`（AgentScope 2.0.9 的 `SOP` / `SOPStep` / `SOPEngine` / `SOPRunState`）、`engines/agents/billing.py`、`engines/agents/process_log.py`、`engines/agents/messaging/`。
- 产物：过程日志 `logs/sop-YYYYMMDD.log`；运行状态 JSON（调用方自行落盘）。
- 平台侧（`apps/`、`frontend/`、`engines/ai`）无改动；验证范围为 `engines/agents` 的离线校验脚本（`temps/`）。
