## 0. 前置（顺序门）

- [x] 0.1 `element-locator-element-table-editing` 已于 2026-09-23 归档（`openspec/changes/archive/2026-09-23-element-locator-element-table-editing/`），主规格已含其分页条款与「元素行增删改接口契约」；本变更 delta 已按归档后基线补齐（两条换代要求 REMOVED + ADDED、接口契约 MODIFIED），`openspec validate rework-save-to-elements --type change --strict` 通过
- [x] 0.2 复核元素定位呈现面勘测清单与实现一致（列定义 / 表单字段 / 行 DTO / `element_fields.py` 白名单 / `views_page_elements.py` 响应字段），勘测结论落在 `design.md` 的背景表

## 1. 后端：检查器保存契约（序号口径 + 缩略图裁剪 + 不落截图）

- [x] 1.1 `apps/device_inspector/api.py`：`element_ids` 改为「全量节点索引 1 基坐标顺序序号」，按 `snapshot.nodes_json` 经 `build_layers` 取元素；越界/非整数 → `ValueError`。验证：`test_inspector_save_elements.py::test_save_keeps_only_selected_seqs` / `::test_save_rejects_out_of_range_seq` 通过
- [x] 1.2 同文件 + `apps/device_inspector/service.py` 新增 `crop_save_thumbnails`：按 bounds 从快照整屏截图裁剪缩略图，截图缺失/无尺寸/裁剪失败 → 留空 + 告警。验证：`::test_save_crops_thumbnail_from_snapshot_screenshot`（裁剪出 10×10）/ `::test_save_keeps_thumbnail_empty_when_screenshot_missing` 通过
- [x] 1.3 `apps/device_inspector/views.py`：入参 docstring 与错误码对齐（越界 → 400）；`element_aliases.index` 语义改为序号。验证：`test_inspector_save_element_aliases.py` 四例通过
- [x] 1.4 保存不再向元素定位传 `screenshot_path`（`import_snapshot_page` 已删除该入参）。验证：`::test_save_writes_only_converged_fields_and_no_screenshot` 断言页面 `screenshot_path == ""`

## 2. 后端：元素定位字段集合与迁移（五个呈现面的源头）

- [x] 2.1 `apps/element_locator/models.py` 新增 `seq` / `primary_xpath` / `primary_stable` / `long_clickable` / `checkable` / `focusable` + 迁移 `0016_element_checkable_element_focusable_and_more`。验证：`makemigrations --check --dry-run` → No changes detected
- [x] 2.2 `apps/element_locator/api_snapshot.py`：`import_snapshot_page` 写入收敛为六项 + 去重键，删除整屏截图复制；`_copy_into_locator` 源缺失/复制失败一律留空 + 告警。验证：`test_inspector_snapshot_media.py` 四例（副本 / 删快照后副本仍在 / 留空告警 / 不串图）通过
- [x] 2.3 `apps/element_locator/element_fields.py`：`UPDATE_FIELDS`（四字段）与 `CREATE_FIELDS`（+ 备注与去重键）分离，`normalize_element_fields(raw, allowed)` 越界即 `ValueError`，人工主定位 `primary_stable=False`。验证：`test_element_row_crud.py` 十五例通过
- [x] 2.4 `api.py` / `views_page_elements.py`：列表与单元素 payload 收敛（新增 `seq` / `primary_xpath` / `primary_stable` / 三项标志；移除候选列表与 `screenshot_path`）。验证：`test_element_row_crud.py::test_update_persists_editable_fields`（人工主定位不稳定）与 `::test_update_rejects_out_of_scope_fields` 通过
- [x] 2.5 legacy 端点同口径：`add_element_to_page` / `batch_add_elements` 统一走 `normalize_element_fields`，`import_snapshot` 不再接受 `screenshot_path`；AI 保存链路经同一函数收敛。验证：`python -m pytest tests/graybox -q` → 491 passed

## 3. 前端：检查器保存链路（解冻与必选校验）

- [x] 3.1 `store.ts`：删除 `SAVE_TO_ELEMENTS_FROZEN` 与守卫；新增 `checkedSeqs()` / `checkedCount`，`element_ids` 下发整数序号、`element_aliases.index` 同步为序号。验证：`store.spec.ts`「勾选后请求体按元素序号组装」通过
- [x] 3.2 `store.ts` + `index.vue`：入口守卫（未勾选不打开弹窗、不发请求）+ 弹窗确认同一校验，文案统一取自 `NO_SELECTION_MESSAGE`。验证：`store.spec.ts`「未勾选任何元素时提示…且不发请求」通过
- [x] 3.3 `constants.ts`：删除 `FROZEN_REASONS.saveToElements`，新增 `NO_SELECTION_MESSAGE` 与 `KEY_DISABLED_MESSAGE`（原 `store.ts` 内的重复字面量一并收敛）。验证：`npx vitest run tests/device-inspector` 通过
- [x] 3.4 `index.vue`：按键底色按 `canSaveToElements`（有 `snapshot_id`）切换，无快照时灰底 + `KEY_DISABLED_MESSAGE`。验证：`npx vue-tsc --noEmit` 无本模块报错

## 4. 前端：元素定位呈现（与 2.x 同批）

- [x] 4.1 `PageElementsWorkbench.vue`：列集合改为缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点（保留分页、双击编辑、新增一行与批量删除）；缩略图列渲染图片并处理失效占位，交互标注列渲染七项标志。验证：`PageElementsWorkbench.spec.ts` 五例通过
- [x] 4.2 `EditableCell.vue` + `usePageElements.ts`：行 DTO 与更新映射收敛（`seq` / `primary_xpath` / `primary_stable` / 七项标志），去掉 `bounds→坐标四件套` 与 `xpath→候选列表` 的旧映射。验证：同上前端用例 + `vue-tsc` 通过
- [x] 4.3 `PageElementFormDialog.vue`：字段收敛为元素名称（必填）/ resource-id / 坐标 / 文本 / 主定位 / 备注 / 测试点，去掉 class 与 content-desc 输入。验证：`vue-tsc` 通过（`TextField` 联合类型与后端同源）
- [x] 4.4 `api.ts` 的 `PageElementFields` 与 `helpers/elementRowValidation.ts`：类型与校验列集合与后端一致（`TEXT_MAX_LENGTH` 只留 alias / text_val / primary_xpath / resource_id；`validatePrimaryXPath` 取代 `validateXPath`；`firstXPath` / `parseBounds` 随旧口径移除）。验证：`elementRowValidation.spec.ts` 五例通过

## 5. 测试与门禁

- [x] 5.1 新增保存契约用例（落位 `tests/graybox/integration/test_inspector_save_elements.py`，需 `django_db` 故放集成层）：序号筛减 / 越界 400 / 六项字段与不落截图 / 缩略图裁剪 / 截图缺失降级 —— 5 例通过
- [x] 5.2 元素定位侧用例：`test_element_row_crud.py` 改写为收敛口径（越界字段 400、人工主定位不稳定、坐标仍解析为去重键）；`test_inspector_save_element_aliases.py` 改用 `nodes_json` 与序号语义（含越界拒绝）
- [x] 5.3 `test_inspector_snapshot_media.py` 第二节按新媒体口径重写（只复制缩略图、页面不落截图、源缺失留空）
- [x] 5.4 前端用例：`store.spec.ts`（+2 例：勾选必选与序号请求体）、`PageElementsWorkbench.spec.ts`（新增 5 例：七列 / 缩略图占位 / 交互标注 / 序号 / 可编辑面）、`elementRowValidation.spec.ts`（改写 5 例）
- [x] 5.5 门禁：`manage.py check` 0 issues · `makemigrations --check` 无差异 · `ruff check + format` 通过 · `pytest tests/graybox` **491 passed** · `npx vue-tsc --noEmit` 仅余 3 条既有 `ProjectTree.vue` 报错 · `vite build` ✓ · `npm run lint:styles` 四批通过 · `npx vitest run` **56 files / 311 tests passed** · `openspec validate rework-save-to-elements --type change --strict` 通过

## 7. 删除「已保存页面」功能

- [x] 7.1 前端：删除 `components/SavedPagePicker.vue`（文件已删）；`index.vue` 去掉入口按键 / `SavedPagePicker` 挂载 / `onFrozenClick` / `FROZEN_REASONS` 引用；`store.ts` 去掉 `SAVED_PAGE_FROZEN` / `viewSavedPage` / `pickerVisible` / `apiGetPageView`；`api.ts` 去掉 `apiGetPageView`；`constants.ts` 去掉 `FROZEN_REASONS`；`StructureAnalysisPanel.vue` / `ScreenshotView.vue` 的回看口径注释与提示文案改掉。验证：全仓（排除归档）检索 `SavedPagePicker|viewSavedPage|apiGetPageView|FROZEN_REASONS|SAVED_PAGE_FROZEN|pickerVisible` 只剩变更产物；`npx vue-tsc` 仅余 3 条既有 `ProjectTree.vue` 报错
- [x] 7.2 后端：删除 `device_inspector.views.page_view` 与路由、`api.get_page_view` 与 `__all__` 条目；删除 `element_locator` 的 `get_page_full` / `_element_dict` 与 `__all__` 条目。验证：`python manage.py check` 0 issues、`ruff check` 通过、全仓检索 `get_page_view|get_page_full` 只剩变更产物与两条文档说明
- [x] 7.3 测试与用例：删除 `tests/api/case/inspector.yaml` 的 TC-INS-007 / TC-INS-070 两条页面回看用例；`frontend/tests/device-inspector/p0/store.spec.ts` 删除冻结入口用例与 `apiGetPageView` mock；`SnapshotListDrawer.spec.ts` 同步删除 mock。验证：`pytest tests/graybox tests/api` **551 passed**、`npx vitest run` **56 files / 310 tests passed**
- [x] 7.4 文档：`API-设备检查器.md` 删除 §9 与总览行；`PRD-03` 删除「已保存页面只读回看」整节与其测试节、更新工具条 / 覆盖层 / 入口可用性 / 保存节 / 缺口与附录（误删的「删除快照」测试节已恢复）；`PRD-需求总纲` 设备检查器能力条目去掉「已保存页面回看」；`PRD-04` 的跨模块读口描述改为「只写不读」。验证：检索无残留的可用口径表述

## 8. 修复：dev 库迁移与保存弹窗目录来源（联调反馈）

- [x] 8.1 **dev 库迁移漏跑**（保存失败 + 元素表查不出数据的共同根因）：`0016_element_checkable_element_focusable_and_more` 只在 `makemigrations` 生成、未 `migrate`，dev 库缺 `el_elements.seq`/`primary_xpath`/`primary_stable`/三项交互标志 → 任何 `Element` 查询抛 `(1054, "Unknown column 'el_elements.seq'")`：保存链路 500「保存失败」、元素定位元素表整表查不出。已执行 `python manage.py migrate element_locator`（0016 OK），并在 design 的门禁清单里把 `migrate` 列为必跑项
- [x] 8.2 **保存弹窗的目录来源用了退役的 legacy 口径**：`SaveToElementsDialog.vue` 从 `/elements/pages/` 按 `is_folder` + `parent_id` 过滤目录；项目化迁移（0013）后目录独立成 `el_locator_directories`、`Page.parent_id` 恒空，故级联永远为空（看不到「测试目录 / govee」）。已改为读取元素定位项目树 `GET /api/elements/projects/android/tree/`：目录节点构级联（value = 目录名，后端按名字逐段解析）、页面下拉取所选目录下的 file 节点
- [x] 8.3 验证：`temps/verify_save_path.py` 在 dev 库实跑 —— 快照 369（137 节点）以 `folder_path="测试目录 / govee"`、`element_ids=[1]` 保存 → `{'saved': 1, ...}`，落页 `directory_id=5 → govee`、`screenshot_path` 为空、元素 `seq=1` 且缩略图副本文件存在，验证后删除临时页面（`cleaned: True`）；`npx vitest run tests/device-inspector tests/element-locator` 49 例通过、`vue-tsc` 无本模块报错

## 6. 文档

- [x] 6.1 `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`：save-elements 的序号语义、`element_aliases`、六项字段、缩略图裁剪、不落截图、新错误码；§9 页面只读视图示例同步
- [x] 6.2 `dev_docs/DEV_TEST/接口文档/API-元素定位.md`：元素列表响应收敛、添加/批量/更新的字段白名单与拒绝口径、`import-snapshot` 不再接受截图
- [x] 6.3 `dev_docs/ARCH_PRD/PRD-03-设备检查器.md`（解冻、勾选必选、六项字段、序号口径、附录第 10 条）与 `PRD-04-元素定位.md`（元素表七列与可编辑四项、接口契约、`el_elements` 列、快照导入）
