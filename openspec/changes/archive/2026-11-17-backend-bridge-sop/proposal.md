## Why

平台现在只有**单角色**执行（`platform_ui` 对话卡）：模型自己说做完就算完，没有验收。

`engines/ae_harness/workflow/sop/` 已有完整的「执行者动手 + 验收者逐条核对」抽象，但只有控制台装配（`sop_runner.py`，读命令行、打印、落本包 `logs/`）。平台侧没有自己的装配入口。

本变更**只补这个装配入口**：在 `engines/backend_bridge/workflow/` 建平台 SOP，调用既有抽象，不改对话页、不改 `ae_harness` 的实现。

## What Changes

- 新增 `engines/backend_bridge/workflow/`：
  - `roles.py`：装配执行者（全量设备工具）与验收者（只读工具），共用一个观测中间件。
  - `sop_ui.py`：一次运行的入口——选流程、覆盖任务描述、调 `run_sop`、把结果整理成 `SopRunResult`。
- 步骤加载、步骤推进、重试预算、驳回记录、事件记录、报告渲染全部复用 `engines/ae_harness/workflow/sop` 与 `engines/ae_harness/event`；**不新写编排、不新立步骤格式**。
- 报告落在 `logs/agents/backend_bridge/`；逐次用量作为结构化数据返回，由后端写入既有账本。
- 新增管理命令 `run_ui_sop`，用于在平台侧触发并验收这条 SOP（与单角色命令 `run_ui_agent` 并列）。

**明确不做**：不改 AI 助手对话页、不新增对话卡片、不改 `WorkflowListView` / `WorkflowStreamView`、不改 `ae_harness` 任何代码、不接 `task_list` 任务链路。

## 关联文档

- 需求来源：需求方「在 `engines/backend_bridge` 创建 UI 执行与验收的 SOP，功能与 `ae_harness` 一致，只允许使用不允许自创；**本次只改 SOP，对话页不参与**」。
- 边界规则：[`engines/backend_bridge/AGENTS.md`](../../../engines/backend_bridge/AGENTS.md)（2.1 SOP 与单角色分工、红线 7「禁止自创 SOP」）、[`engines/ae_harness/workflow/AGENTS.md`](../../../engines/ae_harness/workflow/AGENTS.md)（`sop/` 是通用抽象，只有 `sop_runner.py` 是控制台装配）。
- 受影响主 spec：新建 `backend-bridge-sop`。
- 相关既有能力：`backend-bridge-agent`（单角色平台会话，本变更不改它）。

## Capabilities

### New Capabilities

- `backend-bridge-sop`: 平台侧执行 + 验收 SOP 的装配、一次运行的返回值形状、触发入口与报告落盘。

### Modified Capabilities

无。对话页仍只有单角色，SOP 不进对话模块。

## Impact

- 代码：新增 `engines/backend_bridge/workflow/{__init__,roles,sop_ui}.py` + `backend/apps/ai_assistant/management/commands/run_ui_sop.py`。
- 依赖方向：`backend_bridge → ae_harness`（单向），`ae_harness` 零改动。
- 产物：`logs/agents/backend_bridge/<时间戳>/<时间戳>_sop_ui.{jsonl,html}`（与单角色报告同根、不同角色名）。
- 测试：新增 `tests/engines/backend_bridge/unit/test_sop_*.py`。
