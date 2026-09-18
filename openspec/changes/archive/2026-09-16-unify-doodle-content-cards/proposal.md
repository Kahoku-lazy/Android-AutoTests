## Why

AI 助手的小助手卡（`AgentRouteCard`）与任务卡（`TaskBoard` 内条目）仍是实线不对称圆角 + 模块私有按钮，与 hand-drawn-doodle 模版的 deco-card / Do 便利贴 / `#comp-buttons` 两套语言。后续其它模块内容卡若各自抄样式会双实现。需要共享内容卡壳与涂鸦按钮，先在 AI 助手落地，其它模块复用同一 API。

## What Changes

- 新增共享 `DoodleNote.vue`：`variant="note"`（胶带 deco-card，小助手）与 `variant="sticky"`（Do 便利贴，任务；失败可切 Dont 红底）
- 新增共享 `DoodleBtn.vue`：`tone="danger" | "teal" | "yellow"`（删除红 / 校验与详情青绿 / 配置黄）
- AI 助手 `AgentRouteCard`、`TaskBoard` 任务条目改为薄包装共享件；删除仍走 `ConfirmButton`，外观用 `DoodleBtn` danger
- 同步 doodle-craft 组件规格与 `frontend/AGENTS.md` 共享件说明
- 补齐单测
- **BREAKING**：无 API/路由破坏；视觉为有意换皮。本轮不改 `KpiCard`、`AppCard`、页头 `wb-btn`

## 关联文档

- 视觉模版：`temps/hand-drawn-doodle-sidebar.html`（`#page-decorations` Tape Strip、`#page-rules` sticky.do、`#comp-buttons`）
- 方案原型：`temps/prototype-doodle-content-cards.html`
- 说明：无对应 PRD/ARCH 编号文档；属前端共享视觉组件统一，不改业务接口

## Capabilities

### New Capabilities

- `frontend-doodle-content-card`：共享内容卡（note / sticky）与涂鸦按钮（danger / teal / yellow）的可见行为、装饰、状态底色与 a11y

### Modified Capabilities

（无）

## Impact

- 前端共享：`frontend/src/shared/components/DoodleNote.vue`、`DoodleBtn.vue`
- AI 助手：`AgentRouteCard.vue`、`TaskBoard.vue`（及 `ConfirmButton` 外观衔接）
- 技能与文档：`.agents/skills/doodle-craft/references/components.md`、`frontend/AGENTS.md`
- 测试：相关 vitest、`cd frontend && npm run typecheck`
- 不影响：后端 API、鉴权、路由表、KPI 卡、AppCard 内容块、页头按钮
- 明确非本轮：设备卡 / 用例卡 / 报告条目卡的批量换皮（共享件就绪后可跟）
