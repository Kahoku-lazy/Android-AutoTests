## 1. 后端：必填口径与冲突文案

- [x] 1.1 `apps/element_locator/element_fields.py` 在 `normalize_element_fields` 里补「更新时元素名称非空」校验（提交为空串 → `ValueError`，中文原因），与既有 `primary_xpath` 非空校验同一处。验证：`python -m ruff check apps/element_locator` 通过，且 2.1 的「清空元素名称被拒」用例通过。
- [x] 1.2 `apps/element_locator/api.py#create_element` 命中同页既有 `(resource_id, bounds)` 时，先取既有行的 `id` 与 `alias`（`only()`），`ConflictError` 文案改为「该元素已在当前页面中：<元素名称>（id=<n>）」，既有名称为空时只给 id。验证：2.1 的「409 文案指认既有元素」用例通过。
- [x] 1.3 复核 `apps/element_locator/views_page_elements.py` 的两个视图仍只做参数解析与错误码映射（400 / 409 透传），状态码与路径不变。验证：`python manage.py check` 0 issues。

## 2. 后端测试

- [x] 2.1 `tests/graybox/integration/test_element_row_crud.py` 增补三组用例：更新把 `alias` 提交为空串 → 400 且库中值不变；更新只提交 `text_val` → `alias` / `primary_xpath` / `is_test_point` 不变；手动新增撞去重键 → 409 且原因含既有元素名称（既有名称为空时含其 id）。验证：`python -m pytest tests/graybox/integration/test_element_row_crud.py -v` 全通过。

## 3. 前端：校验口径与勾选保留

- [x] 3.1 `frontend/src/modules/element-locator/helpers/elementRowValidation.ts` 新增元素名称非空校验（返回中文原因或 `null`），表格与新增弹窗共用；`frontend/tests/element-locator/p0/elementRowValidation.spec.ts` 增补用例。验证：`cd frontend && npx vitest run tests/element-locator/p0` 通过。
- [x] 3.2 `composables/usePageElements.ts#load` 增加「保留勾选」选项：失败重载路径保留仍然存在的元素 id，默认行为与切换页面、批量删除成功后仍清空勾选。验证：`npx vitest run tests/element-locator/p0`（含新增的勾选保留用例）通过。
- [x] 3.3 `components/PageElementsWorkbench.vue` 把元素名称列接上非空校验，并确认新增撞车时原样展示后端原因（含既有元素指认）。验证：`cd frontend && npm run build` 通过，工作台用例通过。

## 4. 前端：wire DTO 类型化与死代码

- [x] 4.1 `types.ts` 新增页面元素 wire DTO（元素 payload / 列表响应 / 写入响应）；`api.ts` 的 5 个 legacy 封装改用这些类型与 `Envelope`；`usePageElements.ts` 删除就地断言、`PageElementRow.primary_stable` 与 `toRow` 中该字段。验证：`cd frontend && npx vue-tsc --noEmit` 在本模块 0 错。
- [x] 4.2 `composables/useLocatorTree.ts#createdLeafId` 只认 `page.id`，删除 `payload.data.id` 死分支。验证：`npx vue-tsc --noEmit` 0 错，且新建页面后仍能跳转到该页面详情。
- [x] 4.3 删除零消费代码：`api.ts` 的 `apiGetPages`；`components/PageElementFormDialog.vue` 里对空值恒不触发的 `validatePrimaryXPath` 调用分支（长度校验保留）。验证：全仓 grep 零引用，`npx eslint src/modules/element-locator` exit 0。

## 5. 前端：详情页与面板收敛

- [x] 5.1 `LocatorFileView.vue` 改为直接调用 `apiDeletePage(fileId)` 并在本页处理成功/失败提示，不再构造 `useLocatorTree`；确认删除文件后不再多发一次目录树请求（进入详情页仍是 1 次）。验证：`npm run build` 通过，人工在 Network 面板确认删除后没有多余的 `projects/android/tree/` 请求。
- [x] 5.2 `components/LocatorFilePanel.vue` 删除 `hideIdentity` prop、`kindLabel` 与身份块（全仓只有 `hide-identity` 一种用法），`LocatorTree.vue` / `LocatorFilePanel.vue` 的 `deleteFile` 事件去掉恒为 `'page'` 的 `kind`，`types.ts` 删除随之零消费的 `FILE_KIND_LABELS`。验证：`npx vue-tsc --noEmit` 0 错 + `npx eslint src/modules/element-locator` exit 0。

## 6. 文档

- [x] 6.1 新增 `frontend/src/modules/element-locator/AGENTS.md`：模块边界、信封双轨登记、校验防线在后端、拖拽双通道、关单附加项；不复述根 `AGENTS.md`。验证：文件非空，内容与 `frontend/AGENTS.md` 无冲突。
- [x] 6.2 `frontend/src/modules/element-locator/tokens.css` 删除 `/* -> --color-indigo-84 */` 残留注释。验证：`cd frontend && npm run lint:styles` 通过。
- [x] 6.3 元素定位接口文档同步两条错误口径：更新提交空元素名称 → 400；手动新增撞去重键 → 409 且原因指认既有元素。验证：文档所列端点与方法同 `apps/element_locator/urls.py` 一致。

## 7. 关单门禁

- [x] 7.1 后端：`python manage.py check`、`python manage.py makemigrations --check`（本次无模型改动）、`python -m ruff check apps/element_locator`、`python -m ruff format --check <本次改动文件>`、`python -m pytest -m "unit or integration"` 全通过。
- [x] 7.2 前端：`cd frontend && npm run build`、`npm run lint`、`npm run lint:styles`、`npx vitest run tests/element-locator/p0` 全通过。
- [x] 7.3 边界：`python tools/gen_arch_stats.py --check-boundaries` 零违规。
- [ ] 7.4 人工验收：对照本次两个 delta 的新增 / 修改场景走查——清空元素名称被拒、撞车提示指认既有元素、单格更新失败后勾选仍保留、新增撞车文案可见、更新只提交部分字段时其余不动。