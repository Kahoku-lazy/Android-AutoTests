## 1. 设计层死资源（组件与静态文件）

- [x] 1.1 删除 `frontend/src/views/components/AnimalFace.vue` 整文件（129 行）。验证：全仓 `animal[-_]?face` 命中数 0（排除 openspec 归档与本 bundle）
- [x] 1.2 删除 `frontend/public/login/login-hero-01.jpg` 及随之变空的 `frontend/public/login/` 目录。验证：`login-hero` / `useHeroImage` / `heroImage` 全仓命中数 0；`Test-Path frontend/public/login` = False（`frontend/dist/login/` 为构建产物，按 Non-goals 不动）
- [x] 1.3 清理失效文档条目：删 `frontend/tests/PRIORITY_TEMPLATE.md`（P2 表行）与 `frontend/tests/login/p2/README.md`（P2 清单行）中的 `useHeroImage`。验证：`frontend/tests` 内 `useHeroImage` 命中数 0

## 2. 布局 / 样式层死代码

- [x] 2.1 删 `frontend/src/views/LoginView.style.css` 的 `--login-panel-width: 380px;`。验证：`--login-panel-width` 全前端命中数 0；`--login-rule` / `--login-margin-line` / `--login-dash` 三个在用局部变量保持不变
- [x] 2.2 删 `frontend/src/views/components/LoginErrorOverlay.vue` 中 el-button 的 `class="wb-btn"`。验证：该文件 `wb-btn` 命中数 0；该组件 diff 仅此 1 行（`git diff` 确认 1 deletion）

## 3. 逻辑 / 类型层死代码

- [x] 3.1 删 `frontend/src/shared/auth/token-storage.ts` 的 `getActiveUsername()`；`frontend/src/router.ts` import 收敛为仅 `getToken`。验证：`frontend/src` 内 `getActiveUsername` 命中数 0（`frontend/tests/device-pool/**` 的 mock 按 Non-goals 不动）
- [x] 3.2 删 `LoginViewState.accountList` 声明与返回值；保留 `useViewStateMachine(auth.accountList, …)` 对 `useAuthPool` 返回值的直接使用。验证：`LoginView.logic.ts` 内仅剩 1 处 `accountList`（即该保留行）；`LoginView.hero.spec.ts` 的 `useLoginView` mock 本就未提供该字段
- [x] 3.3 收敛 6 处冗余 `export`：`AccountTokens` / `AuthTokenData` / `AuthRefreshData`（`shared/types/auth.ts`）与 `LoginCardProps` / `RegisterCardProps` / `AccountSwitchPromptProps`。验证：先确认 `frontend/tests` 对这 6 个类型 import 数为 0，改后 `export interface (…)` 命中数 0

## 4. 门禁与复扫

- [x] 4.1 复扫：1.1–3.3 每项符号/路径逐一 grep，残留命中数为 0（`accountList` 仅剩有意保留的 1 处）；`npm run lint:styles` 通过（exit 0，style-gates 四批全过）
- [x] 4.2 前端门禁：`npm run typecheck` = 2（30 个错误）——**全部为既有问题，与本变更无关**：错误分布于 `tests/dashboard/p0/useDashboardStats.spec.ts`(12)、`tests/dashboard/p1/DashboardView.logic.spec.ts`(8)、`tests/dashboard/p1/ModuleNavigator.spec.ts`(7)、`src/modules/case-manager/components/ProjectTree.vue`(3)，这 4 个文件在工作区中均已是 modified 状态；错误码为 TS2353/TS2322/TS2339/TS2352，**无一条** `no exported member` / `Cannot find module`，且命中 `AnimalFace`/`AccountTokens`/`getActiveUsername` 等本次删除符号的报错数为 **0**。`vitest --project login/p0 --project login/p1` = 61 passed / 3 failed，失败全部集中在 `tests/login/p1/LoginErrorOverlay.spec.ts`（`.el-dialog` / `.el-overlay` 找不到）；已做 A/B 对照：把该组件还原为 `git show HEAD:` 版本后同样 **3 failed | 3 passed**，证明为既有失败（EP/VTU DOM 漂移），非本变更引入
- [x] 4.3 登录页实拍复核：重跑 `temps/login-layer-map/login-layer-map.cjs` —— 26 个设计层元素全部命中（measuredA=26 / B=6 / 覆盖层=4）、login / register / switchPrompt 三态均可渲染（states=3）、二次校验 0 控制台报错、0 孤儿选择器；产物 HTML 字节数 460045 与删除前完全一致，说明页面渲染无可见变化
