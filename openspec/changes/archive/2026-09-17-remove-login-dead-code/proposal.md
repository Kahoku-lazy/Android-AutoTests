## Why

登录模块前端静态排查（2026-09-17，逐符号 grep + 依赖可达性 + 真实渲染）确认了一批**零消费方**的代码与资源。归档变更 `2026-09-16-redesign-login-hand-drawn-hero` 的 1.1 只摘掉了登录页对 `AnimalFace` 的**引用**，组件文件与其配套静态资源却留在仓库里；此外还有死导出、死字段、死 CSS 变量与永不命中的类名。它们不影响运行，但持续误导阅读者（`AnimalFace.vue` 的注释至今写着「LoginView 贴纸板用」），并让 `--app-stat-text` 这类令牌以「有人在用」的错觉存活。

## What Changes

按设计层与代码层分组删除（详见 tasks.md）：

1. **设计层死资源**：删除孤儿组件 `views/components/AnimalFace.vue`（129 行、5 个动物 SVG、3 个局部令牌）；删除孤儿静态资源 `public/login/login-hero-01.jpg` 及随之变空的 `public/login/` 目录；清理 `frontend/tests` 中指向已不存在的 `useHeroImage` 的失效条目。
2. **布局/样式层**：删除死 CSS 变量 `--login-panel-width`（`LoginView.style.css`，同文件另 3 个局部变量仍在用）；删除 `LoginErrorOverlay` 上的无效类名 `wb-btn`（登录页不挂 `.wb-shell`，该规则永不命中）。
3. **逻辑/类型层**：删除死导出 `token-storage.getActiveUsername()` 与 `router.ts` 对应的未使用 import；删除死字段 `LoginViewState.accountList`（接口声明与返回值，无任何消费方）；收敛 6 处冗余 `export` 修饰。

**Non-goals（本变更明确不做）**：

- **不修** `.meeting-doodle` 的 `transform: rotate(1.2deg)` 导致 L5 错误浮层被囚在卡片内的问题。该问题经渲染实测与对照实验证实（`.el-overlay` 实测 424×403 vs 注入 `transform:none` 后 1440×900），但属**行为变更**，不属删除范畴，另开变更处理。
- **不动** `shared/styles/tokens.css` 的 `--app-stat-text`。该令牌全前端 0 消费，但其退役应走既有令牌通道/退役流程，不在本变更顺手删除。
- **不动** `frontend/tests/device-pool/**` 中对 `getActiveUsername` 的 mock：多余键无害，且属他模块范围。
- **不动** `frontend/dist/**`：构建产物，下次构建自然收敛。

## 关联文档

- `openspec/specs/frontend-login-hand-drawn-hero/spec.md` —— 其既有需求「系统 MUST NOT 在 Hero 中渲染动物贴纸板」与 Scenario「Animal sticker board is removed」正是本变更要落实的对象；本变更使**实现补齐到既有需求**，而非改变需求
- `frontend/AGENTS.md` —— 分层纪律、共享件清单、字号与令牌约束（确认待删项不属共享件清单）
- 无新增 PRD/ARCH：纯死代码与死资源清理，无业务需求变化

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯删除且行为等价：`.openspec.yaml` 已设 `skip_specs: true`。待删项均为零消费方的代码与资源，删除后 `/login` 的可见行为、认证流程与 API 契约不变；`frontend-login-hand-drawn-hero` 的需求本就要求「无动物贴纸板」，本变更是让实现与既有需求一致，不产生需求 delta。

## Impact

- 前端源码：`views/components/AnimalFace.vue`（删除整文件）、`views/LoginView.logic.ts`、`views/LoginView.style.css`、`views/components/LoginErrorOverlay.vue`、`views/components/{LoginCard,RegisterCard,AccountSwitchPrompt}.vue`、`shared/auth/token-storage.ts`、`shared/types/auth.ts`、`router.ts`
- 静态资源：`frontend/public/login/`（删除目录）
- 测试说明文档：`frontend/tests/PRIORITY_TEMPLATE.md`、`frontend/tests/login/p2/README.md`
- 后端 / API / 数据库 / 依赖：无
- 验证范围：`npm run typecheck`、`npm run lint:styles`、`vitest --project login/p0` 与 `login/p1`、登录页三态实拍复核
