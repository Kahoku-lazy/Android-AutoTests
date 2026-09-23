## 1. 后端：更新与新增的校验口径

- [x] 1.1 `apps/element_locator/api.py#update_element` 扩写可写白名单为定位业务字段（`alias/text_val/content_desc/class_name/resource_id/bounds/xpath_candidates/clickable/enabled/scrollable/checked/is_test_point/notes/tags`），并对越界输入做逐列校验：`bounds` 必须匹配 `[x1,y1][x2,y2]` 且 `x2>=x1`、`y2>=y1`，字符串长度不超模型列宽，`xpath_candidates` 必须是合法 JSON 数组；非法时抛 `ValueError`。验证：`python -m ruff check apps/element_locator` + 3.1 的拒绝用例通过。
- [x] 1.2 同文件：当入参含 `bounds` 时，`update_element` MUST 解析出 `x/y/width/height` 并随同一次 UPDATE 写入。验证：3.1 的「bounds 与坐标分量一致」用例通过。
- [x] 1.3 `apps/element_locator/views_page_elements.py#update_element` 视图改为返回真实结果：成功 `{status:true}`；元素不存在 `404`；非法输入 `400` 并带中文原因（不再对任意 id 一律 `{status:true}`）。验证：3.1 对应用例通过 + `python manage.py check`。
- [x] 1.4 `views_page_elements.py#add_element_to_page` 改为**仅新增**：命中同页既有 `(resource_id, bounds)` 时返回 `409`（不再 upsert 覆盖）；补「resource_id 与 bounds 至少填一个」校验，两者皆空返回 `400`；`xpath` 输入写为单条 `{"type": "manual", "xpath": <值>, "count": 1}` 候选。验证：3.1 的新增成功 / 缺必填 / 撞唯一约束三组用例通过。

## 2. 后端：元素批量删除

- [x] 2.1 `apps/element_locator/api.py` 新增 `delete_elements(*, element_ids)`：空集合抛 `ValueError`、任一 id 不存在抛 `LookupError`（整批不落库）、成功在单个 `transaction.atomic()` 内删除并返回 `{"deleted": n}`；在 `__all__` 登记。验证：3.1 的批量删除三组用例通过。
- [x] 2.2 `apps/element_locator/views_page_element_batch.py` 新增 `batch_delete_elements` 视图（`@api_view(["POST"])`，body `{ids:[int]}`，错误经 `_raise_or_conflict` 风格映射 400/404），`urls.py` 注册 `path("items/batch-delete/", batch_delete_elements, name="el_items_batch_delete")`。验证：`python manage.py check` 0 issues。
- [x] 2.3 `tests/graybox/unit/test_element_locator_views_split.py` 的 `LEGACY_ROUTES` 增补 `("items/batch-delete/", "el_items_batch_delete", None)`。验证：`python -m pytest tests/graybox/unit/test_element_locator_views_split.py -q` 通过。

## 3. 后端测试

- [x] 3.1 新增 `tests/graybox/integration/test_element_row_crud.py`（`pytest.mark.django_db` + `pytest.mark.element_locator`）：各定位列更新后持久化；改 `bounds` 时 `x/y/width/height` 同步；非法 `bounds` / 负数尺寸被拒（值不变）；新增成功；新增缺必填 400；新增撞唯一约束 409；批量删除成功返回条数；空集合 400；含不存在 id 404 且整批不删。验证：`python -m pytest tests/graybox/integration/test_element_row_crud.py -v` 全通过。

## 4. 前端：校验纯函数与分页

- [x] 4.1 新增 `frontend/src/modules/element-locator/helpers/elementRowValidation.ts`：每列一个纯校验函数（bounds 形状与尺寸、数字列非负整数、字符串列宽、XPath 非空），返回中文原因或 `null`；配套单测 `frontend/tests/element-locator/p0/elementRowValidation.spec.ts`。验证：`cd frontend && npx vitest run tests/element-locator/p0` 通过。
- [x] 4.2 `components/PageElementsWorkbench.vue` 接入共享 `usePagination`（`pageSize: 10`，不提供行数选择器），新增「第 X / Y 页 · 共 N 条」与上一页 / 下一页；当接口 `total` 大于本次取回条数时展示「仅显示前 N 条」提示。验证：`cd frontend && npm run build` 通过，并人工确认默认 10 行、翻页正确。

## 5. 前端：全列编辑 / 新增 / 批量删除

- [x] 5.1 `components/PageElementsWorkbench.vue` 把 `AppTable` 插槽扩展到全部可编辑列（别名、文本、content-desc、class、resource-id、XPath、bounds、测试点、备注），采用本地行缓存 + 失焦 / 回车提交；校验不通过时就地提示并恢复原值。验证：`npm run build` 通过，并人工逐列编辑确认刷新后保持。
- [x] 5.2 工具栏新增「+ 新增一行」入口（弹窗或尾行表单），按 4.1 的校验函数校验（别名必填、resource-id 与 bounds 至少一个），成功后重载并跳到最后一页。验证：`npm run build` 通过，并人工验证缺必填被拒、成功新增可见。
- [x] 5.3 表格新增勾选列与「删除选中」动作：二次确认文案含勾选条数，确认后整批删除并清空勾选、重载并夹取页码。验证：`npm run build` 通过，并人工验证勾选 3 行删除后其余行不受影响。
- [x] 5.4 `frontend/src/modules/element-locator/api.ts` 新增 `createPageElement(pageId, body)`、`batchDeleteElements(ids)` 封装并扩写 `apiUpdateElement` 的入参类型；`frontend/tests/element-locator/p0/api.spec.ts` 增补两个端点的 method/URL/body 用例（同步文件头端点数量说明）。验证：`npx vitest run tests/element-locator/p0` 通过。

## 6. 文档同步

- [x] 6.1 元素定位接口文档补记：`PUT /api/elements/items/{id}/` 的可写字段与 400/404 口径、`POST /api/elements/pages/{id}/elements/` 改为仅新增（409）、新增 `POST /api/elements/items/batch-delete/`。验证：文档所列端点与方法同 `apps/element_locator/urls.py` 一致。

## 7. 单元格交互与新增行弹窗布局

- [x] 7.1 `frontend/src/modules/element-locator/components/EditableCell.vue` 改为默认渲染纯文本、双击才挂载 `el-input`（自动聚焦）；Enter 提交、Esc 取消、失焦提交；非法输入就地提示并恢复原值。验证：`cd frontend && npm run build` + `npx vitest run tests/element-locator/p0` 通过，并人工确认打开页面时单元格无输入框、双击可改、提交/取消后回到纯文本。
- [x] 7.2 `PageElementFormDialog.vue` 重排布局：`label-position="top"` + 两列网格（640px 宽、XPath / 备注通栏、body 限高 `60vh` 滚动、顶部一行必填提示），并把 `el-form-item` 的 `margin-bottom` 提到 `--app-space-lg`，使 Element Plus 绝对定位的错误行不再被下一格输入框遮挡。验证：`cd frontend && npm run build && npm run lint:styles` 通过，并人工触发「别名留空 / resource-id 与坐标都空 / 坐标填 abc」三种错误，确认红色文案完整可见。

## 8. 关单门禁

- [x] 8.1 后端：`python manage.py check && python manage.py makemigrations --check && ruff check apps/element_locator && ruff format --check <本次改动文件>` + `pytest -m "unit or integration"`。
- [x] 8.2 前端：`cd frontend && npm run build`、`npm run lint`、`npm run lint:styles`、`npx vitest run tests/element-locator/p0` 全通过；按 `vue-frontend-check` 量规自检布局裁剪、字号与接口契约。
- [x] 8.3 边界：`python tools/gen_arch_stats.py --check-boundaries` 通过。
- [ ] 8.4 人工验收：逐条对照 `specs/element-locator-page-workbench/spec.md` 的新增 / 修改场景走查（默认 10 行分页、翻页不丢行、各列可编辑并持久化、XPath 覆盖为单条候选、非法输入被拒且不写库、新增一行、缺必填被拒、勾选 3 行批量删除）。
