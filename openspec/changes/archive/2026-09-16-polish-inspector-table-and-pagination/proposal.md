## Why

上一轮 `rework-inspector-table-and-controls` 收尾时登记了五项「不在本次范围」的后续项，用户要求一次性收掉：

1. 快照抽屉的**删除**是写库级删除（DELETE 端点 + 清理截图/缩略图文件），却没有二次确认（`SnapshotListDrawer.vue:47-55` 直接调 `store.deleteSnapshot`）。
2. 共享 `usePagination` **数据变少不回退**：`pagedItems` 会切出空片，设备管理页与检查器都受影响（检查器上轮已用页面级 `watch` 补，设备页仍缺）。
3. 元素表 8 列最小宽合计 ≈986px、中栏实宽 ≈630px，横向滚动可用性差（列一滚就走丢）。
4. 元素表区域的列宽与间距是散落的裸字面量（`10px` / `14px` / `6px` / `38px` 等），既不在共享刻度上也未登记。
5. `ai-assistant/ToolDebugPage.style.css:132` 的 `var(--app-bg)` 是**全仓唯一**引用且令牌不存在 → `npm run lint:styles` 批 3 硬门禁亮红（该文件是工作区里未跟踪的在途文件）。

## What Changes

- **① 快照删除二次确认**：抽屉删除改走 `ElMessageBox.confirm`（危险态、写明不可恢复），确认后才调删除；取消不发请求。
- **② 共享分页自动夹取**：`shared/composables/usePagination.ts` 在 `totalPages` 缩小时把 `currentPage` 夹到有效范围（四处消费方同时受益）；检查器面板自己的「回第 1 页」watch 保留（那是本页 spec 要求的语义）。
- **③ 横向滚动可用化**：把 `device-pool/composables/useTableDragScroll.ts` **提升**到 `shared/composables/useTableDragScroll.ts`（消除跨模块内部 import），检查器元素表接同一套：外层容器横向滚动 + 按住拖拽平移 + **首列（选择 / 缩略图 / 元素名称）左侧冻结**。
- **④ 列宽与间距集中登记**：新建 `device-inspector/tokens.css` 登记 `--insp-*` 间距令牌（**值不变 = 视觉零变化**），列宽移入模块 `constants.ts`；组件内不再出现这两类裸字面量。
- **⑤ 悬空令牌修复**：`.td-input` 的 `var(--app-bg)` → `var(--app-bg-input)`（该选择器就是输入框，语义最近；该文件属他人在途工作，只改这一行）。
- **不破坏性**：不改后端与 7 个端点契约、不改路由、不改设备管理页的表格结构与分页 UI（它只受益于 ②）、不删共享件、不新增第二套表格或分页实现。

## 关联文档

- 上一轮变更与归档：`openspec/changes/archive/2026-09-16-rework-inspector-table-and-controls/`（本变更是其 tasks 中「后续可选」五项的执行）。
- 评审稿：`temps/inspector-redesign-proto.html`（表纸 / 分页栏口径来源）。
- `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`：删除端点契约不变（本次只加前端确认）。
- `openspec/specs/device-inspector-page/spec.md`、`frontend-l4-data-surface/spec.md`：本次经 delta 修改。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `device-inspector-page`：新增「快照删除需二次确认」「元素表横向滚动可用与首列冻结」「列宽与间距集中登记」三条要求。
- `frontend-l4-data-surface`：「Single pagination implementation」补「结果集变小后自动夹取页码，不落在空页」并要求该行为由共享 composable 承担。

## Impact

- 共享层：`shared/composables/usePagination.ts`（自动夹取）、新增 `shared/composables/useTableDragScroll.ts`（自 device-pool 提升）
- device-pool：`DevicePoolView.logic.ts` 的 import 改指共享件（其余不动，行为因 ② 受益）
- device-inspector：`components/SnapshotListDrawer.vue`（确认框）、`components/StructureAnalysisPanel.vue`（拖拽容器 + 首列冻结 + 去掉裸字面量）、新增 `tokens.css`、`constants.ts`（列宽与表格最小宽）、`index.vue`（间距令牌引用）
- ai-assistant：`ToolDebugPage.style.css`（仅 1 行悬空令牌 → `--app-bg-input`；该文件为工作区未跟踪文件）
- 后端：无改动（无迁移、无契约变更）
- 规格：2 份 delta
- 测试：无既有分页单测，本次以 Playwright 真机走查（拖拽平移 / 首列冻结 / 页码夹取 / 删除确认）+ 既有门禁验收
