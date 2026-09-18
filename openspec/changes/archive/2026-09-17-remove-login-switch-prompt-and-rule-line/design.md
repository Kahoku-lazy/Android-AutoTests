## Context

牵连面（静态扫描结果）：

| 项 | 命中 |
|---|---|
| `switchPrompt` / `AccountSwitchPrompt` | 源码 6 处、测试 8 处、文档 3 处 |
| `onSwitchToExisting` / `onAddNewAccount` | 源码 8 处、测试 5 处 |
| `?add=1` | `tools/register_cases/*.json` 12 个 + `tools/login_cases/*.json` 1 个 + `tools/generate_report.py:80` |
| `--login-margin-line` | 仅 `LoginView.style.css` 自身（声明 + ::before 消费） |
| `activeAccount` | `LoginView` 侧仅服务切换提示卡；`useAuthPool` / `AppSidebar` 侧是账号菜单在用（**不动**） |

关键事实：`openspec/specs/` 下**没有任何非归档 spec 提到 switchPrompt**（`grep` 命中 0），因此本变更是「新增一条需求把两态定下来」，而不是修改既有需求。

## Goals / Non-Goals

**Goals**：登录页只剩 login / register 两态；去掉与横线纸面重复的粉红竖线；清干净因此产生的死代码。

**Non-Goals**：不动路由守卫的 `?add=1` 放行、不动 `tools/` 下 13 个 E2E 用例、不动多账号能力与侧栏账号菜单。

## Decisions

**D1：保留 `router.ts` 的 `?add=1` 放行，不视为本变更的清理对象。**

`if (token && to.path === '/login' && !to.query.add) return '/dashboard'` 里的 `!to.query.add` 确实是为「添加新账号」流程引入的，但**现在它是 13 个既有 E2E 用例的入口**：`tools/register_cases/*.json`（12 个）与 `tools/login_cases/*.json`（1 个）都以 `http://localhost:5173/login?add=1` 打开页面。删除该放行会让这些用例在已登录的浏览器里被重定向到 `/dashboard`，整批失效。

取舍：UI 侧不再有任何入口写入 `?add`，该分支成为「脚本/手动可达」的入口。保留它 = 保住既有用例；删除它 = 本变更顺带打掉一批回归资产。选保留，并在 proposal 里登记为 Non-goal。

**D2：`useViewStateMachine` 保留为独立 composable，只瘦身不合并。**

删掉账号池探测后它只剩 `viewState` + `switchMode` 约 12 行，并入 `LoginView.logic.ts` 也说得通。但合并会：① 删掉一个有独立 P0 spec 的可测单元；② 让 `login/p0/useViewStateMachine.spec.ts` 无处安放。按「只碰必须碰的」，只删该删的入参与函数。

**D3：连带删除 `LoginViewState.activeAccount`，入参与返回值一起收。**

`activeAccount` 在 `useLoginView()` 的消费者里**只有** `LoginView.vue` 一处，且只用于喂给 `AccountSwitchPrompt`。切换提示卡删除后它即死代码，故从接口与返回值中移除（与上一个变更删 `accountList` 同一口径）。注意 `useAuthPool` 自己的 `activeAccount` 仍被 `AppSidebar` 消费，**不动**。

**D4：粉红边线连同 `--login-margin-line` 令牌一起删。**

删掉 `.login-page::before` 后 `--login-margin-line` 全仓命中数为 0（仅剩声明本身），属「无人消费的模块私有变量」，与该变量的 3 个兄弟（`--login-rule` / `--login-dash` 仍在消费）不同。一并删除，避免留下一条只为死规则存在的令牌。

**D5：本变更必须重跑设计层地图产物。**

`frontend/AGENTS.md` §设计层地图产物 第 1 条把「改 `LoginView.vue` / `LoginView.style.css` 等 9 个文件后必须重跑」写成硬要求，本变更正好命中其中 8 个。产物需同步：三态 → 两态（C 节）、去掉粉红线相关注释（A 节与图例第 1 行）。这正是该规则第一次被实际触发。

## Risks / Trade-offs

- [已登录用户访问 `/login` 的体验变化] → 由「先看切换提示卡」变为「直接看登录表单」；这是本次明确要求的行为。侧栏账号切换入口不受影响
- [`tools/` 用例描述文案变陈旧]（仍写「跳过已登录账号切换提示」）→ 功能不受影响（`?add=1` 仍放行）；已在 Non-goals 登记，不顺手改生成器措辞
- [删除 `AccountSwitchPrompt.spec.ts` 会让 login/p1 少 3 条用例] → 预期内：被测组件已删除；总体用例数下降不代表覆盖退化，`LoginView.hero.spec.ts` 会补一条「已有账号也直接显示表单」的断言来守住新需求
- [地图产物忘记重跑] → 由 `--check` 兜住：生成器自身在受管清单内，改 `REGIONS` 未重跑会被判过期

## Migration Plan

无数据迁移、无路由变化。回滚 = 还原被删文件与两处样式，并按需回滚 spec delta。

## Open Questions

`tools/generate_report.py:80` 与 13 个用例 JSON 里「跳过已登录账号切换提示」的描述已不符合现状，是否单独开变更修生成器措辞并重生成？
