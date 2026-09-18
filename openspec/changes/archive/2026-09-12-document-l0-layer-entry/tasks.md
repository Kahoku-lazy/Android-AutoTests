## 1. 补 L0 层速查（frontend/AGENTS.md）

- [x] 1.1 元素链：视口 → html(L0-1) → body(L0-2) → #app(L0-3) → .app-shell(L1) → .main-content → 页面根
- [x] 1.2 代码范围表：四个位置 + 行号 + 各自负责的内容（`index.html` / `main.ts` / `style.css:33-53` / `tokens.css:18` 起）
- [x] 1.3 「能写什么」6 条：盒模型裁切 / 排版基线 / 全站背景 / 根级令牌 / 外壳元信息 / 应用装配
- [x] 1.4 「不能写什么」5 条：业务布局 / 新组件类 / 模块私有变量 / 组件里写 L0（scoped 静默失效）/ 动 overflow 与整层 fixed
- [x] 1.5 运行时写入现状表：4 条写入点 + 清理方式
- [x] 1.6 破约发现方式：dev-only `scroll-guard.ts` + 5 条已知缺口

## 2. 事实核对（不改代码）

- [x] 2.1 `style.css:33-53` 逐行确认 L0 段内容与终止位置（其后为组件类）
- [x] 2.2 `tokens.css:18` `:root, [data-theme="light"]`、`:335 --side-w: 228px`
- [x] 2.3 全量搜 L0 选择器：仅 `style.css` 命中 → 无组件级 L0 写入
- [x] 2.4 `no-bg-anim` 全仓搜索：仅 `router.ts:34,36`，无 CSS 消费方（写入文档的「死开关」结论）
- [x] 2.5 `data-theme` 全仓搜索：仅 `tokens.css:18`，无运行时换肤（写入文档的「已知缺口」结论）
- [x] 2.6 行数核对：style 311 / tokens 428 / workbench-theme 145 / motion 91、`main.ts` 21、`index.html` 17

## 3. 门禁

- [x] 3.1 Markdown 结构自检：新节 6 处小节标题 + 2 张表 + 1 个 text 代码块，标题前后空行正确（`### 跨模块共享文件` 前已留空行）
- [x] 3.2 零代码影响：未改任何 `.ts` / `.vue` / `.css`，无需重跑 typecheck / 构建