## MODIFIED Requirements

### Requirement: Evaluator product surface is gone

系统 MUST NOT 在 AI 助手侧栏或路由表中暴露评测中心。访问已移除路径时 MUST 不渲染评测工作台。AI 助手侧栏 SHALL 只有一个入口「AI 助手」，MUST NOT 再出现任何子项（「平台小助手」「AI工具箱」「知识库」「评测中心」均不作为侧栏子项）。

#### Scenario: Sidebar has three AI children

<!-- 场景名沿自变更前：侧栏子项已全部收起，本场景改为守住「AI 助手只有单一入口」这一不变量 -->

- **WHEN** 已登录用户查看侧栏「AI 助手」
- **THEN** 它是指向 `/ai-assistant/agents` 的单一入口，没有展开子项
- **AND** 既没有「评测中心」，也没有「知识库」「AI工具箱」

#### Scenario: Evaluator route is not registered

- **WHEN** 检查前端路由表
- **THEN** 不存在 path `/ai-assistant/evaluator`
