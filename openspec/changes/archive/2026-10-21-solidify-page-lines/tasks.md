## 1. 侧栏线型

- [x] 1.1 `AppSidebar.style.css` 在 `.sidebar` 作用域声明 `--sidebar-line: solid` 与 `--sidebar-border: var(--size-stroke-sketch) var(--sidebar-line) var(--ink)`，六处描边改引用 `--sidebar-border`；`tokens.css` 删除 `--comp-sidebar-dash`。验证：`rg "comp-sidebar-dash|sidebar-dash" frontend/src` 无匹配，且六个选择器均使用 `var(--sidebar-border)`。
- [x] 1.2 更新 `LoginView.style.css` 中提到 `--comp-sidebar-dash` 的注释为「侧栏自有线型令牌」。验证：`rg "comp-sidebar-dash" frontend/src` 无匹配。

## 2. 仪表盘章节

- [x] 2.1 `DashboardView.style.css` 删除 `.doc-section--board` 的 `border` 覆写，`.chapter-head` 与 `.subhead::after` 的 `dashed` 改 `solid`。验证：该文件 `.doc-section--board` 规则内无 `border:`，两处分隔线为 `solid`。
- [x] 2.2 确认 KPI / 卡片虚线未动：`rg "dashed" frontend/src/shared/components/KpiCard.vue frontend/src/shared/styles/workbench-theme.css` 仍有原命中。验证：两份文件不在本变更 diff 内。

## 3. 文档登记

- [x] 3.1 更新 doodle-craft `references/tokens.md` 的线型口径与 `references/components/layout.md` 的侧栏/分区描述。验证：两份文档不再把侧栏或 `.doc-section` 写成虚线约束。

## 4. 验证与关单

- [x] 4.1 `cd frontend; npm run lint:styles`：批 1 / 批 2 / 批 4 通过，批 3 仅剩变更前已存在的 51 处 `task-list` 借用 `ai-assistant` 模块令牌（本变更未触碰这些文件），无新增命中。
- [x] 4.2 `cd frontend; npx vue-tsc --noEmit` 与 `npx vite build` 通过，`prettier --check` 对四个改动样式文件通过。
- [x] 4.3 真实页面验收（Playwright，1686×1200）：四个章节外壳与章节头/子标题分隔线计算 `border-style` 为 `solid`；KPI 卡与智能体卡为 `dashed`；侧栏右分隔、品牌区底线、激活项、用户卡为 `solid`；`/login` 的 Meeting doodle 仍为 `dashed`。截图：`temps/visual-check/solid-dashboard.png`、`solid-sidebar.png`、`solid-login.png`。
- [x] 4.4 `openspec validate "2026-10-21-solidify-page-lines" --strict` 通过，归档后主 spec 与 delta 一致。
