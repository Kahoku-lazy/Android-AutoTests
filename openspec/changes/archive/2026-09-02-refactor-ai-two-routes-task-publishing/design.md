## Context

后端 `apps/ai_assistant/` 已有 4 套 Harness（planner / vision / reasoning / strong），`plan()` + `build_agent()` 已实现「规划 → 执行」。前端为单模型配置 + 自由对话（SSE）。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 智能体配置从单模型改为多线路（`route_configs`）。
- 任务发布（提交 → 分发 → 列表/详情）。
- 移除主对话（SSE + 聊天窗口）。

**Non-Goals:**

- 平台任务线路本期只做入口占位，不开发 reasoning 执行逻辑。
- 不改动 toolbox / knowledge / evaluator 三个子页。

## Decisions

### D1 配置存储：route_configs JSONField

- 选择：`ai_agents` 增 `route_configs JSONField`。
- 备选：拆表 `ai_agent_routes` + `ai_route_models`（规范但 3 表 + 迁移量大）。
- 理由：符合「一智能体 = 一配置对象」语义，增线路免迁移。

### D2 任务模型：扩展 ai_tasks

- 选择：扩展 `AITask`（goal / requirements / attachment / route / checklist / report_name / status）。
- 备选：新表 `ai_task_submissions`。
- 理由：复用已有表 + 历史端点。

### D3 线路分发

- 选择：`TaskSubmitAPIView` 内按 `route` 分发；`device_control` → `plan()` + `build_agent("vision")`；`platform_task` → 占位返回「线路开发中」。
- 理由：复用已有 `plan()`/`build_agent()`，platform_task 不提前开发。

### D4 主对话移除

- 选择：删 SSE 路由 + `chat_views.py` + 前端聊天窗口 + 会话/消息 API。
- 理由：任务历史由 `ai_tasks` + `ai_execution_logs` 承载。

## 模块防火墙自检

- `ai_assistant` 写库收敛到 `api.py`（`route_configs` 加密、任务 CRUD 均走 api.py）。
- 不跨 App import `service`/`runner`/`consumer`/`state_machine`；线路执行经 `device_pool`/`device_inspector`/`case_manager`/`test_runner` 的 `api.py`（现有 `tools.py` 已如此）。
- 前端不直连数据库，经 `djangoClient` → `/api/...` DRF。
- SSE 删除不新增通道（通道收敛：移除唯一 SSE，无新增）。

## Risks / Trade-offs

- [route_configs 迁移旧扁平字段折叠] → 数据迁移脚本 + 回滚预案。
- [SSE 删除面广] → 确认 gateway/中间件无残留引用；前端删 `useSSE`/`SSEMessageBuilder`。
- [api_key 存于 JSON 内] → 复用 Fernet 加密 + 脱敏 + 一次性 reveal。
- [platform_task 占位] → 明确返回「线路开发中」，避免静默吞错。
