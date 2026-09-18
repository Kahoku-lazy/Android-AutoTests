## Purpose

定义 Django 与可替换 AI 引擎之间的进程内协议：Django 仅传入任务表单、三角色模型配置与工具清单，引擎完成「规划 → 执行 → 验收」并返回归一化结果；换框架只换引擎实现，Django 逻辑不变。

## ADDED Requirements

### Requirement: AiEngine 协议接口
AI 引擎 SHALL 暴露阻塞接口 `run(TaskRequest) -> TaskResult`；Django 经 `get_ai_engine(settings.AI_ENGINE)` 工厂获取引擎，引擎内部负责框架的异步装配与执行，Django 不感知框架内部实现。

#### Scenario: 调用引擎
- **WHEN** Django 调用 `get_ai_engine("agentscope").run(req)`
- **THEN** 引擎在进程内完成执行并返回 `TaskResult`，Django 无任何 `agent_scope`/`asyncio.run`/`AgentScope` 直接引用

### Requirement: TaskRequest 契约
Django SHALL 通过 `TaskRequest` 传入 `goal`、`route`、三角色模型配置（planner/executor/verifier，api_key 已解密）、工具清单（`tools`）、`max_loops` 及可选 `requirements`/`checklist`/`report_name`/`device_serial`/`user_id`。

#### Scenario: 组装请求
- **WHEN** 前端提交任务（`POST /api/ai/tasks/submit`）
- **THEN** `engine_adapter` 从 `AITask` 与 `route_configs`（解密后）组装 `TaskRequest`，模型 api_key 以明文传入引擎

### Requirement: TaskResult 归一化
引擎 SHALL 返回 `TaskResult`（`status`/`summary`/`completed`/`failed`/`log`/`usage`/`reason`）；两条线路（device_control / platform_task）结果同构，`summary` 落 `AITask.result`。

#### Scenario: 结果落库
- **WHEN** 引擎返回 `TaskResult`
- **THEN** Django 按 `status` 写 `AITask` 状态，`summary` 写 `result`（device_control 不再恒空）

### Requirement: 引擎零 apps 依赖
`ai_engines` SHALL 不 import `apps.*` 内部实现；业务工具经 `TaskRequest.tools` 注入，引擎只负责包装与调用。`ai_engines` 是唯一可触碰第三方 AI 框架的层。

#### Scenario: 工具注入
- **WHEN** 引擎需要平台工具
- **THEN** 工具函数由 Django 层注入（`TaskRequest.tools`），引擎不直接 import `apps` 业务模块

### Requirement: 引擎注册与 fail-fast
`get_ai_engine` SHALL 按 `AI_ENGINE_REGISTRY` 惰性加载引擎并进程内缓存；未注册名 / 不可导入 / 构建失败 SHALL 抛 `ConfigurationError`，不做静默回退。

#### Scenario: 未注册引擎
- **WHEN** `settings.AI_ENGINE` 为未注册名
- **THEN** `get_ai_engine` 抛 `ConfigurationError`（fail-fast）
