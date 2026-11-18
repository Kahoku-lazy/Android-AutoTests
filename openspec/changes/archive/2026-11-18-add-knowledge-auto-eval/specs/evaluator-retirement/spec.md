## MODIFIED Requirements

### Requirement: Evaluator product surface is gone
系统 MUST NOT 在 AI 助手侧栏或路由表中暴露评测中心。访问已移除路径时 MUST 不渲染评测工作台。AI 助手侧栏子项 SHALL 仅为平台小助手、AI工具箱（知识库子项已由 `knowledge-base-retirement` 下线）。本能力的退役范围是旧评测中心（题库 / 运行 / 框架 / KB 自测）；知识页内嵌的检索评测（`knowledge-auto-eval`）不属于评测中心：其端点位于 `/api/knowledge-search/evaluations/`、表用 `ks_eval_*` 前缀、不占用 AI 助手侧栏入口。

#### Scenario: Sidebar has three AI children

<!-- 场景名沿自变更前：知识库子项已由 knowledge-base-retirement 下线，本场景改为守住「侧栏只剩平台小助手与 AI工具箱」这一不变量 -->

- **WHEN** 已登录用户查看侧栏「AI 助手」分组
- **THEN** 子项为「平台小助手」「AI工具箱」
- **AND** 既没有「评测中心」，也没有「知识库」

#### Scenario: Evaluator route is not registered
- **WHEN** 检查前端路由表
- **THEN** 不存在 path `/ai-assistant/evaluator`

#### Scenario: KB embedded eval is not the evaluator center
- **WHEN** 知识页自动评测运行
- **THEN** 其端点都在 `/api/knowledge-search/evaluations/` 之下
- **AND** `/api/evaluator/*` 仍返回 404
- **AND** AI 助手侧栏不出现评测中心入口