## Why

登录页的虚线**不是登录页自己的**：`LoginView.style.css` 把 `--login-dash` 指向共享令牌 `--comp-sidebar-dash`（侧栏与主区的分隔线）。后续要把全站虚线换成铅笔实线时，改这一个侧栏令牌会**静默把登录页一起改掉**，而登录页正是这次唯一要保留虚线的页面。同一文件里还有 3 处 `2.5px` 描边宽度字面量、1 处 `margin: -var(...)` 的非法负值写法。

先把登录页的线型与描边宽度收回到它自己的作用域，全站线型切换才有安全的落点。

## What Changes

- **新增 T0 描边宽度原子** `--size-stroke-sketch: 2.5px`（`shared/styles/tokens.css`）。全站已有 7 处 `2.5px` 描边字面量（本单只收敛登录页 3 处），先按"规格原子唯一登记"口径登记。
- **登录页自持线型**：在 `.login-page` 作用域声明 `--login-line: dashed` 与组合令牌 `--login-border: var(--size-stroke-sketch) var(--login-line) var(--ink)`；删除 `--login-dash: var(--comp-sidebar-dash)` 这条跨边界借用。
- `.hero-cta--ghost` 的 `border-style: dashed` 改取 `var(--login-line)`，使登录页的"留虚线"决定只有一处出口。
- **修正令牌用法缺陷**：`auth-form-card.css` 的 `margin: -var(--app-space-sm)` 是非法 CSS（`var()` 不能直接取负），改为 `calc(-1 * var(--app-space-sm))`。
- **Non-goals（本次不做）**：
  - **不改任何可见外观**：虚线仍是虚线、描边宽度仍是 2.5px、颜色仍是墨色。验收以"改前改后像素级一致"为准。
  - 不改侧栏、卡片、弹窗、表纸的线型——那是下一步的全站切换。
  - 不动阴影、圆角、字号、间距刻度。
  - 不令牌化登录页的一次性装饰几何（胶带 72px、圆点 10px、横线本 31/32px、Hero 栅格 1120px）。
  - 不动登录业务契约、组件结构与路由。

## 关联文档

PRD-00（登录模块）——登录页视觉归属该需求编号。设计系统的令牌登记口径由 `openspec/specs/frontend-l0-design-tokens` 承载，无独立 PRD 编号；本次不改任何登录业务行为。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-l0-design-tokens`: 新增「描边宽度与线型以令牌登记」要求——登记手绘描边宽度原子，并要求线型（`dashed` / `solid`）由其消费边界以令牌自持，禁止跨边界借用决定。
- `frontend-login-hand-drawn-hero`: 新增「登录页线型由登录页作用域令牌决定」要求——登录页保留虚线是登录页自己的登记，全站线型变化不得波及。

## Impact

- `frontend/src/shared/styles/tokens.css`：新增 1 个 `--size-*` 原子。
- `frontend/src/views/LoginView.style.css`：3 处描边改引用（`.hero-cta`、`.hero-cta--ghost`、`.meeting-doodle`），删除 1 条借用声明。
- `frontend/src/views/styles/auth-form-card.css`：1 处描边改引用 + 1 处非法负值修正。
- 门禁：`cd frontend && npm run lint:styles`（字号下限 / token 唯一性与引用完整性 / 几何尺度）与 `npx vue-tsc --noEmit`。
- 无后端、API、数据表改动；无依赖新增。
