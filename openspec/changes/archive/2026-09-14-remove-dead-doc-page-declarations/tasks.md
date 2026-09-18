## 1. 复核判据

- [x] 1.1 逐处复核 7 个 `.doc-page` 选择器的权重与 `!important`，确认「可删 5 处、保留 2 处（TaskDetailPage 全保留 / report index 保留 `overflow!important`）」；验证：结论与 design §Context 表格一致

## 2. 删除失效声明

- [x] 2.1 `device-inspector/index.vue` 的 `.doc-page`：删 `height: 100%` 与 `overflow: hidden`，保留 `display` / `flex-direction` / `background-color`；验证：该块不再含 height/overflow，`background-color: var(--paper)` 仍在
- [x] 2.2 `report-generator/TaskReport.vue` 的 `.doc-page`：删 `height:100%` 与 `overflow-y:auto`；验证：`rg "\.doc-page\{[^}]*height" frontend/src/modules/report-generator/TaskReport.vue` 0 命中
- [x] 2.3 `report-generator/ReportDetail.vue`：同上；验证：同 2.2 的检索 0 命中
- [x] 2.4 `report-generator/CaseBreakdown.vue`：同上；验证：同 2.2 的检索 0 命中
- [x] 2.5 `report-generator/index.vue`：**只**删 `height:100%`，保留 `overflow:hidden!important`；验证：该行仍含 `overflow:hidden!important` 且不含 `height:100%`

## 3. 文档同步

- [x] 3.1 更新 `frontend/AGENTS.md` L2 速查 §⑥：去掉「A/C 类 `.doc-page{height:100%}` 死声明」中的已清项，并纠正 ai-assistant / device-pool 的误列（改为：已清理 5 处；`ai-assistant/TaskDetailPage` 的复合选择器 + `!important` 属**生效**声明，勿删）；验证：文档不再把 TaskDetailPage / device-pool 列为死声明持有者

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误（既有无关报错需注明）
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：构建成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁（样式层 + 布局裁剪）；验证：一.1 记为 N/A 并附「被覆盖声明删除 ⇒ 渲染恒等」的静态证明，逐项记录无新增违规
