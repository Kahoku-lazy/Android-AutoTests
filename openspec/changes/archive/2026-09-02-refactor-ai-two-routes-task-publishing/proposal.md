## Why

平台小助手当前是「自由对话」形态（用户自然语言 → 规划 → 执行），缺乏可治理、可审计的任务化入口。为收敛为「两条明确能力线路 + 任务发布」，需要把智能体配置改为多线路模型配置、新增任务发布模块，并移除主对话。

## What Changes

- 新增：智能体多线路配置——一个智能体携带多条线路的模型配置（控制设备 = 规划模型 + 执行模型；平台任务 = 规划模型 + 执行模型）。
- 新增：任务发布模块——任务卡片（任务目标/任务要求/任务附件/智能体线路/报告文件名/任务校验清单）→ 提交 → 按线路执行 → 任务列表/详情。
- 新增：平台任务线路占位入口（本期不开发 reasoning 执行逻辑，仅保留入口）。
- 修改：智能体配置从「单模型」改为「多线路模型配置」。
- 移除：主对话（SSE 流式对话接口 + 前端聊天窗口）**BREAKING**。

## 关联文档

- PRD：`dev_docs/02-PRD需求/PRD-08-AI助手.md`
- ARCH：`dev_docs/03-设计与架构/ARCH-08-AI助手.md`
- 设计笔记：`dev_docs/项目笔记/AgentScope/多智能体编排-最终骨架设计.md`

## Capabilities

### New Capabilities

- `ai-agent-routes`: 智能体多线路模型配置（控制设备/平台任务各含规划 + 执行模型，配置完显示在平台助手栏）
- `ai-task-publishing`: 任务发布（任务卡片提交 → 按线路分发执行 → 任务列表/详情）

### Modified Capabilities

（无——现有 spec 不覆盖 AI 助手能力，本次均为新增能力）

## Impact

- 后端 `apps/ai_assistant/`：删 `chat_views.py`（SSE）；`AIAgent` 增 `route_configs`、`AITask` 增任务字段（+ migration）；`serializers.py`/`api.py`/`views_drf.py`/`urls.py` 配套；新增任务提交端点与线路分发（复用 `plan()` + `build_agent()`）。
- 前端 `frontend/src/modules/ai-assistant/`：删聊天窗口；配置页多线路改造；新增任务发布模块（组件/composable/api/路由）。
- 测试：删对话接口测试；新增任务提交 + 智能体多线路配置测试。
- 跨模块：`dashboard`/`evaluator` 若读 `ai_agents` 扁平模型字段需同步；SSE 为全平台唯一流式通道，删除需确认无其它模块复用。
