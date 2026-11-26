## Why

任务清单里「失败」是唯一没有证据入口的终态：报告只在事件流正常跑完后渲染，模型 400、网关不可用这类运行中异常会绕过收尾，任务只剩一个「失败」标签。实测 30 条任务里 18 条失败、只有 2 条有报告（都是验收不通过），与 PRD 要求的「失败能定位到具体步骤与证据」不符。

## What Changes

- SOP 运行在**运行中异常中断**时也落一份 HTML 报告：补写过程日志的收尾汇总、结束对齐记录并渲染报告，在报告概览里标注「运行中断：<原因>」。
- 把这次报告定位交回调用方：`run_bound_sop` 增加失败回调，`task_runner` 在失败 payload 写入 `report_run` / `report_name`。
- 失败任务因此自动获得「报告」入口：任务清单按钮与测试报告台账都按既有 `report_run` / `report_name` 契约工作，**不需要**改前端与台账代码。
- 明确不产报告的边界：用户取消（`cancelled`）、预算中断（`interrupted`）、起跑前失败（绑定/工作流编号缺失，尚无事件）保持现状。
- 规格补齐：把「哪些终态产报告、失败报告如何交回调用方」写进主规格，避免以后又只在正常路径产出。

**BREAKING**：无。失败 payload 只新增两个既有字段，接口形状不变，无数据库迁移。

## 关联文档

- `PRD-平台总需求`：测试工程师场景「失败能定位到具体步骤与证据」；观测闭环含任务事件时间线与测试报告。
- 相关既有规格：`backend-bridge-sop`、`ai-task-list`、`report-ai-task-list`、`task-execution-lifecycle`。

## Capabilities

### New Capabilities

<!-- 无新增能力：本次只补既有 SOP 报告链的失败分支。 -->

### Modified Capabilities

- `backend-bridge-sop`: 报告产出时机从「只在正常结束」扩展到「运行中异常中断也产出」，并新增失败回调把报告定位交回调用方。
- `ai-task-list`: 失败任务行在结果带报告定位时 MUST 提供「报告」入口。
- `report-ai-task-list`: 异常中断产生的失败报告 MUST 与验收不通过的报告同等进入报告台账。
- `task-execution-lifecycle`: 明确 `completed` / `failed` 产报告、`cancelled` / `interrupted` 不产报告的口径。

## Impact

- **引擎装配**：`engines/backend_bridge/workflow/bound_sop.py`（失败收尾与回调）；不改 `engines/ae_harness/`。
- **后端任务**：`backend/apps/task_list/task_runner.py`（失败 payload 带报告定位）。
- **接口**：`/api/tasks/*` 的列表行新增非空 `report_run` / `report_name`；`/api/reports/` 增多行失败报告。字段与信封不变。
- **前端**：`frontend/src/modules/task-list/`、`frontend/src/modules/report-generator/` 代码不变，只多出可点的失败报告。
- **测试**：新增 `tests/task/integration/` 灰盒用例；`tests/arch/unit/test_sop_report_contract.py` 增契约守护；回归 `tests/report/`。
- **文档**：`task_list_task_lifecycle.md`、`backend_bridge_role_assembly.md` 补失败报告口径。
