## Context

现状（读码核实，`frontend/src/modules/device-inspector/`；动机见 proposal.md - Why）：

- `components/StructureAnalysisPanel.vue:170-172`：`<AppTable v-if="elements.length" …>` —— 无元素时整张表格（含表头）被 `EmptyState` 替换。
- `store.ts:64-99`：`mergedRows` 用 `shared/ocrMatch` 把 OCR 文本合并进 dump 行；`store.ts:300-306` 的 `saveToElements` 用它的 `_rowKey`（`'d'+下标`）反查勾选下标。
- `components/CaptureForm.vue:8-11`：`METHODS`（仅 Dump / 仅 OCR）+ `el-radio-group`；`store.ts:46` `captureMethod`。
- OCR 展示触点：`ScreenshotView.vue:12-16,128,213-225,234-236,261-286`、`SnapshotListDrawer.vue:8,43`、`index.vue:41-43,125-129,138`。
- 分页参照物：`device-pool/index.vue:119-216`（`.table-toolbar` + `.device-table-wrapper` + `AppTable`）、`device-pool/constants.ts:38-46`（表头 54 / 行高 64 / `PAGE_SIZE_OPTIONS` / `DEFAULT_PAGE_SIZE`）、共享 `shared/composables/usePagination.ts`。实测（`temps/devices-table-css.json`）：`.ac-table-wrap.sketch-sheet` 为 `border:2px solid var(--ink)` + `border-radius:2px 6px 2px 4px` + `box-shadow:4px 4px 0 0 <accent>`；表头 53px/12px/700/uppercase；`.table-toolbar` 高 38px、`.page-info` 14px/600/次级色。
- 共享 `usePagination` **不会**在数据变少时回到第 1 页（`pagedItems` 会算出空片），设备管理页亦未处理。

## Goals / Non-Goals

**Goals:**

- 进入页面即见完整表格（表头 + 8 列），空数据由表格自身空态承担，文案统一「未选中设备」。
- 元素表格固定 8 行一页，上一页 / 下一页常驻，接共享分页实现。
- 抓取方式恒为 Dump；OCR 采集 / 保存 / 展示三处链路一次性收敛为单链路。
- 按已评审的变体 A 重做页面分区筹码与设备选择控件，全部复用既有皮肤与令牌。

**Non-Goals:**

- 不改三栏布局顺序（变体 C 被否，其与 `device-inspector-page`「三栏布局顺序」冲突）。
- 不改后端与 7 个端点契约（`capture` 的 `method` 入参、`di_snapshots.ocr_json` 落库都不动）。
- 不动设备管理页的分页与按钮组、不改路由、不新建第二套表格 / 分页实现。
- 不删 `shared/ocrMatch.ts` 与其单测（仅本模块不再消费）。
- 不自绘下拉、不引入新设计令牌。

## Decisions

### D1 表格常驻与空态归属

`StructureAnalysisPanel.vue` 去掉 `AppTable` 的 `v-if`，空态改走 `AppTable` 的 `#empty` 插槽（`EmptyState` + `constants.EMPTY_TEXT.noDevice`）；分区列保留自己的「暂无分区数据」提示。分页栏放在**表纸之上**（与设备管理页 `.table-toolbar` 同位），只渲染右半段（`第 X / Y 页 · 共 N 条` + `.page-nav` 两个 `el-button.wb-btn`），不渲染左半「显示行数」。
表纸：`AppTable` 传 `accent="var(--c-element)"`、`:striped="true"`、`table-layout="auto"`；页面作用域把 `border-style` 覆写为 `solid`（宽度/颜色仍取 `--comp-sheet-border`，线型登记见 `frontend-doodle-sketch-table` delta）。

- 备选：把空态做成表格外的 `EmptyState`（现状）—— 否决：正是用户要修的「看不到表格」。
- 备选：分页栏放到 `.workspace` 之上（工具条下方）—— 否决：会与筛选栏并列，视觉上离表格太远。

### D2 分页接线与「回第 1 页」缺口

新建 `device-inspector/constants.ts`：`PAGE_SIZE_OPTIONS=[8]`、`DEFAULT_PAGE_SIZE=8`、`TABLE_HEADER_HEIGHT_PX=54`、`TABLE_ROW_HEIGHT_PX=64`、`TABLE_MIN_WIDTH_PX=986`、`EMPTY_TEXT={ noDevice: '未选中设备' }`。面板内 `usePagination(props.elements, { pageSize: DEFAULT_PAGE_SIZE, options: PAGE_SIZE_OPTIONS })`，`AppTable` 的 `data-source` 改用 `pagedItems`，`共 N 条` 取源长度。
共享 composable 不自动回第 1 页：在本页 `watch` 源长度 + `activeRole`，长度变化时 `goPage(1)`（只修本页，设备管理页留给后续）。

- 备选：自写 `currentPage`/`totalPages` —— 否决：违反 `frontend-l4-data-surface`「唯一分页实现」与模块常量真相源。

### D3 勾选键直取（合并行删除后的保存口径）

`mergedRows` 整段删除后，`saveToElements` 的筛减改为直接解析 `checkedIds`：过滤 `'d' + 数字` 的键 → `element_ids`。行键仍由 `analyzeSnapshot` / `viewSavedPage` 写入 `_rowKey`，与选择列同一来源，杜绝二次映射失配。

- 备选：保留 `mergedRows` 只为取下标 —— 否决：它存在的唯一理由是 OCR 合并，OCR 下线后属死计算。

### D4 OCR 链路拆除的边界

删除：`store.ts` 的 `import matchOcrToElements` / `ocrTexts` / `selectedOcr` / `mergedRows` / `selectOcr` / `viewSavedPage` 的 `ocr_count`+`texts` 映射 / `capture()` 成功提示里的 OCR 数字；`index.vue` 的 `onOcrClick` / `:ocr-results` / `:selected-ocr` / `@click-ocr` / 页脚「N OCR」/ 副标题里的「与 OCR」；`ScreenshotView.vue` 的 `ocrResults` / `selectedOcr` props、`click-ocr` emit、OCR 绘制段与 `hitTestOcr`；`SnapshotListDrawer.vue` 的 `METHOD_LABELS` 中 `ocr`/`both` 与「OCR N」。
保留：`shared/ocrMatch.ts` 与其单测（零消费但不删）、后端 `di_snapshots.ocr_json` 与 `capture` 的 `method` 入参（只是前端不再发 `ocr`）。

- 备选：连带删除 `shared/ocrMatch.ts` —— 否决：共享件与共享测试不属本模块范围，删了会让其它潜在消费方无件可用。

### D5 去抓取方式选择

`CaptureForm.vue` 删 `METHODS` 与 `el-radio-group`；`store.ts` 删 `captureMethod`，`capture()` 固定 `apiCapture(serial, 'dump')`。未选设备时「获取」仍是灰键 + 提示（既有守卫不变），忙碌态仍用原生 `disabled`。

### D6 变体 A 的落地形态

- 分区筹码：`.sap-section` 由纯文本行改为硬边按键（`button` + `aria-pressed`），含分区名与计数徽标；未选中 `--c-workflow`、选中 `--c-dashboard`；新增「全部分区」复位项（`activeRole = null`）。
- 设备选择：**保留 Element Plus `el-select`**，只由页面作用域把**触发键**改造成硬边按键（始终可用的天蓝底 —— 它是选择设备的入口，不能是灰键）；下拉项文案补齐「在线 / 使用中」状态，禁用逻辑沿用 `availableDevices`（已排除被执行引擎占用的设备）。
  **下拉浮层不换皮**：`el-select` 的 popper 默认传送到 body（页面作用域 `:deep()` 不可达），仓库内也无 `popper-class` + 全局样式的先例；为浮层加全局规则会越出「页面样式落在页面作用域」的边界。故触发键换皮、浮层保持 Element Plus 默认（白纸观感已接近，定位与键盘可达性更稳）。原型里的纸面下拉属示意，落地下沉为后续可选打磨项。
- 备选（否决）：自绘「硬边触发键 + 纸面下拉」—— 键盘导航、焦点管理、点击外部关闭、滚动定位都要自建，违反「共享件优先 / 不重复造轮子」，且 `vue-frontend-check` 五.7「可点击非原生控件无键盘角色」会判 🟠。

### D7 空表文案统一的副作用（已登记）

统一为「未选中设备」后，**筛选/搜索无匹配**也显示这一句。这是用户拍板的口径，已在 `device-inspector-page` delta 中显式写成 Scenario，避免后续被误判为 bug。备选（按原因区分三种文案）被用户否决。

## 模块防火墙自检

- 改动全部在 `frontend/src/modules/device-inspector/`，无 `apps/` 改动：不新增跨 App import、不触碰 ORM、无写库路径变化。
- 前端 HTTP 出口仍是模块唯一出口 `device-inspector/api.ts`（内部走 `@/shared/api-client`）：不新增端点、不新增 WS/SSE。
- 跨模块依赖**减少**一项：`@/shared/ocrMatch` 的消费被移除；其余（`@/modules/element-locator/api`、`@/shared/components/*`、`@/shared/composables/usePagination`、`@/shared/icons`）均为既有用法。
- 共享件与全局令牌零改动；模块私有样式仍落在 `.inspector-workbench` 作用域内；新增常量落在模块 `constants.ts`。

## Risks / Trade-offs

- [工具条「x/y 元素」与分页「共 N 条」口径可能不一致] → 两者都取同一 `filteredAnalysisElements` 源；实现时用同一 computed 派生。
- [8 行 × 64px + 表头 54 = 566px 可能超过当前栏高] → 表纸自适应容器高度并内部滚动，`min-height` 只保证 8 行可读；窄视口堆叠时给最小高度，避免 0 高度。
- [8 列最小宽 ≈986px 超过中栏宽度，XPath/bounds 需横向滚动] → 保留横向滚动（既有现象，非本次引入）；拖拽平移列为 P2 可选。变体 C 曾以消除该滚动为目标，被用户否决。
- [OCR 展示拆除后历史快照不再显示 OCR 框选/计数] → 用户已确认单链路；后端数据仍在，若日后要恢复展示需另开变更。
- [删 `mergedRows` 影响保存口径] → D3 直接解析勾选键；验收任务要求真机核对「勾 3 行 → 请求体 `element_ids` 精确等于这 3 行下标」。
- [自绘控件可达性] → D6 保留 `el-select`；筹码用原生 `button` + `aria-pressed`。
- [原型与落地的差异：下拉浮层不做纸面皮肤] → 已在 spec 写明「浮层由 Element Plus 承担定位与可达性」；若后续要做纸面下拉，需先立 `popper-class` + 全局样式的边界口径。

## Migration Plan

纯前端改动：无数据迁移、无部署顺序约束、无接口契约变更。回滚 = 还原本次提交。
门禁：`npm run lint:styles` 退出码 0、`npx vite build` 通过、`npm run typecheck` 报错文件集不新增（既有：`tests/dashboard/**`、`store.ts` 的 OcrMatchPoint 四项、`case-manager/ProjectTree.vue`；其中 `store.ts` 的 4 条会随 D4 删除 `mergedRows` 一并消失），并用 Playwright 真机走查四条需求 + `vue-frontend-check` 逐项记录。
