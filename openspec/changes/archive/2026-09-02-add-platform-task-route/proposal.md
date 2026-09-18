## Why

平台任务（platform_task）线路在「双线路 + 任务发布」重构后仍为占位（`views_drf.py` 返回「线路开发中」）。现在需要落地平台任务的真实能力：让 AI 编排平台工具，完成「探索手机→元素定位→页面图谱→用例生成→用例执行」的测试资产生产流水线。

## What Changes

- 新增 `PlatformTaskConfig`（config.py）、`PlatformTask`（model.py）、`PlatformTaskWorkflow`（workflow.py）三个类，复用三模型骨架（planner → executor ↔ verifier）。
- 新增平台任务三套提示词（PLATFORM_PLANNER / PLATFORM_EXECUTOR / PLATFORM_VERIFIER_PROMPT）。
- 新增 `PLATFORM_VERIFIER_TOOLS`（只读查询工具子集）供验收模型二次确认。
- 扩展 `AUTO_ALLOW_TOOLS`，平台写工具（save_case / run_test / save_page_flow 等）自动放行。
- `TaskSubmitAPIView` 的 platform_task 分支从「线路开发中」改为 `PlatformTaskWorkflow.run`。

## 关联文档

- PRD：dev_docs/02-PRD需求/PRD-08-AI助手.md（§2.1 平台小助手：两条线路卡片 + 任务下发）
- ARCH：dev_docs/03-设计与架构/ARCH-08-AI助手.md（v3.4 两条线路，platform_task 占位）

## Capabilities

### New Capabilities
- `ai-platform-task`: 平台任务线路——AI 编排平台工具完成测试资产生产流水线（探索定位 / 页面图谱 / 用例生成 / 用例执行）。

### Modified Capabilities
<!-- 无 -->

## Impact

- apps/ai_assistant/agent_scope/：config.py / model.py / workflow.py / tools.py
- apps/ai_assistant/views_drf.py：TaskSubmitAPIView 的 platform_task 分支接线
- apps/ai_assistant/api.py：新增平台任务执行辅助
- 前端：无改动
- 测试：tests/ai_assistant/ 平台任务相关用例
