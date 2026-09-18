## Context

三模型骨架已就绪：`DeviceExecution`（config/model/workflow 三层的设备执行类）+ `DeviceExecutionWorkflow`（planner → executor ↔ verifier）。`route_configs` JSON 已含 `platform_task` 三槽配置，但代码层无对应类，platform_task 分支为占位。

## Goals / Non-Goals

**Goals:**
- 用 class 区分线路：新增 `PlatformTaskConfig` / `PlatformTask` / `PlatformTaskWorkflow`。
- 复用三模型骨架（planner → executor ↔ verifier，max_loops 重试）。
- 平台任务全用文本模型（工具返回 JSON/文本，无图）。
- executor 装 `REASONING_TOOLS`，verifier 装 `PLATFORM_VERIFIER_TOOLS`。

**Non-Goals:**
- 不改动设备控制（device_control）现有逻辑。
- 不新增 .py 文件（config/model/workflow/tools 内加类）。
- 不新增数据表 / Pydantic 契约（复用 GoalPlan / PlannerOutput / VerificationResult）。
- 不做异步后台执行（首版同步 asyncio.run）。

## Decisions

- D1 写工具权限 → AUTO_ALLOW：用户下发任务即授权，平台写工具自动放行。
- D2 同步 vs 异步 → 首版同步 asyncio.run，与 device_control 一致，后续迁后台任务。
- D3 借道设备 → 允许：职责① capture_page、职责④ run_test 需 serial，目标产出仍是平台资产。
- D4 独立提示词 → 独立：平台任务 planner/verifier 语义（产出资产）与设备控制（操作设备）不同。

## 模块防火墙自检

- 跨 App import：仅经各 App api.py（capture_snapshot / save_snapshot_to_elements、save_ai_definition / get_case_digest、get_run_status / run_test、get_or_create_flow、build_page_flow_document 等），已在 tools.py 现有 handler 内完成，本设计无新增跨模块 import。
- 无直接 ORM 写：所有写操作经各 App api.py。
- 无新增 service / runner / consumer / state_machine import。

## Risks / Trade-offs

- [平台写工具 AUTO_ALLOW 可能误写] → 任务下发即授权 + verifier 二次确认 + 日志可审计。
- [同步执行阻塞慢任务（run_test）] → 首版接受，后续迁后台任务 + AITask 状态轮询。
- [planner 职责判断错误] → 独立 PLATFORM_PLANNER_PROMPT 显式要求「先判断职责①~④再编排工具」。
