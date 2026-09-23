## Why

「保存到元素定位」在元素表改为展示**全量元素**后，因下标口径冲突被前端冻结（`SAVE_TO_ELEMENTS_FROZEN`）；冻结期间保存链路本身也与需求脱节：勾选集合从未进入请求体、元素定位侧存了一份用不上的整屏截图副本，且元素定位的数据呈现（表列 / 新增表单 / 行内编辑 / 接口返回 / 写入白名单）与元素字段的真实口径对不上。

本变更把两侧**同批**改到位：检查器侧解冻并按新口径保存；元素定位侧把元素字段与呈现一并收敛，使「保存什么」与「看什么、改什么」出自同一套字段。

**前置依赖**：另一在途变更 `element-locator-element-table-editing`（元素表分页 / 双击行内编辑 / 新增一行 / 批量删除，任务已全绿）正在改同一批文件与同两条 `element-locator-page-workbench` 要求。本变更 MUST 在它**归档之后**以其归档后的主规格为基线落地：保留它的分页、新增、批量删除与双击编辑能力，只收敛「呈现列 + 可编辑字段 + 写入白名单」。

## What Changes

**检查器侧（保存）**

- **解冻入口**：去掉前端冻结开关，「保存到元素定位」在页面已有快照（存在 `snapshot_id`）时可用；无快照与「已保存页面」回看态仍为灰键并按既有口径提示。
- **勾选必选**：未勾选任何元素时点击「保存到元素定位」MUST 提示「至少勾选一个元素才能保存」，MUST NOT 打开保存弹窗、MUST NOT 发起请求；弹窗内确认保存时同一校验再执行一次。
- **下标口径对齐**：勾选集合以快照**全量元素的坐标顺序序号**（1 基，与检查器表格「序号」列同值）为唯一口径。**BREAKING**：`POST /api/inspector/snapshots/{id}/save-elements` 的 `element_ids` 由「展示保留集的 0 基下标」改为「全量元素的 1 基坐标顺序序号」；序号越界返回 400（不再静默丢弃）。
- **缩略图**：保存时按待保存元素的 bounds 从该快照**已存的整屏截图**裁剪缩略图（检查器侧裁剪），复制到元素定位自有目录并指向副本；不重新抓取设备画面。截图缺失或裁剪失败时该元素缩略图留空并记录告警，保存不失败。
- **不再保存 / 关联截图**：导入路径 MUST NOT 复制整屏截图，页面 `screenshot_path` 导入后保持为空，元素定位记录 MUST NOT 引用检查器媒体路径；检查器快照自身的截图照旧保留。
- **只保存六项**：写入元素记录的信息收敛为**缩略图、元素名称（别名）、序号、文本、主定位（表达式 + 是否稳定）、交互标注（七项交互标志）**；不再写入类名、内容描述、屏幕坐标、层级深度、父内序号与候选 XPath 列表。`resource_id` 与 `bounds` 仍写入，作为去重键。

**元素定位侧（数据格式与呈现，与保存同批变更）**

- **元素表列集合收敛**：改为**缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点**七列（去掉 resource-id 与坐标列），缩略图列渲染真实图片、交互标注列渲染七项标志。
- **可编辑面收敛**：行内可编辑只剩**元素名称 / 文本 / 主定位 / 测试点**；缩略图、序号、交互标注保持只读（采集产物）。
- **新增一行表单同步**：字段收敛为元素名称（必填）、resource-id、坐标、文本、主定位、备注、测试点；去掉 class 与 content-desc 输入；resource-id 与坐标作为去重键只在新增表单出现。
- **主定位成为一等字段**：新增 `primary_xpath`（+ `primary_stable`），写入口径为单条主定位；元素列表响应不再返回候选列表与页面截图路径。
- **写入白名单与校验唯一口径**：检查器导入、新增一行、行内更新共用同一字段规整口径；更新入参只接受可编辑四字段，其它字段 MUST 被拒绝（400）而不是静默忽略。
- **不动**：`el_elements` 既有列不删（历史数据与手工 / AI 写入入口仍用），`(page, resource_id, bounds)` 唯一约束不变；快照保留上限、删除 / 清空与媒体引用判定、分层端点、检查器元素表列集合。

**删除「已保存页面」功能（本次一并做）**

- 入口与只读回看链路整体删除，不留冻结壳：`components/SavedPagePicker.vue`、`store.viewSavedPage` / `SAVED_PAGE_FROZEN` / `pickerVisible`、`apiGetPageView`、`FROZEN_REASONS`。
- 连带删除其专属后端读口：`GET /api/inspector/pages/{id}`（`device_inspector.views.page_view` + `api.get_page_view`）与 `element_locator.api.get_page_full`（含 `_element_dict`）。
- 规格侧：`device-inspector-page` 删除「已保存页面选择器按行展示」「已保存页面入口冻结」两条要求，并把四条提及回看的既有要求（按键可用性 / 手机屏幕换算 / 失效媒体降级 / 结构视图唯一）改写为快照口径；`frontend-doodle-button` 与 `frontend-l5-overlay` 的示例清单同步去掉该弹层。

## 关联文档

- PRD-03（设备检查器）
- PRD-04（元素定位）

## Capabilities

### New Capabilities

- `inspector-save-to-elements`: 从检查器勾选元素保存到元素定位的完整契约——勾选序号口径、必选校验、写入元素定位的字段集、缩略图生成来源、导入不携带整屏截图。
- `element-locator-element-fields`: 元素定位的元素字段集合与呈现口径——字段集合是唯一口径、呈现列集合、列表响应字段（写入白名单与错误码由 `element-locator-page-workbench` 的「元素行增删改接口契约」收窄）。

### Modified Capabilities

- `device-inspector-page`: 「元素表格勾选驱动筛减保存」的勾选范围口径（下标→序号）、跨分组/跨页保持的口径与未勾选提示文案。
- `device-inspector-snapshots`: 「导入到元素定位时复制媒体到元素定位自有目录」收敛为只复制元素缩略图，不再复制整屏截图、不再写页面 `screenshot_path`。
- `element-locator-page-workbench`: 元素工作台的呈现列集合与行内可编辑字段集合（按前置变更 `element-locator-element-table-editing` 归档后的主规格重写）。
- `frontend-doodle-button`: 「Device-inspector keys adopt the hard-edge skin」的示例按键清单去掉「已保存页面」。
- `frontend-l5-overlay`: 「Overlay close policy follows input-bearing content」的只读弹层清单去掉「已保存页面选择」。

## Impact

- 后端（检查器）：`apps/device_inspector/api.py`（序号解析、缩略图裁剪与清理）、`views.py`（入参校验与错误码）、`service.py`（复用整屏截图裁剪实现）
- 后端（元素定位）：`apps/element_locator/models.py` + 新增迁移（`seq` / `primary_xpath` / `primary_stable` / `long_clickable` / `checkable` / `focusable`）、`api_snapshot.py`（字段集收敛、不落截图、缩略图副本）、`element_fields.py`（写入白名单与校验唯一口径）、`api.py`（元素 CRUD 写函数）、`views_page_elements.py`（列表响应字段与更新入参）、`views_page_element_batch.py`、`views_snapshot.py`（导入端点不再接受截图）
- 前端（检查器）：`frontend/src/modules/device-inspector/{store.ts,index.vue,constants.ts,api.ts,components/SaveToElementsDialog.vue}`；删除 `components/SavedPagePicker.vue`
- 后端（删除读口）：`apps/device_inspector/{views.py,urls.py,api.py}`、`apps/element_locator/{api.py,api_snapshot.py}`
- 前端（元素定位）：`components/PageElementsWorkbench.vue`（列集合、缩略图与交互标注渲染、可编辑面）、`components/PageElementFormDialog.vue`（新增表单字段）、`components/EditableCell.vue`（只用于四个可编辑列）、`composables/usePageElements.ts`（行 DTO 与更新映射）、`helpers/elementRowValidation.ts`（校验列集合同源）、`api.ts`（入参与 DTO 类型）
- 测试：`tests/graybox/unit/test_inspector_save_elements.py`（新增）、`tests/graybox/integration/test_inspector_save_element_aliases.py` 与 `test_inspector_snapshot_media.py`（媒体口径改写）、元素定位侧元素字段用例（新增 / 改写）、`tests/api/case/inspector.yaml`、`frontend/tests/device-inspector/`、`frontend/tests/element-locator/`
- 文档：`API-设备检查器.md`（save-elements 入参）、`API-元素定位.md`（元素字段、列表响应、更新白名单）、`PRD-03-设备检查器.md`、`PRD-04-元素定位.md`
