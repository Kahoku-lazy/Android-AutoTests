## Why

上一变更把 L0 契约写进了 `frontend/AGENTS.md`（L0 行 + 规则 4），但**只写了「不许做什么」**：没有元素链、没有控制区域、没有代码落点行号、没有「能写什么 / 不能写什么」的正反清单，也没有运行时写入 L0 的现状登记。换个 AI 接手时，仍然要靠读 `style.css` 反推 L0 的职责与边界。

本变更在 `AGENTS.md` 里补一节**自解释的 L0 层速查**，让接手 AI 不读代码就能回答：L0 是什么、管哪些元素、代码在哪几行、能写什么、不能写什么、谁在运行时写它、怎么发现破约。

## What Changes

在「布局区域与归属」四·条规则之后新增 `### L0 层速查：视口 / 文档流`（59 行），六个小节：

1. **元素链**：浏览器视口 → `html`(L0-1) → `body`(L0-2) → `#app`(L0-3) → `.app-shell`(L1) → `.main-content`(策略①) → 页面根 (L2–L5)
2. **代码范围**：唯一允许写 L0 的四个位置及行号 —— `index.html`(17 行全文) · `src/main.ts`(21 行全文) · `src/style.css:33-53`(全局段，全文 311 行) · `src/shared/styles/tokens.css:18` 起 `:root`(全文 428 行)
3. **L0 能写什么**：6 条（文档流盒模型与裁切 / 全局排版基线 / 全站底色与纸面点阵背景 / 根级令牌 / 浏览器外壳元信息 / 应用装配与全局副作用注册）
4. **L0 不能写什么**：5 条（不写业务布局 / 不新增组件类到 L0 段 / 不写模块私有变量 / 组件里不许写 `html|body|#app`（scoped 会编译成 `body[data-v-x]` 永不匹配）/ 不动 `overflow:hidden` 与不挂整层 fixed）
5. **运行时写入 L0 现状表**：4 条（`useSidebarResize` 的 `--side-w` 与 body cursor/userSelect、`AppSidebar` 复位、`router.ts` 的 `no-bg-anim`、`animations.ts` 粒子）逐条标注清理方式
6. **破约如何被发现**：dev-only `scroll-guard.ts` 告警 + 5 条已知缺口（兜底行为、死 class、title 不一致、`100vh` 移动端、无运行时换肤）

## 关联文档

- 无 PRD / ARCH；承接 `2026-09-12-document-l0-contract-and-add-scroll-guard`（L0 行 + 规则 4 + 自检模块）

## Capabilities

（无 / 无）→ `skip_specs: true`

## Impact

- 只改 **1 个文件**：`frontend/AGENTS.md`（146 → 206 行，+60）；不动任何代码、不动 CSS、不影响运行时
- 文中每一处行号与事实都在本次会话内**逐一核对过**：`style.css:33-53`（`*` 归零 / `html,body,#app` 定高裁切 / `#app` 兜底 / `body` 排版）· `tokens.css:18` `:root, [data-theme="light"]`、`:335` `--side-w: 228px` · `main.ts` 21 行 · `index.html` 17 行 · 运行写入点 `useSidebarResize.ts:25,30,43,44,55,56`、`AppSidebar.vue:138,139`、`router.ts:34,36`、`animations.ts:158`
- 交叉验证（未改代码，只做事实核对）：全量搜 `html|body|#app` 选择器 **仅命中 `style.css`**（无人从组件里写 L0）· `no-bg-anim` 只有 `router.ts:34,36` 两个写入点、**无 CSS 消费方** · `data-theme` 只有 `tokens.css:18` 一个选择器、**无运行时换肤代码** · `style.css` 311 行 / `tokens.css` 428 行 / `workbench-theme.css` 145 行 / `motion.css` 91 行（后两者不碰 L0）