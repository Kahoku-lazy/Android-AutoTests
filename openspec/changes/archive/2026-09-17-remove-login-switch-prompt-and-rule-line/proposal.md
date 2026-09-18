## Why

登录页有两处与当前定位不符的东西：

1. **账号切换提示态（`switchPrompt`）**：本地已有账号时，登录页会先弹一张「检测到已登录账号 / 切换到 xxx / 添加新账号」的提示卡，而不是直接给表单。这是一个中间态页面，把「我只是想登录」的路径拉长了一步；其两个动作（切到 dashboard、带 `?add=1` 重载）也都可以由既有入口替代——账号切换本来就在侧栏有独立入口，`?add=1` 则是脚本/手动可达。
2. **左侧粉红边线**（`.login-page::before`，`left: --app-space-2xl`）：横线笔记本纸面已经由 `.login-page` 的重复渐变表达，这条竖线是额外的装饰，去掉后纸面更干净。

## What Changes

- **删除 `switchPrompt` 视图态**：`ViewState` 收敛为 `"login" | "register"`；删除 `views/components/AccountSwitchPrompt.vue` 与 `useViewStateMachine` 里的账号池探测（`onMounted` + `accountList`）、`onSwitchToExisting`、`onAddNewAccount`；左栏「登录 / 注册」CTA 恒可见（去掉 `v-if="viewState !== 'switchPrompt'"`）
- 随之成为死代码的一并清理：`LoginViewState.activeAccount`（只服务切换提示卡）、`useViewStateMachine` 不再需要的 `accountList` 入参
- **删除左侧粉红边线**：删除 `.login-page::before` 规则（含 `≤768px` 的 `left` 覆写）与随之无人消费的 `--login-margin-line` 令牌
- 同步测试：删 `AccountSwitchPrompt.spec.ts`；`useViewStateMachine.spec.ts` / `LoginView.hero.spec.ts` 去掉切换提示相关用例与 mock；清理指向已删文件的注释与 `PRIORITY_TEMPLATE.md` 登记行
- 按 `frontend/AGENTS.md`「设计层地图产物」规则，**同步重跑** `temps/login-layer-map/`（三态 → 两态、去掉粉红线注释、`--check` 归零）

**Non-goals**：
- **不动 `router.ts` 的 `?add=1` 放行**：`tools/register_cases/*.json` 与 `tools/login_cases/*.json` 共 **13 个既有 E2E 用例**都以 `/login?add=1` 进入表单，删掉该放行会让它们全部被守卫重定向到 `/dashboard`
- 不改 `tools/` 下那 13 个用例里「跳过已登录账号切换提示」的旧描述文案（属生成器措辞，另行处理）
- 不动多账号能力本身：`useAuthPool` 的 `switchAccount` / `logoutAccount` 与侧栏账号菜单保持不变

## 关联文档

- `openspec/specs/frontend-login-hand-drawn-hero/spec.md` —— 本变更为其**新增一条需求**：登录页只有 login / register 两态，不再有账号切换提示态
- `frontend/AGENTS.md` §设计层地图产物 —— 本变更触发该产物必须重跑
- `openspec/changes/archive/2026-09-16-redesign-login-hand-drawn-hero/` —— 其任务 2.2 曾要求「switchPrompt 态仍优先展示 AccountSwitchPrompt」，本变更反转该决定（该条只是任务、未进主 spec）
- 无新增 PRD/ARCH

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-login-hand-drawn-hero`: 新增需求「Login page has only login and register modes」——登录页视图态只有 login / register；已有账号时直接呈现表单，不再先显示切换提示

## Impact

- 前端源码：`views/LoginView.vue`、`views/LoginView.logic.ts`、`views/composables/useViewStateMachine.ts`、`views/LoginView.style.css`、`views/styles/login-card.css`、`shared/types/auth.ts`；删除 `views/components/AccountSwitchPrompt.vue`
- 测试：删除 `tests/login/p1/AccountSwitchPrompt.spec.ts`；改 `tests/login/p0/{useViewStateMachine,LoginView.hero}.spec.ts`、`tests/login/p1/LoginErrorOverlay.spec.ts`（注释）、`tests/PRIORITY_TEMPLATE.md`
- 证据产物：`temps/login-layer-map/`（按规则重跑）
- 路由 / 后端 / API / `tools/` E2E 用例：不改
- 验证范围：`npm run typecheck`、`npm run lint:styles`、`vitest --project login/p0 --project login/p1`、登录页实拍复核、`--check` 归零
