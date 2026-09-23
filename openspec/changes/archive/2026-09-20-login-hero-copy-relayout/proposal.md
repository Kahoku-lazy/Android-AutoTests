## Why

登录页左侧 Hero 文案层级偏弱（标题 32px、描述两行 16px），与设计标注（截图红字）给出的品牌表达不一致；同时页面版本徽标仍停留在 v2.1，需要推进到 v3.0。本次只动左栏文案的内容、字号与对齐，以及版本徽标，不碰认证业务契约与右侧 Meeting doodle。

## What Changes

- 版本徽标：`v2.1` → `v3.0`（含 `aria-label`）。
- 移除左栏眉标整块（`p.hero__eyebrow`，文本「AI 自动化测试」）——需求 2 指定的 `//*[@id="app"]/div/main/div/div/div[2]/div[1]/p` 经真实渲染核对即该元素。
- 左栏文案改为 4 行，字号按设计标注（标注红字实测标题墨高 ≈50px、副行墨高 ≈31px，对齐当前品牌字体即为 48px / 32px）：
  1. `AI 自动化测试平台` —— 48px（新增刻度档）
  2. `实现让AI来做测试` —— 32px
  3. `让测试工作摆脱重复的劳动` —— 32px
  4. `专注于创造价值` —— 32px
- 左栏对齐：4 行文案与既有 CTA（`登录` / `注册 →`）统一居中于左侧文案块。
- 设计令牌：`tokens.css` 新增字号刻度 `--font-size-3xl: 48px` 及其别名 `--app-size-3xl`，并同步 `dev_docs/animal-island-ui-style` 令牌说明与技能 references。
- 右侧 Meeting doodle、登录 / 注册表单、错误覆盖层、认证流程 MUST 保持不变（无新接口、无字段变更）。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-登录模块.md`（登录模块范围；其中第 3 条明确页面级 UI 需求以 `frontend/src/views/AGENTS.md` 的「前端UI设计」为准，本变更的 UI 需求登记同源）
- UI 规范：`frontend/src/views/AGENTS.md`（登录页前端 UI 需求）· `frontend/AGENTS.md`（字号刻度硬性规范 §7）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-login-hand-drawn-hero`：Hero 左栏文案内容（4 行）、字号（48px / 32px）、对齐（文案与 CTA 居中）、版本徽标 `v3.0`、眉标移除。
- `frontend-l0-design-tokens`：字号刻度新增 48px 档（T0 原子 `--font-size-3xl` + 别名 `--app-size-3xl`），并明确该档的适用层级。

## Impact

- 前端页面：`frontend/src/views/LoginView.vue`（模板）、`frontend/src/views/LoginView.style.css`（样式）。
- 设计令牌：`frontend/src/shared/styles/tokens.css`。
- 文档与产物：`frontend/src/views/AGENTS.md`（UI 需求登记）、`frontend/AGENTS.md`（字号档位口径如有需要）、`temps/login-layer-map/`（登录页设计层标注图必须重跑）。
- 测试：`frontend/tests/login/p0/LoginView.hero.spec.ts` 及登录页相关用例。
- 无后端 / API / 数据库影响。
