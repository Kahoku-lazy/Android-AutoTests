## Purpose

约定评测中心从产品与 HTTP 面下线：不再提供侧栏入口与 `/api/evaluator/*`，题库/运行表删除，Django App 仅作为卸表迁移壳保留，避免残留可调用的评测能力。

## ADDED Requirements

### Requirement: Evaluator product surface is gone
系统 MUST NOT 在 AI 助手侧栏或路由表中暴露评测中心。访问已移除路径时 MUST 不渲染评测工作台。AI 助手侧栏子项 SHALL 仅为平台小助手、AI工具箱、知识库。

#### Scenario: Sidebar has three AI children
- **WHEN** 已登录用户查看侧栏「AI 助手」分组
- **THEN** 子项为「平台小助手」「AI工具箱」「知识库」，且没有「评测中心」

#### Scenario: Evaluator route is not registered
- **WHEN** 检查前端路由表
- **THEN** 不存在 path `/ai-assistant/evaluator`

### Requirement: Evaluator HTTP API is unmounted
系统 MUST NOT 再把 `apps.evaluator.urls` 挂到 `/api/evaluator/`。对该前缀的请求 SHALL 得不到评测业务视图（题库 / 运行 / 框架 / KB 自测）。

#### Scenario: Evaluator include is absent
- **WHEN** 检查根 URL 配置
- **THEN** 不存在 `include("apps.evaluator.urls")`

### Requirement: Evaluator tables are dropped
`ev_question_banks`、`ev_questions`、`ev_runs`、`ev_results` SHALL 由 Django 迁移删除。`apps.evaluator` MAY 仍列在 `INSTALLED_APPS` 中，但 MUST NOT 再声明这些 Model。

#### Scenario: Models module has no eval tables
- **WHEN** 检查 `apps.evaluator.models`
- **THEN** 不定义 `QuestionBank`、`Question`、`EvalRun`、`EvalResult`
