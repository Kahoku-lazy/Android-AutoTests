## Why

`frontend/src/shared/styles/motion.css` 已定义路由切换过渡 `.fade-slide-*`，但主区 `router-view` 从未接线，全前端零消费方，路由切换实际是硬切；同时该实现硬编码 `0.28s ease`，与既有的 `--app-duration-slow: 0.25s` / `--app-ease` 令牌口径冲突，且 `motion.css` 与 `shared/animations.ts` 都没有 `prefers-reduced-motion` 降级。项目动效规范（`.agents/skills/doodle-craft/references/tokens.md` §1.9）已把「路由切换 0.25s」列为必含项，本变更补齐这一未完成项并统一动效口径。

## What Changes

- 在 `App.vue` 的主区 `router-view` 接线路由切换过渡：`<transition>` 包住 `<keep-alive>`，`key` 仍用 `route.path`
- 过渡实现对齐设计令牌：时长用 `--app-duration-slow`、缓动用 `--app-ease`，移除 `0.28s ease` 与位移量裸值
- 为路由过渡补 `prefers-reduced-motion: reduce` 降级：用户禁用动效时不做位移/淡入，直接切换
- 为 `shared/animations.ts` 的 animejs 编排动效补 reduced-motion 短路：禁用时跳过动画、直接落到终值
- **BREAKING**：无。纯前端壳层视觉行为，不涉及接口、路由表、鉴权或数据
- 不改侧栏结构，不改模块业务布局与组件

## 关联文档

- 主题动效规范：`.agents/skills/doodle-craft/references/tokens.md` §1.9 动效（路由切换 0.25s / `--app-duration-slow` / `--app-ease`）
- 前端 L0/L1 布局与滚动口径：`frontend/AGENTS.md`（视口固定 + 内层滚动；L1 主区职责）
- 前置同域变更：`openspec/changes/l0-paper-doodle-bg/`（主区视觉层，已完成，本变更不改其行为）
- 说明：`dev_docs/文档编号对照表.md` 不存在，`dev_docs/` 下无对应 PRD/ARCH/UI 编号文档；本变更属视觉主题口径补齐，不改业务接口，故不引用编号文档

## Capabilities

### New Capabilities

- `frontend-motion`: 前端动效的可见行为与降级契约 —— 路由切换过渡的存在与时长口径，以及 CSS 过渡与 JS 编排动效在用户禁用动效时的降级行为

### Modified Capabilities

（无；`openspec/specs/` 下暂无既有前端动效能力）

## Impact

- 前端壳层：`frontend/src/App.vue`（主区 `router-view` 接线）、`frontend/src/shared/styles/motion.css`（过渡实现 + a11y 降级）、`frontend/src/shared/animations.ts`（animejs reduced-motion 短路）
- 技能口径：`.agents/skills/doodle-craft/references/tokens.md` §1.9（如需显式写明 reduced-motion 降级要求）
- 测试范围：`frontend/tests/`（现有单测不覆盖路由过渡；若抽出 reduced-motion 判定工具需补单测），`cd frontend && npm run typecheck`
- 不影响：API、鉴权、路由表、各模块业务组件与页面布局、侧栏结构
