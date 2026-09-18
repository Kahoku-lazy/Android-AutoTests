## Why

登录页 L5 错误浮层（`LoginErrorOverlay`）实际没有起到「阻塞型覆盖层」的作用：它的遮罩只盖住了右边那张便签卡，而不是整页。渲染实测 + 对照实验已定位根因：

- `.el-overlay` 实测 **424×403 @ (822,215)**，而视口是 **1440×900**
- 给 `.meeting-doodle` 注入 `transform: none` 后复测，`.el-overlay` 变为 **1440×900 @ (0,0)** —— 因果成立

根因：`LoginView.style.css` 给 `.meeting-doodle` 写了 `transform: rotate(1.2deg)`（手绘倾斜）。**带 transform 的祖先会成为 `position: fixed` 后代的包含块**，于是 `el-dialog` 的遮罩相对卡片解析。后果：遮罩只盖卡片、点遮罩关闭只在卡片内生效、弹层居中基准是卡片而非视口——不满足 `frontend-l5-overlay` 对「阻塞型覆盖层」的语义。

## What Changes

- `LoginErrorOverlay` 的 `el-dialog` 增加 `append-to-body`（Teleport 到 `body`），使遮罩跳出手绘倾斜卡片的包含块，恢复全视口覆盖与 `body` 居中
- 保留 `.meeting-doodle` 的 `transform: rotate(1.2deg)`：手绘倾斜是设计语言，**不靠删样式来绕开问题**
- 在 `.meeting-doodle` 的 transform 处与覆盖层组件注释里登记该约束，防止回归

**Non-goals**：不改浮层文案 / 宽度 / 关闭策略（纯展示浮层保持 Element Plus 默认的点遮罩关闭）；不改可见性绑定写法（维持 spec 要求的 `:model-value` + `@update:model-value`）；不引入自绘遮罩。

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md` —— 本变更为其**新增一条需求**（阻塞型覆盖层必须跳出被 transform 困住的包含块）
- `openspec/specs/frontend-login-hand-drawn-hero/spec.md` —— 登录页手绘 Hero 版式（含便签卡倾斜），本变更保证其视觉不变
- `frontend/AGENTS.md` §布局区域 L0–L5（L5 覆盖层归模块所有）
- 渲染实测证据与对照实验：`temps/login-layer-map/`（D 节 + `overlayRects` / `overlayControl`）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l5-overlay`: 新增需求「Blocking overlays escape transformed ancestors」——阻塞型覆盖层的遮罩 MUST 覆盖整个视口，挂载点位于带 transform 的容器内时 MUST Teleport 到 `body`

## Impact

- 前端：`frontend/src/views/components/LoginErrorOverlay.vue`（`append-to-body` + 注释）、`frontend/src/views/LoginView.style.css`（transform 处补约束注释，不改值）
- 后端 / API / 依赖 / 数据库：无
- 验证范围：登录页实拍复测（`.el-overlay` 尺寸 = 视口）、`vitest --project login/p1`、`npm run typecheck`
