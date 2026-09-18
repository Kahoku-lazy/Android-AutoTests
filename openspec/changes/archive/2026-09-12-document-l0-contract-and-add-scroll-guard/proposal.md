## Why

L0 契约（`html` / `body` / `#app` 一律 `height:100%` + `overflow:hidden`，滚动只能发生在内层容器）此前只写在 `style.css` 里：**没有文档，也没有任何机制发现破约**。而破约的后果是静默的——页面内容超出一屏、又被某个 `hidden` 层裁掉时，界面上不报错、不滚动，只是"少了半截"，只能靠人肉发现。

本变更补两件事：把 L0 写成明文契约，并加一个**仅开发环境**的自检把破约变成一条控制台告警。

## What Changes

1. **文档化 L0**（`frontend/AGENTS.md`）
   - 布局区域表补 **L0** 行：视口 / 文档流，归属 `index.html` + `main.ts` + `style.css` 顶部 + `tokens.css` 的 `:root`，标注为**唯一允许写 `html` / `body` / `#app` 样式的位置**
   - 规则补第 4 条「**L0 不滚，滚动必须发生在容器里**」：说明这是"视口固定 + 内层滚动"策略的入口条件；确需运行时写入（CSS 变量 / `body` 类名 / 全局监听）必须收敛到 composable 并成对清理；新页面必须落在策略① `.main-content` 或策略② `.doc-page--fixed .doc-body` 内，链上每个 `flex:1` 都要配 `min-height:0`
2. **新增 dev-only 自检**（`frontend/src/shared/dev/scroll-guard.ts`）
   - 判定：从页面根（`.main-content > *`）往上走 —— 先遇到**能滚**的一层 → 合法；先遇到 `hidden` / `clip` 且自身不可滚的一层 → 判定为裁切点；`visible` 的溢出继续往上冒，冒到 `body` / `html` 仍无人接手 → 判定为裁切点（并报最先溢出的那一层）
   - 时机：首屏 `requestAnimationFrame` + `router.afterEach`（延后 400ms 等异步取数渲染）+ `resize`（debounce 300ms）；同一元素只告警一次
   - 依赖可注入（`getPageRoot` / `getOverflowY` / `warn`），与 `api-auth-interceptors` 的 DI 做法一致，便于验证
3. **接线**（`frontend/src/main.ts`）：`import.meta.env.DEV` 为真时 `void import(...)` 安装一次；生产分支由 Vite define 静态消除
4. **明确不做**：不改任何 CSS、不动页面 DOM、不加依赖、不引入生产包

## 关联文档

- 无 PRD / ARCH；承接 `2026-09-11-scroll-container-audit-and-dead-declaration-cleanup` 与 `2026-09-11-layout-tokens-and-explicit-scroll-strategy`

## Capabilities

（无 / 无）→ `skip_specs: true`

## Impact

- 改动 **2 个源文件**（`frontend/AGENTS.md`、`frontend/src/main.ts`）+ **新增 1 个**（`frontend/src/shared/dev/scroll-guard.ts`，156 行）
- 验证：`eslint` **0 error 0 warning**（`scroll-guard.ts` + `main.ts`）· `vue-tsc --noEmit` **35 条既有错误不变**（新文件 0 错误）· jsdom 实跑真实模块 **A1–A6 六种链型全 PASS** + 安装/去重行为 PASS · `vite build` 通过且 `dist` 内**搜不到** `scroll-guard` / `L0 契约被破`（确认未进生产包）
- 副作用：dev 控制台在破约页面多一条 `[scroll-guard]` 告警；生产与其它环境零变化
