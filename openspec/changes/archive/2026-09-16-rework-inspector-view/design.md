## Context

现状（读码核实，`frontend/src/modules/device-inspector/`）：

- `index.vue` 工具条渲染 6 个按键，其中「结构分析」/「返回元素列表」由 `store.viewMode`（`'elements' | 'structure'`）
  二选一，默认 `'elements'`；工作区是两列 grid（左 `ScreenshotView`，右 `PageElementsPanel` 或 `StructureAnalysisPanel`）。
- `StructureAnalysisPanel.vue` 内部已是「页面分区（`aside.sap-sections`） + 元素表格（`section.sap-table`）」两列，
  且 `activeRole` 只在组件内使用；`v-if="sections.length"` 决定整块 `.sap-body` 是否渲染。
- `store.ts` 已具备勾选能力：`checkedIds: Set<string>`、`toggleCheck()`、`clearChecked()`；
  `saveToElements()` 用 `mergedRows`（`_rowKey = 'd' + 元素下标`）反查勾选行下标作为 `element_ids`。
- 已保存页面回看（`viewSavedPage()`）用 `snapshot_id: null` 造出一个「伪快照」，且 `analysis` 为 `null`；
  后端 `GET /api/inspector/snapshots/{id}/analyze` 只接受真实快照 id（`apps/device_inspector/api.py:245`）。
- 按键皮肤由页面作用域 `.inspector-workbench` 承担（`index.vue:277-320`），不可用态用原生 `disabled` + `opacity: .5`。

## Goals / Non-Goals

**Goals:**

- 进入 `/inspector` 即呈现完整三栏骨架，且结构视图成为唯一视图、无需按键触发分区。
- 按键可用性以「蓝底可用 / 灰底不可用 + 点击提示」表达，不改变硬边几何。
- 结构表格承担勾选，并让勾选口径与既有 `save-elements` 契约严格对齐。

**Non-Goals:**

- 不改除 `save-elements` 以外的后端接口（其余 6 个端点与 `snapshot`/`analysis` 字段不变）；
  不为已保存页面新建分区分析端点；不改元素定位自身的快照导入端点（`views_snapshot` 的 `ocr_json`）。
- 不改共享件（`AppTable` / `FilterTabs` / `ErrorState`）与 `tokens.css`；不新增色值令牌。
- 不保留任何形式的「元素列表」视图（dump/OCR 合并行表格整体下线）。
- 不改 `SaveToElementsDialog` 的保存目标选择与校验逻辑（只删「OCR 数据」开关一行）。
- 只下线「页面级 OCR 落库」，不下线检查器的 OCR 获取与展示（「仅 OCR」方式、手机屏幕 OCR 框选、
  OCR 计数与 `di_snapshots.ocr_json` 全部保留）。

## Decisions

### D1 三栏布局由外层两列 + 面板内已有两列组合而成

`.workspace` 改为 `grid-template-columns: minmax(0, 2.4fr) minmax(0, 1fr)`：左列放 `StructureAnalysisPanel`，
右列放 `ScreenshotView`；面板内部保留既有 `0.8fr : 2fr`。最终自左至右为 页面分区 ≈21% → 元素表格 ≈51% → 手机屏幕 ≈28%。

- 备选 A：把分区拆成独立 `PageSectionsPanel.vue` 作为外层第一列 —— 否决：需要把 `activeRole` 提升到 store 或 index.vue，
  并新增一个组件文件，视觉结果与 D1 等价，diff 更大。
- 备选 B：外层三列 + 面板只留表格 —— 否决理由同 A。
- 窄视口（`max-width: 1200px`）沿用既有单列纵向堆叠规则，只调整顺序为 分区 → 表格 → 手机。

### D2 单一视图 + 自动分区

删除 `viewMode` 状态与两个切换键；`capture()` 已有的自动 `analyzeSnapshot()` 保留，`viewSnapshot()` 补一次调用。
已保存页面在 `viewSavedPage()` 内构造 `analysis = { is_webview: false, sections: [], elements: 映射后的元素 }`，
只补 `_idx`/`_rowKey`，**不伪造** `role`/`metrics`（分区列与指标列如实显示空态与 —）。

- 备选 A：新增「页面结构分析」后端端点 —— 否决：属后端契约变更，超出「前端显示需求变更」范围（用户已确认走纯前端映射）。
- 备选 B：已保存页面沿用元素列表 —— 否决：与需求 4「元素列表显示页面去掉」直接矛盾。

### D3 勾选行键与 `mergedRows` 同源

结构表格的选择列复用 `store.checkedIds` / `toggleCheck()`，行键统一为 `d<元素下标>`：在 `analyzeSnapshot()` 与
`viewSavedPage()` 写入 `analysis.elements` 时补 `_rowKey = 'd' + _idx`。表头全选只作用于当前所示行。

- 备选：结构面板自行用 `_idx` 数值作键 —— 否决：`saveToElements()` 用 `mergedRows` 的 `_rowKey` 反查，
  数值键会一条都匹配不上，从而静默退化为「保存全部元素」。
- `saveToElements()` 的「未勾选则提示先勾选」守卫保持不变（本次不改保存语义，只补勾选入口）。

### D4 筛选与搜索作用于结构表格，截图高亮仍用全量

把 `filteredElements` 内的筛选/搜索逻辑抽成 `applyFilters(els)`，新增 `filteredAnalysisElements` 供表格使用；
`index.vue` 传给 `ScreenshotView` 的仍是 `store.elements` 全量（与变更前结构视图口径一致）。分区计数保持后端全量口径。

### D5 按键可用性：灰底 + 点击守卫，不用原生 disabled

可用按键天蓝底（`--c-workflow`），不可用按键灰底（`--color-ink-79`）并带 `aria-disabled="true"`，
由 click 守卫统一提示「按键不可用，请先选择设备」。文案与守卫集中在 `store.ts`（`KEY_DISABLED_MESSAGE` +
`notifyKeyUnavailable()`），供 `index.vue` 与 `CaptureForm.vue` 共用，避免同一文案两处硬编码。
「获取」的请求进行中状态保留原生 `disabled`（忙碌态，不属「未选设备」）。

- 备选 A：继续用原生 `disabled` + 外层包裹捕获点击 —— 否决：多一层 DOM，键盘与语义更乱。
- 备选 B：只在 `title` 提示 —— 否决：需求明确要求「点击弹出提示」。

### D6 「保存到元素定位」可用条件收紧为存在快照 id

原条件 `!store.snapshot` 对「已保存页面回看」为假（伪快照非空），点击会 POST `/inspector/snapshots/null/save-elements`。
本次把可用条件改为 `!!store.snapshot?.snapshot_id`，该视图下按键呈灰键并提示。

### D7 默认骨架的可见性条件

`.filter-bar` 去掉 `v-if="store.snapshot"`；结构面板的整块渲染条件由 `sections.length` 改为 `elements.length`，
分区列为空时在列内显示空态文案（否则无分区（已保存页面）时整张表格会一起消失）。

### D8 OCR 落库整链路下线（前端开关 + 后端入参 + 存量清理）

- 前端：`SaveToElementsDialog.vue` 删除「OCR 数据」`el-switch` 与 `includeOcr` 状态；
  `store.saveToElements()` 删除 payload 的 `include_ocr` 字段与 `hasOcrChecked` 分支（该分支只服务勾选 OCR 行，
  元素列表下线后已无 OCR 行可勾）。
- 后端入参：`views.save_elements` 删除 `include_ocr` 读取，`api.save_snapshot_to_elements` 删除该形参并恒以
  `ocr_json=None` 调 `import_snapshot_page`。已核对唯一调用方是 `views.py:87`（无 AI Tool 调用方、无测试引用），
  故可直接删参。
- 保留 `apps/element_locator/api_snapshot.import_snapshot_page` 的 `ocr_json` 形参：元素定位自己的导入端点
  （`views_snapshot.py:38`）仍在传 `body.get("ocr_json")`，删掉会连带废掉该端点既有能力（超出本次范围）。
- 存量清理：新增 `apps/element_locator/migrations/0014_clear_page_ocr_json.py` 数据迁移，把 `el_pages.ocr_json`
  非空的记录置为 `{}`；`reverse_code=migrations.RunPython.noop`（不可逆）。
  备选：写成 management command 手工执行 —— 否决：需各环境各跑一次，容易漏，且与 0013 的数据迁移惯例不一致。
- 不清理：`di_snapshots.ocr_json`（快照本体，OCR 展示/回放依赖）与 `inspector/thumbs/**/ocr_*.png`
  （随快照删除清理，不属页面资产）。

## 模块防火墙自检

- 前端改动仍限 `frontend/src/modules/device-inspector/`；后端改动限 `apps/device_inspector`（自有模块）
  与 `apps/element_locator` 的一条数据迁移。
- 写库路径：页面级 OCR 的下线是**收窄**既有写库参数——`device_inspector.api` 仍经
  `element_locator.api.import_snapshot_page` 写 `el_` 表，跨 App 仍只走对方 `api.py`，不新增直接 ORM 写。
  本次新增的数据迁移属 `element_locator` 自有 Model 的数据订正，由该 App 自己的迁移承载（合规）。
- 无新增跨 App import：`device_inspector` 对 `element_locator` 的依赖与本次之前完全一致
  （`ImportConflictError` / `import_snapshot_page` / `get_page_full`）。
- 前端 HTTP 出口仍是模块唯一出口 `device-inspector/api.ts`（内部走 `@/shared/api-client`），
  不新增端点、不绕过 `api-client`、不新增 WS/SSE。
- 跨模块依赖仅既有两项：`@/shared/ocrMatch`（`mergedRows` 继续服务 `saveToElements`）与
  `@/modules/element-locator/api`（弹窗/选择器既有用法），本次不改其调用方式。
- 共享件与全局令牌零改动，模块私有样式仍落在 `.inspector-workbench` 作用域内。

## Risks / Trade-offs

- [「仅 OCR」快照在新视图下元素表格为空（结构表格只消费 dump 元素）] → 手机屏幕仍叠加显示 OCR 文本、
  页脚仍统计 OCR 条数、快照列表仍显示 OCR 计数；与变更前「结构分析」视图口径一致，不新增回归。
- [存量 OCR 清空不可逆，且与「保留元素定位自身导入端点」不一致] → 本次按用户确认执行全量清空；
  `import_snapshot_page` 的 `ocr_json` 入参保留意味着此后经元素定位自身导入端点仍可写入页面级 OCR。
  若后续要求「OCR 在元素定位彻底不存在」，需另开变更下线该端点的 `ocr_json`。
- [迁移在其它环境一并清空历史 OCR] → 迁移前备份 `el_pages`；`reverse` 为空操作，回滚只还原代码不还原数据；
  执行窗口与发布同步。
- [勾选行键失配会静默保存全部元素] → D3 统一行键；验收加一条「勾 3 行保存后元素定位只多 3 个元素」。
- [灰键脱离原生 disabled，可访问性语义变弱] → 保留 `aria-disabled="true"`、键盘可达与点击提示，
  并在规格中写明该表达方式。
- [已保存页面无分区数据] → 分区列空态 + 指标列 `—`，不伪造 role/metrics（D2）。
- [用户习惯「点结构分析才出分区」] → 获取/回看自动分区取代该动作；工具条不再出现该按键，
  元素表格空态文案同步说明「获取 Dump 快照后显示」。

## Migration Plan

- 发布顺序：先发后端（`include_ocr` 入参删除 + 迁移 0014）再发前端；前端在该窗口内仍会发送
  `include_ocr`，后端忽略未知字段（DRF `request.data` 取值式解析，不报错），故先后顺序不阻塞。
- 数据：`python manage.py migrate` 会执行 `element_locator/0014_clear_page_ocr_json`，清空 `el_pages.ocr_json`；
  执行前请备份 `el_pages` 表（不可逆）。
- 回滚：还原代码提交；数据侧无反向迁移，需从备份恢复 `el_pages.ocr_json`。
- 门禁：`python manage.py check`、`makemigrations --check`、`ruff check apps/device_inspector apps/element_locator`、
  `pytest -m "unit or integration"`、`npm run lint:styles`、`npx vite build`，并按 tasks 的手工走查清单核对需求。
