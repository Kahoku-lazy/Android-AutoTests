## Why

执行与验收现在是引擎里手写的「执行 → 验收 → 不合格回灌重试」循环（`DeviceExecutionWorkflow` 内部的 `_run_step`），步骤推进、重试计数、挂起与状态都自己实现，既与框架能力重复，也无法把一次运行的状态落盘后接着跑。AgentScope 官方提供了「步骤 = 一个执行者 + 一个验证者 + 最多驳回几次」的标准作业流程（SOP），把执行与验收放在同一个步骤对象里，运行状态是可持久化的纯数据。

## What Changes

- **BREAKING**：AgentScope 依赖从 `2.0.7.post1` 升到含 `agentscope.sop` 的版本（当前为 `2.0.9`）；升级前用现有引擎单测与真机冒烟验证兼容性，不兼容则退回自建同形步骤层（见 design）。
- 规划出的每一个步骤改由 **SOP 步骤**承载：`SOPStep(subject, description, executor, verifier, max_attempts)`，一个步骤就是「执行者干活 + 验证者验收 + 被驳回则重做」，重试次数由 `max_attempts` 承担（对齐现有 `max_loops`）。
- 引擎里的手写「执行 ↔ 验收」重试循环退役，改由 `SOPEngine` 按序遍历步骤、消耗驳回次数、产出步骤级进度事件。
- 执行者与验证者以 **`AgentLike` 适配器**接入：适配器内部保留平台特有职责（步骤输入前缀、设备日志证据开窗与读窗、点击证据与关键词回填、按角色聚合用量与费用），对外只暴露 `reply_stream` 与 SOP 要求的交付 / 结论。
- 一次运行的状态改为 **`SOPRunState`**（纯数据、可持久化）：任务运行中的进度改由它派生，挂起后可继续。
- 既有对外行为不变：任务结果、步骤过程记录（执行结果三字段 + 验收结论五字段 + 验证截图 + 日志检查 + 设备日志证据）、设备日志证据口径、`logs/agents.log` 过程日志一律不变。

## 关联文档

- 关联需求编号：`PRD-08-AI助手`（智能体管理 · 设备操控）。
- 说明：该子 PRD 文件尚未建立；本单需求来自现场结论（执行与验收耦合、状态不可续跑），并遵循 AgentScope 官方 SOP 设计。

## Capabilities

### New Capabilities

- `ai-executor-verifier-sop`: 执行与验收以 SOP 步骤承载 —— 步骤由「执行者 + 验证者 + 最多驳回次数」构成、驳回回灌、步骤级进度事件、运行状态可持久化与续跑、既有证据与结果口径保持不变。

### Modified Capabilities

- `ai-engine-protocol`: 引擎对 AgentScope 的版本要求与依赖面更新（引入 SOP 模块，且执行 / 验收的编排职责从引擎自建循环转为框架步骤）。

## Impact

- **引擎**：`engines/ai/workflow/workflow.py`（手写重试循环退役，改为构建 SOP 并驱动 `SOPEngine`）、新增执行者 / 验证者的 `AgentLike` 适配器、`engines/ai/agents/base.py`（按 SOP 需要暴露 `reply_stream` 或提供适配器入口）、步骤级进度与运行状态接入既有 `on_progress`。
- **依赖**：`requirements.txt` 的 `agentscope` 版本下限提高；升级后需核对 `agent / credential / model / message / event / tool` 各导入面（已核对 2.0.9 均保留）。
- **平台后端**：`apps/ai_assistant/engine_adapter.py` 与任务进度落库沿用现有口径（运行状态如落盘，落点走引擎注入，不新增跨 App 依赖）。
- **测试**：引擎单测（步骤推进、驳回重试、状态序列化与续跑、适配器证据口径）、平台侧任务链路回归、真机冒烟一次。
- **不做**：不改三角色提示词的输出契约、不改设备动作工具、不改日志证据判定口径、不引入 SOP 服务端（在线人工验收）形态。
