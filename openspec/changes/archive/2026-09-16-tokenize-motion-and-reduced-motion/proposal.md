## Why

组件级 CSS 动效大面积绕过令牌：实测 `60 处` `transition` / `animation` 声明使用裸时长（`0.12s` 21 处、`0.15s` 11 处、`0.2s` 13 处、`0.1s` 1 处）或裸 `ease`（14 处），其中 `0.12s` / `0.15s` / `ease` 与已登记令牌**取值完全相同**，属纯令牌绕过；`0.2s` / `0.1s` 不在刻度上。同时 `prefers-reduced-motion` 只覆盖 12 个文件，而含 transform 过渡的文件有 10 个、其中 7 个缺降级块 —— 用户启用「减少动效」时仍有位移/旋转/缩放动画在播放。`frontend-motion` 目前只约束路由过渡与 JS 编排动效，未覆盖组件级 CSS 动效。

## What Changes

- 令牌化：`0.12s` / `.12s` → `var(--app-duration-fast)`；`0.15s` / `.15s` → `var(--app-duration)`；裸 `ease` → `var(--app-ease)`（三者与令牌**严格同值**，零视觉变化）；`0.1s` → `var(--app-duration-fast)`、`0.2s` → `var(--app-duration-slow)`（微变 +0.02s / +0.05s）
- 补降级：为 7 个含 transform 过渡且缺守卫的文件新增 `@media (prefers-reduced-motion: reduce)` 块
- 登记例外：骨架 shimmer `1.4s` 与状态脉冲 `1.5s` 为无限循环装饰动画，保留固有周期（三者均已有降级）
- 删除一处因替换产生的自引用兜底 `var(--app-duration, var(--app-duration))`
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §5.5 与 §八·批次 B
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 2 · `tokenize-motion-and-reduced-motion`
- 既有要求：`openspec/specs/frontend-motion/spec.md`（本变更把同一契约从路由过渡扩展到组件级 CSS 动效）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-motion`：新增要求「组件级动效取自令牌并提供 reduced-motion 降级」

## Impact

- 令牌化：28 个文件（`modules/**` 与 `shared/**` 的 `.vue` / `.css`）
- 降级：`modules/ai-assistant/components/ToolboxPanel.style.css`、`modules/report-generator/{CaseBreakdown,ReportDetail,TaskReport}.vue`、`modules/workflow/components/WorkflowFileBrowser.vue`、`shared/components/AppSidebar.style.css`、`style.css`
- 观感变化：默认渲染下 `0.1s→0.12s` 与 `0.2s→0.25s` 的过渡略慢；启用「减少动效」时上述 7 处不再播放位移/旋转/缩放
- 不影响：颜色/边框色过渡（沿用同一时长令牌）、路由过渡、`shared/animations.ts` 的 JS 编排动效、骨架 shimmer 与脉冲周期

## 登记为后续变更的输入（本变更不做）

- `1.4s` / `1.5s` 两个无限装饰动画周期的令牌化（需先确定是否纳入 `--app-duration-*` 刻度）→ 待定