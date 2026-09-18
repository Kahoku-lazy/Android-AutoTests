## 1. 文档化 L0 契约（frontend/AGENTS.md）

- [x] 1.1 布局区域表补 L0 行（视口 / 文档流 → `index.html` + `main.ts` + `style.css` 顶部 + `tokens.css` 的 `:root`，唯一允许写 html/body/#app 的位置）
- [x] 1.2 补规则 4「L0 不滚，滚动必须发生在容器里」：入口条件 + L0 收敛写入 + 运行时写入走 composable 并成对清理 + 新页面落在策略①/②内 + `flex:1` 配 `min-height:0`
- [x] 1.3 交叉引用自检模块路径 `shared/dev/scroll-guard.ts`

## 2. dev-only 滚动自检

- [x] 2.1 新增 `src/shared/dev/scroll-guard.ts`：`detectClippedChain`（纯判定）+ `installScrollGuard`（时机与去重）
- [x] 2.2 判定规则实现：能滚优先 → `hidden`/`clip` 判裁切 → `visible` 继续上冒 → 冒到 `body`/`html` 仍无人接手则报最先溢出的那一层
- [x] 2.3 依赖注入口 `getPageRoot` / `getOverflowY` / `warn`（对齐 `api-auth-interceptors` 的 DI 做法）
- [x] 2.4 时机与去重：首屏 rAF + `router.afterEach` 延后 400ms + `resize` debounce 300ms；同元素一条告警；HMR 下只装一次
- [x] 2.5 `main.ts` 在 `import.meta.env.DEV` 下动态 import 安装（生产分支静默消除）

## 3. 验证

- [x] 3.1 `eslint src/shared/dev/scroll-guard.ts src/main.ts` → **0 error 0 warning**
- [x] 3.2 `vue-tsc --noEmit` → **35 条既有错误不变**，新文件无错误
- [x] 3.3 jsdom 实跑真实模块（TS 转译 + `import.meta.env.DEV → true`）：
      A1 页面根 hidden 溢出 → 告警@页面根 · A2 根 visible + `.main-content auto` → 合法 · A3 根 visible + 中间层 hidden → 告警@中间容器 ·
      A4 根不溢出 → 合法 · A5 外层 `#app auto` 接手 → 合法 · A6 一路 visible 冒到 body → 告警
- [x] 3.4 `installScrollGuard` 端到端：rAF 后告警 1 条、resize 后再查仍 1 条（去重生效）、二次安装被拒
- [x] 3.5 `vite build` 成功；`dist` 全量搜索无 `scroll-guard` / `L0 契约被破` → **未进生产包**
- [x] 3.6 未做（明确边界）：未改任何 CSS、未动页面 DOM、未加依赖
