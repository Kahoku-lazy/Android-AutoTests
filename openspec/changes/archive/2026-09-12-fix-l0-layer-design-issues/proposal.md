## Why

L0 层设计审查（`temps/l0-audit.mjs` 的 postcss 全量解析 + 生产产物扫描 + 真实浏览器冒烟）发现 4 个问题，本变更逐条修复：

1. **EP 样式下发两遍**：`main.ts` 引全量 `element-plus/dist/index.css`（349 KB），`vite.config.js` 的 `ElementPlusResolver` 又按需注入组件样式 → dist 里同一套样式存在两份（`index-*.css` 383 KB + 14 个 `el-*.css` 分包 89 KB），CSS 合计 735 KB
2. **高度链被 `100vh` 破**：L0 用 `html/body/#app{height:100%}` 建链，L1 却用 `.app-shell{height:100vh}`；移动端动态工具栏下 `100vh > #app.clientHeight` → `#app{overflow:auto}` 兜底被激活 → 双层滚动条（`LoginView` / `NotFound` 同类）
3. **图标能力外包给未锁版本的 CDN 且失败静默**：`index.html` 引 `https://unpkg.com/lucide@latest`（head 内阻塞、无版本号/SRI），消费方是 `if (window.lucide) …` 守卫 → 内网/离线环境图标全空且无提示
4. **缺移动端/主题基线**：全仓无 `color-scheme`、无 `overscroll-behavior`

## What Changes

1. **EP 样式只留一份**：`vite.config.js` 两处 `ElementPlusResolver({ importStyle: false })`，样式统一由 `main.ts` 的全量 import 提供
   - ⚠️ 先试了更激进的「删全量、只走按需」，**验证阶段抓出真实回归**：30 个文件是显式 `import { ElMessageBox } from 'element-plus'`，绕过了 resolver 的样式注入 → 产物里**没有 `.el-message-box` 样式**（确认弹窗将失去样式）。故改为保守方案：全量保留 + 关闭按需注入，同样只下发一份
2. **高度链拉直**：`.app-shell` 改 `height:100%`（`App.vue`）；`LoginView` / `NotFound` 的 `100vh` 改 `100%`；`.main-content` 补 `overscroll-behavior: contain`（内层滚到底不再把滚动交给 `#app`）
3. **lucide 本地化 + 子集**：`npm i lucide`（^1.45.0，lockfile 锁死）；`index.html` 删 CDN；新增 `shared/icons/lucide-registry.ts` 登记平台真正用到的 **14 个**图标名（侧栏 12 + 页头 literal 7 去重），`main.ts` 注入 `window.lucide.createIcons`
   - ⚠️ 先试了 `import { icons }`（全量 1834 个图标）→ 入口包从 ~15 KB 涨到 730 KB；改子集后入口回到小体积，且图标名漏登记时 lucide 自己会打印 not-found 告警（不静默）
4. **补基线**：`style.css` L0 段加 `html { color-scheme: light }`（深色系统下原生滚动条/控件不再变暗）
5. **同步文档**：`frontend/AGENTS.md` 的 L0 速查节更新（链图 `.app-shell` 100%、四个位置的行数与新内容、⑤ 表新增 `window.lucide`、⑥ 新增「EP 样式口径（改前必读）」）

## 关联文档

- 承接 `2026-09-12-document-l0-contract-and-add-scroll-guard`、`2026-09-12-document-l0-layer-entry`（本变更按该节的契约逐条修复 L0）

## Capabilities

（无 / 无）→ `skip_specs: true`

## Impact

- 改 **8 个源文件**：`main.ts` · `App.vue` · `style.css` · `views/LoginView.style.css` · `views/NotFound.vue` · `vite.config.js` · `index.html` · `AGENTS.md`；新增 **1 个**：`src/shared/icons/lucide-registry.ts`；依赖 **+1**：`lucide@^1.45.0`（package.json + lockfile）
- 产物：CSS **735 → 578 KB**（删掉重复的 `el-*.css` 分包，0 个）· JS **2854 → 2839 KB**（入口不再含全量 lucide）
- 验证（`temps/l0-fix-verify.mjs`，静态产物 + 本地静态服务 + Playwright/chromium 真实浏览器）：**全 16 项 PASS** —— `.el-message-box` 等 12 项函数式 API/复合组件样式齐备 · 29 个在用 EP 组件主类齐备 · 运行时 `--el-color-primary` = 我方 `#F7C948`（EP 默认在前、我方在后）· `.app-shell` 与 `#app` 等高 800px 且 `#app` 未被撑破 · `overscroll-behavior:contain` · `color-scheme:light` · 14/14 图标渲染成 svg · 首屏 0 条 unpkg/lucide 请求 · 0 条 console 错误
- 门禁：`eslint` 0 problem · `vue-tsc --noEmit` **35 条既有错误不变** · `vite build` 成功
- 未做（明确边界）：未删 `body.no-bg-anim` 死开关、未统一 `--side-w` 三处取值、未动 Google Fonts 外链（有本机字体回退）、未改 `index.html` 英文 title（均为已知缺口，登记在 `frontend/AGENTS.md`）