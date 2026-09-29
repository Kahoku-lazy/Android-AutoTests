## MODIFIED Requirements

### Requirement: Evaluator product surface is gone
系统 MUST NOT 在 AI 助手侧栏或路由表中暴露评测中心。访问已移除路径时 MUST 不渲染评测工作台。AI 助手侧栏子项 SHALL 仅为平台小助手、AI工具箱（知识库子项已由 `knowledge-base-retirement` 下线）。

#### Scenario: Sidebar has three AI children

<!-- 场景名沿自变更前：知识库子项已由 knowledge-base-retirement 下线，本场景改为守住「侧栏只剩平台小助手与 AI工具箱」这一不变量 -->

- **WHEN** 已登录用户查看侧栏「AI 助手」分组
- **THEN** 子项为「平台小助手」「AI工具箱」
- **AND** 既没有「评测中心」，也没有「知识库」

#### Scenario: Evaluator route is not registered
- **WHEN** 检查前端路由表
- **THEN** 不存在 path `/ai-assistant/evaluator`
