## 1. 复核

- [x] 1.1 复核 6 个 `wb-*` 类全仓 0 引用（含动态拼接），并确认 `wb-btn--sunset`（dashboard 在用）与 `wb-loader`（WbLoader.vue 在用）仍在用；验证：检索结果与 design §Context 一致

## 2. P0 dashboard 容器口径补漏

- [x] 2.1 `frontend/src/modules/dashboard/index.vue:52` 页面根补 `dashboard-workbench`；验证：该行 class 含 `dashboard-workbench`
- [x] 2.2 `DashboardView.style.css` 的 `.doc-page` / `.doc-body` 收窄为 `.dashboard-workbench .doc-page` / `.dashboard-workbench .doc-body`，并删除 `.doc-page` 块内 `height:100%` 与 `overflow:hidden`；验证：该文件不再出现行首裸 `.doc-page {` / `.doc-body {`，且 `display` / `flex-direction` / `background-color: var(--paper)` 保留

## 3. P1 死 CSS 类清理

- [x] 3.1 删除 `workbench-theme.css` 的 `.wb-chip`（含 `.is-active` / `.on` 变体）与 `.wb-status-pill`；验证：`rg "wb-chip|wb-status-pill" frontend` 0 命中
- [x] 3.2 删除 `motion.css` 的 `.wb-btn--teal` / `.wb-btn--berry` / `.wb-btn--sky` / `.wb-spinner`；验证：`rg "wb-btn--teal|wb-btn--berry|wb-btn--sky|wb-spinner" frontend` 0 命中，且 `wb-btn--sunset` 与 `wb-loader` 仍在

## 4. 门禁与验收

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误（既有无关报错需注明）
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：构建成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁（样式层 / 布局裁剪）；验证：逐项记录，无新增违规
- [x] 4.4 dashboard 三档（768 / 1024 / 1280）目视；验证：**用户于 2026-09-14 授权关单** —— dashboard 目视由用户在已登录浏览器中代验（本环境无登录态，无法自测）；用户未回传逐项结论，按授权关闭，本条记录为「代验 + 授权」而非静态替代
