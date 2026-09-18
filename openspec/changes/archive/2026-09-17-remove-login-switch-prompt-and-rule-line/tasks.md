## 1. 删除 switchPrompt 视图态（源码）

- [x] 1.1 `shared/types/auth.ts`：`ViewState` 收敛为 `"login" | "register"`
- [x] 1.2 `useViewStateMachine.ts` 瘦身至 15 行：删 `accountList` 入参、`onMounted` 账号池探测、`onSwitchToExisting`、`onAddNewAccount`，以及随之无用的 `useRouter` / `useRoute` / `onMounted` / `ComputedRef` 导入；注释改「两态」
- [x] 1.3 `LoginView.logic.ts`：接口与返回值去掉 `activeAccount` / `onSwitchToExisting` / `onAddNewAccount`；调用改为 `useViewStateMachine(clearServerError)`
- [x] 1.4 `LoginView.vue`：删 import、三个解构项（`账号 & 视图状态` 注释收为 `视图状态`）、`<AccountSwitchPrompt>` 整块；`.hero__cta` 去掉 `v-if="viewState !== 'switchPrompt'"`（CTA 恒可见）；`meetingTitle` 注释去掉切换提示态措辞
- [x] 1.5 删除 `views/components/AccountSwitchPrompt.vue`
- [x] 1.6 `views/styles/login-card.css` 头注释去掉 `AccountSwitchPrompt`

## 2. 删除左侧粉红边线

- [x] 2.1 `LoginView.style.css`：删 `.login-page::before` 规则与 `≤768px` 的 `left` 覆写
- [x] 2.2 删 `--login-margin-line` 声明。验证：`login-margin-line` 全前端命中数 **0**；`--login-rule` / `--login-dash` 保留

## 3. 测试同步

- [x] 3.1 删除 `tests/login/p1/AccountSwitchPrompt.spec.ts`
- [x] 3.2 `useViewStateMachine.spec.ts` 重写为 2 条（初始 login / switchMode 清错切换）；删掉 switchPrompt、query.add、两个回调共 4 条；去掉 `clearAuthStorage` 与 `beforeEach`；顺带清掉该文件原有的重复文档注释
- [x] 3.3 `LoginView.hero.spec.ts`：类型联合去 `switchPrompt`；mock 去 `activeAccount` / 两个回调；删 `AccountSwitchPrompt` stub 与旧 switchPrompt 用例；**新增**「两个模式 CTA 恒可见，且不再有账号切换提示」（断言两个 CTA 存在、DOM 无「检测到已登录账号」「添加新账号」、切到 register 态后 CTA 仍双在）
- [x] 3.4 `LoginErrorOverlay.spec.ts` 两处注释不再引用已删的 `AccountSwitchPrompt.spec.ts`
- [x] 3.5 `PRIORITY_TEMPLATE.md`：删 AccountSwitchPrompt 登记行与「多账号 switchPrompt 全流程」E2E 候选行

## 4. 设计层地图产物同步（frontend/AGENTS.md 规则首次实际触发）

- [x] 4.1 `login-layer-map.cjs`：删 switchPrompt 复现块（空 token 注入 + `stateCard`）；REGION 1 说明改「横线本背景挂在它身上（左侧粉红边线已删除）」；REGION 6 由三态改「login / register 两态互斥」
- [x] 4.2 `template.html`：A 节 lead 去粉红竖线；C 节标题/meta/hint 由三态改两态。`README.md` 同步 3 处（目录行、自检截图行、关键结论）
- [x] 4.3 重新生成 + 自检：`measuredA`=26、`measuredB`=6、`states` 3 → **2**（`stateCaptions` = login 态 / register 态）、`notes`=[]、`legendRows`=30、`leftoverDeadSelectors`=0、`errs`=[]；`--check` exit 0（指纹 `dc6ceebd50c5`）
- [x] 4.4 顺带修正校验器里**我自己在 L5 修复那轮留下的陈旧断言**：`overlayFinding` 判的是 `body.innerHTML.includes('对照实验')`，而该措辞只存在于「未修复」分支（修复后为「对照复测」），导致它恒假。改为数据驱动的 `overlayCalloutTitle`（回带标题文本，缺失才为 null），现报「复验：L5 遮罩已覆盖整个视口」

## 5. 门禁与归档

- [x] 5.1 `npm run typecheck` = 30 例，与既有基线**同数**，登录相关 **0**；`npm run lint:styles` 通过（style-gates 四批）
- [x] 5.2 `vitest --project login/p0 --project login/p1` = **11 files / 58 tests 全通过**（原 12/65：删除 AccountSwitchPrompt.spec 3 条、删 useViewStateMachine 4 条、换掉 hero 1 条、新增 hero 1 条）
- [x] 5.3 实拍复核（`verify-canvas-0.png`）：左侧粉红竖线**已消失**（仅剩横线本横向纹路）、`登录/注册` 双 CTA 恒可见、登录卡正常渲染、页面上无切换提示内容、0 控制台报错
- [x] 5.4 `openspec validate` 通过后归档；主 spec `frontend-login-hand-drawn-hero` 同步新增需求「Login page has only login and register modes」
