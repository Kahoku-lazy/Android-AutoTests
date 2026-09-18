## Why

设备检查器（`/inspector`）当前默认落在「元素列表」视图：进页面看不到页面分区与手机屏幕，
必须先点「结构分析」才有内容；工具条按键用 `disabled` + `opacity .5` 表达不可用，用户看不出
「应该先选设备」；布局把手机屏幕放在最左，页面分区被夹在中间；元素列表与结构表格信息高度重叠，
而结构表格又无法勾选筛减。用户据此提出四项显示需求（默认内容 / 按键蓝灰 / 三栏布局 /
去元素列表页 + 表格勾选保存），需要一次性收敛为单一结构视图。

## What Changes

- **默认内容**：进入 `/inspector` 即渲染完整骨架（工具条、筛选栏、页面分区、元素表格、手机屏幕），
  不再需要先点「结构分析」；快照获取（`capture`）与快照回看（`viewSnapshot`）后自动请求分区分析。
- **BREAKING（规格层面）删除元素列表页**：移除 `store.viewMode` 与「结构分析」「返回元素列表」两个按键，
  删除 `components/PageElementsPanel.vue`（dump/OCR 合并行表格）。结构表格成为唯一表格。
- **三栏布局**：从左到右 = 页面分区 → 元素表格 → 手机屏幕（现状为手机屏幕 → [页面分区+表格]）。
- **BREAKING（规格层面）按键可用性**：可用按键天蓝底（`--c-workflow`），不可用按键灰底；
  不可用按键不再使用原生 `disabled`，保持可点击并统一提示「按键不可用，请先选择设备」。
  据此 `frontend-doodle-button` 中「Disabled key drops its offset shadow」与
  「Dark-background key keeps readable text」两条 Scenario 必须改写。
- **勾选保存**：结构表格新增选择列（含表头全选），勾选集合沿用既有 `checkedIds`（键 `d<元素下标>`）
  与 `save-elements` 契约，勾选 = 保存到元素定位的筛减范围；未勾选任何行时仍提示先勾选。
- **已保存页面回看**：由元素列表改为同一张结构表格展示（已保存页面无分区数据，页面分区列显示空态、
  指标列显示 —）；该视图无 `snapshot_id`，「保存到元素定位」按键呈灰键。
- **去掉 OCR 落库**：保存到元素定位不再写入页面级 OCR——前端移除弹窗「OCR 数据」开关与
  `include_ocr` 载荷，后端 `save-elements` 端点删除 `include_ocr` 参数并始终以 `ocr_json=None` 落库
  （**BREAKING**：`API-设备检查器.md` 的 `include_ocr` 字段退役）；并以数据迁移清空
  `el_pages.ocr_json` 的全部历史数据（存量清理，不可逆）。
- **不破坏性**：后端只收窄 `save-elements` 一个端点的入参，其余 6 个端点与 `snapshot`/`analysis`
  字段口径不变；元素定位自身的快照导入接口（`views_snapshot` 的 `ocr_json`）不改；
  共享件 `AppTable` / `FilterTabs` / `ErrorState` 与 `tokens.css` MUST NOT 修改。

## 关联文档

- `dev_docs/ARCH_PRD/PRD-00-需求总纲.md`：设备检查器条目（一键 dump/OCR 快照落库 · 快照回看/删除 · 筛减导入元素定位 · 已保存页面回看）为本次四项显示需求的功能边界。
- `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`：7 端点契约真相源；本次删除 `save-elements` 的
  `include_ocr` 字段，需双边同步。
- `dev_docs/DEV_TEST/接口文档/API-元素定位.md`：`el_pages.ocr_json` 字段的对外形态（页面只读视图仍返回该字段，
  存量数据被清空后为 `null`）；本次不改该模块接口，只清理数据。
- `dev_docs/ARCH_PRD/PRD-03-设备检查器.md` **不存在**（PRD-00 仍引用该编号，文件已移除），故本次不引用 PRD-03。
- `openspec/specs/frontend-doodle-button/spec.md`：设备检查器按键皮肤要求，本次经 delta 修改。
- `openspec/specs/frontend-l4-data-surface/spec.md`：表格行状态与选择列口径，本次经 delta 修改。

## Capabilities

### New Capabilities

- `device-inspector-page`：设备检查器页面（`/inspector`）的默认呈现内容、唯一结构视图与自动分区、
  三栏布局顺序、按键可用性的颜色与提示表达、结构表格勾选与筛减保存。

### Modified Capabilities

- `frontend-doodle-button`：「Device-inspector keys adopt the hard-edge skin」的底色与状态表达改变
  （可用天蓝 / 不可用灰 + 点击提示），退役墨黑底「获取」与 `disabled opacity .5` 两条 Scenario。
- `frontend-l4-data-surface`：「Table row state stays visible」的 Scenario 由「元素面板或结构面板」
  改为唯一的结构表格。

## Impact

- 前端页面：`frontend/src/modules/device-inspector/`
  - 修改：`index.vue`（三栏布局、按键可用性、筛选栏常驻、去视图切换）、`store.ts`（去 `viewMode`、
    分区行键与筛减口径、已保存页面映射、自动分析、灰键提示、去 `include_ocr`）、
    `components/StructureAnalysisPanel.vue`（选择列 + 空分区兜底）、
    `components/CaptureForm.vue`（「获取」可用性表达）、
    `components/SaveToElementsDialog.vue`（删除「OCR 数据」开关）
  - 删除：`components/PageElementsPanel.vue`
- 后端：
  - 修改：`apps/device_inspector/views.py` 与 `apps/device_inspector/api.py`（删除 `include_ocr`，
    保存恒不写页面级 OCR）
  - 新增：`apps/element_locator/migrations/0014_*.py`（数据迁移：清空 `el_pages.ocr_json`，`reverse` 为空操作）
  - 不改：`apps/element_locator/api_snapshot.py` 的 `ocr_json` 入参（元素定位自身导入接口仍在用）
- 文档：`dev_docs/DEV_TEST/接口文档/API-设备检查器.md`（删除 `include_ocr` 行与相关说明）
- 规格：新增 `openspec/specs/device-inspector-page/spec.md`；delta 修改 `frontend-doodle-button`、
  `frontend-l4-data-surface`
- 测试：`frontend/tests/` 现无 device-inspector 用例（`tests/README.md` 记为「未开始」），本次不新增
  自动化用例，验收走既有门禁（`npm run lint:styles`、`npx vite build`）+ 手工走查四场景
