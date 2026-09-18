## 1. 令牌与共享规则

- [x] 1.1 在 `frontend/src/shared/styles/tokens.css` 的 T0 通用组件配色段登记 `--comp-table-row-accent`（默认 `var(--c-element)`）与 `--comp-table-row-selected-bg`（`color-mix(in srgb, var(--comp-table-row-accent) 18%, var(--app-bg-card))`）；验证：`npm run lint:styles` 退出码 0，且两条令牌可被 `var()` 解析
- [x] 1.2 在 `frontend/src/shared/styles/workbench-theme.css` 的 AppTable 段新增行选中共享规则，命中 `.el-table__body tr.is-selected > td.el-table__cell` 与 `tr.current-row > td.el-table__cell`，底色取 `var(--comp-table-row-selected-bg)` 且带 `!important`，作用域同时覆盖 `.wb-shell` 与 `.workflow-workbench`；验证：规则选择器含 `> td.el-table__cell` 与 `!important`

## 2. 迁移三处行选中实现

- [x] 2.1 `device-inspector/components/PageElementsPanel.vue`：`row-class-name` 返回 `is-selected`，删除 `:deep(.pep-row--selected)` 规则；验证：文件内不再出现 `pep-row--selected`
- [x] 2.2 `device-inspector/components/StructureAnalysisPanel.vue`：改用 `is-selected`，删除 `--sap-row-selected-bg` 与 `:deep(.sap-row--selected)`；验证：文件内不再出现 `sap-row--selected` 与 `--sap-row-selected-bg`
- [x] 2.3 `element-locator/components/PageElementsWorkbench.vue`：`rowClassName` 返回 `is-selected`，删除 `page-row--active` 与 `current-row` 两条私有规则；验证：文件内不再出现 `page-row--active`
- [x] 2.4 全仓检索确认行状态类只剩 `is-selected`；验证：对 `pep-row--selected|sap-row--selected|page-row--active|--sap-row-selected-bg` 全仓 grep 命中数为 0（已执行）

## 3. 网格线口径收敛

- [x] 3.1 `frontend/src/style.css`：`.el-table td` 的下边框色由 `var(--app-border-light)` 改为 `transparent` 并补意图注释（保持 1px 占位，视觉零变化）；验证：Chromium 实测 `border-bottom: solid rgba(0, 0, 0, 0)`，与改动前同为不可见
- [x] 3.2 `workbench-theme.css` 的 `.ac-table th` / `.ac-table td` 两条被全局 `!important` 覆盖的死声明改为 `transparent` 并注明由全局皮肤接管；验证：全仓检索确认本次改动未新增「白色/近白色当可见边框色」的声明
- [x] 3.3 `device-pool/DevicePoolView.style.css`：移除行间彩色虚线（三组 `tr:nth-child(3n±)` 的 `border-bottom-color`）与列间白色分隔线，保留状态色条；验证：文件内不再出现 `nth-child(3n` 行色与 `td + td` 列分隔线；状态色条规则 `row-online` / `row-busy` 仍在

## 4. 表头排版单一来源

- [x] 4.1 `device-pool/DevicePoolView.style.css` 移除 `font-size: var(--app-size-md) !important`、`font-weight: 800 !important`、`letter-spacing` 与 7 色分栏底线；验证：Chromium 实测表头计算样式为 `12px / 700 / uppercase`，与全局皮肤一致

## 5. 门禁与验收

- [x] 5.1 `npx vite build --mode development` 通过（`built in 36.53s`，退出码 0，需放宽沙箱以允许 esbuild 启动子进程）；`npm run typecheck` 报错 **全部位于 `frontend/tests/dashboard/**` 的 `DashboardRawData` 类型不匹配，属**既有无关报错**（本变更未触碰任何 .ts 与类型定义），已记录
- [x] 5.2 `cd frontend && npm run lint:styles` 通过；验证：批 2 / 批 3 硬门禁全绿，退出码 0
- [x] 5.3 按 `vue-frontend-check` 与 `doodle-craft` 门禁扫描本次改动的 7 个文件；验证：新增 27 行中无任何 hex/rgb/圆角/阴影字面量（仅注释含 `px` 字样），命中的存量违规（`#fff`、`999px`、模糊阴影等）归属后续变更批次，本变更未引入新违规
- [x] 5.4 浏览器引擎渲染断言（Playwright + Chromium，合成 DOM 复刻 Element Plus 表格结构，加载真实 `tokens.css` + `style.css` + `workbench-theme.css`）：6 项断言全部 PASS —— 改动前 `tr` 级行状态底色与未选中行**完全相同**（复现缺陷）；改动后选中行底色为 `color(srgb 0.938 0.918 0.996)` 与未选中 `rgb(255,255,255)` 可区分；表头 `12px / 700 / uppercase`；行线 `solid rgba(0,0,0,0)`。**限制**：本项为共享 CSS 契约级验证，未加载真实运行中的应用与数据；带数据的页面目视回归见 5.5
- [x] 5.5 确认未触碰范围外文件；验证：`git diff --stat` 本次仅含 7 个文件（`tokens.css` / `workbench-theme.css` / `style.css` / `DevicePoolView.style.css` / `PageElementsPanel.vue` / `StructureAnalysisPanel.vue` / `PageElementsWorkbench.vue`），工作区其余改动属其他在飞工作，未触碰