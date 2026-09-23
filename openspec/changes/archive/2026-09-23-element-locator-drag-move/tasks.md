## 1. 后端：移动校验与批量落库

- [x] 1.1 `apps/element_locator/api_directories.py` 的 `move_item` page 分支补同级重名预检（按 `(directory_id, label)`，根为 `directory_id IS NULL`，排除自身），重名抛 `ConflictError`；验证：`ruff check apps/element_locator` 通过，且 3.1 的单件重名用例通过。
- [x] 1.2 同文件新增 `batch_move_items(*, items, parent_directory_id=None)`：校验集合非空、每项 `kind` ∈ {directory, page}；目标目录解析复用 `_resolve_target_directory`；用一次 `LocatorDirectory.objects.values_list("id", "parent_id")` 建父子映射，剔除「目录祖先或页面所属目录祖先已在本批集合中」的后代；整体包 `transaction.atomic()`，逐项调用 `move_item`；返回 `{"moved", "skipped"}`；并在 `api.py` 的 `__all__` 与 import 中登记。验证：`python -m pytest tests/graybox/integration/test_locator_batch_move.py -q`（用例见 3.1）。
- [x] 1.3 `apps/element_locator/views_projects_drf.py` 新增 `batch_move_items` 视图（`@api_view(["POST"])`，body `{items: [{kind, id}], parent_directory_id}`，缺省 null 表示项目根），错误经既有 `_raise_or_conflict` 映射；`apps/element_locator/urls.py` 注册 `path("batch-move/", batch_move_items, name="el_batch_move")`。验证：`python manage.py check` 0 issues。
- [x] 1.4 `tests/graybox/unit/test_element_locator_views_split.py` 的 `LEGACY_ROUTES` 增补 `("batch-move/", "el_batch_move", None)`，与 `urls.py` 逐条对齐。验证：`python -m pytest tests/graybox/unit/test_element_locator_views_split.py -q` 通过。

## 2. 前端：拖动与批量移动

- [x] 2.1 `frontend/src/modules/element-locator/api.ts` 新增 `moveLocatorItems(body: { items: { kind: 'directory' | 'page'; id: number }[]; parent_directory_id: number | null })` → `POST /elements/batch-move/`；验证：`frontend/tests/element-locator/p0/api.spec.ts` 增补该端点用例（并同步文件头的端点数量说明），`cd frontend && npx vitest run tests/element-locator/p0` 通过。
- [x] 2.2 新增 `frontend/src/modules/element-locator/composables/useLocatorTreeMove.ts`：封装「提交移动」（单件拖动 = 1 项的批量，与勾选走同一路径）、勾选集合收集与去重、成功/失败提示、完成后 `loadTree()` 重载；`useLocatorTree.ts` 暴露 `moveItems`。验证：`cd frontend && npm run typecheck` 通过，且 3.2 的移动语义用例通过。
- [x] 2.3 `frontend/src/modules/element-locator/components/LocatorTree.vue` 接入桌面拖动：`draggable` + `allow-drag` + `allow-drop`（仅 `type === 'inner'` 且落点为目录时允许）+ `@node-drop`，并在树体顶部常驻「项目根」落点行（原生 `dragover`/`drop`，目标 `null`）。验证：`cd frontend && npm run build` 通过，并人工验证桌面拖入目录、拖回项目根、拖到页面被拒。
- [x] 2.4 同组件接入触摸端长按拖拽：`touchstart` 记录节点并启动 1 秒计时，`touchmove` 位移超阈值取消计时（视为滚动），计时到点进入拖动态后以 `document.elementFromPoint` 命中并高亮目标行、`touchend` 落点；检测到触摸输入即关闭 `el-tree` 原生 `draggable`，两条路径互斥。验证：`cd frontend && npm run build` 通过，并在触摸设备/模拟器人工验证「按住满 1 秒起拖」与「未满 1 秒为普通点击」。
- [x] 2.5 同组件接入批量选择：工具栏「批量选择」开关（开启后 `show-checkbox` + `check-strictly`，勾选不级联）、勾选计数、工具栏「移动到…」入口与新增 `components/MoveToDirectoryDialog.vue`（只列目录，含「项目根」选项）；拖动已勾选节点时整批移动；移动成功后清空勾选。验证：`cd frontend && npm run build` 通过，并人工验证目录+页面混合勾选整批移动、目录与后代同时勾选被去重。
- [x] 2.6 拆分与行数核查：确认 `LocatorTree.vue` ≤ 500 行（逻辑已迁到 2.2 的 composable，样式按需下沉），无魔法字符串与硬编码字号/色值。验证：`cd frontend && npm run lint && npm run lint:styles` 通过。

## 3. 测试

- [x] 3.1 新增 `tests/graybox/integration/test_locator_batch_move.py`（`@pytest.mark.django_db` + `pytest.mark.element_locator`）：单件移动同级重名 409、批量移动成功返回 moved 数、目录与其后代同批时去重、目录移入子孙 409 且其余合法项不落库（原子性）、目标目录不存在 404、空集合 400。验证：`python -m pytest tests/graybox/integration/test_locator_batch_move.py -v` 全通过。
- [x] 3.2 前端移动语义用例：在 `frontend/tests/element-locator/p0/` 覆盖 `moveLocatorItems` 的 method/URL/body 形状与目标为项目根（`parent_directory_id: null`）的透传。验证：`cd frontend && npx vitest run tests/element-locator/p0` 通过。
- [x] 3.3 回归门禁：`python -m pytest tests/graybox/unit -q` 全通过（重点 `test_api_path_callers.py` 对新路径 `/elements/batch-move/` 的解析与三面规模下限、`test_element_locator_views_split.py` 的路由与 300 行预算）。

## 4. 关单门禁

- [ ] 4.1 后端：`python manage.py check && ruff check apps/element_locator && ruff format --check apps/element_locator` 全通过（本变更无 Model 改动，无需 makemigrations）。
- [ ] 4.2 前端：`cd frontend && npm run build`（含 `vue-tsc --noEmit`）通过；按 `vue-frontend-check` 量规逐项自检布局裁剪、字号、硬编码色与接口契约。
- [x] 4.3 边界：`python tools/gen_arch_stats.py --check-boundaries` 通过（确认无新增跨 App import、写库仍只在 `element_locator/api*.py`）。
- [x] 4.4 文档同步：按项目文档约定在元素定位接口文档补记 `POST /api/elements/batch-move/`（请求体、成功信封与 400/404/409 语义）。验证：文档所列端点与方法同 `apps/element_locator/urls.py` 一致。
- [ ] 4.5 人工验收：逐条对照 `specs/element-locator-projects/spec.md` 的六条新增需求的关键场景走查（桌面拖动、触摸长按 1 秒、页面落点被拒、目录落自身被拒、拖回项目根、批量勾选移动、去重、重名被拒、批量勾选删除、删目录连带删页面且不浮回项目根）。

## 5. 批量删除与目录级联删除

- [x] 5.1 `apps/element_locator/api_directories.py` 的 `delete_directory` 改为**子树级联**：用一次 `LocatorDirectory.objects.filter(project_id=...).values_list("id", "parent_id")` 展开子树 id，先删子树内页面（元素随级联删除），再删子树目录，整体 `transaction.atomic()`；验证：5.5 的「删目录不留下浮到项目根的页面」用例通过。
- [x] 5.2 同文件新增 `batch_delete_items(*, items)`：校验集合非空与 `kind`、精确去重、按与 `batch_move_items` 相同的祖先口径剔除后代；整体 `transaction.atomic()`；先统计再删除，返回 `{"deleted", "pages", "elements"}`；并在 `api.py` 的 `__all__` 与 import 中登记。验证：`python -m pytest tests/graybox/integration/test_locator_batch_delete.py -q`（用例见 5.5）。
- [x] 5.3 `apps/element_locator/views_projects_drf.py` 新增 `batch_delete_items` 视图（`@api_view(["POST"])`，body `{items: [{kind, id}]}`），错误经既有 `_raise_or_conflict` 映射；`apps/element_locator/urls.py` 注册 `path("batch-delete/", batch_delete_items, name="el_batch_delete")`。验证：`python manage.py check` 0 issues。
- [x] 5.4 `tests/graybox/unit/test_element_locator_views_split.py` 的 `LEGACY_ROUTES` 增补 `("batch-delete/", "el_batch_delete", None)`。验证：`python -m pytest tests/graybox/unit/test_element_locator_views_split.py -q` 通过。
- [x] 5.5 新增 `tests/graybox/integration/test_locator_batch_delete.py`（`pytest.mark.django_db` + `pytest.mark.element_locator`）：删目录连带删除子树页面与元素、页面不浮回项目根；批量删除混合目录与页面返回 `{deleted, pages, elements}` 计数正确；目录与其后代同批时去重；节点不存在 404、空集合 400。验证：`python -m pytest tests/graybox/integration/test_locator_batch_delete.py -v` 全通过。
- [x] 5.6 前端 `api.ts` 新增 `deleteLocatorItems(body: { items: LocatorMoveItem[] })` → `POST /elements/batch-delete/`；`useLocatorTree.ts` 暴露 `deleteItems(items)`（成功提示 + 重载树）。验证：`cd frontend && npm run typecheck`（本变更文件零新增错误）与 5.8 用例通过。
- [x] 5.7 `components/LocatorTree.vue` 的批量选择工具栏新增「删除」按钮：二次确认文案含勾选数量与「目录将连同其下全部页面一并删除」；确认后提交整批删除，成功后清空勾选；失败提示原因且树保持原状。验证：`cd frontend && npm run build` 通过。
- [x] 5.8 `frontend/tests/element-locator/p0/api.spec.ts` 增补 `deleteLocatorItems` 的 method/URL/body 形状用例（并同步文件头的端点数量说明）。验证：`cd frontend && npx vitest run tests/element-locator/p0` 通过。
- [x] 5.9 文档同步：元素定位接口文档补记 `POST /api/elements/batch-delete/`（请求体 / 计数口径 / 400·404 语义），并把 `DELETE /api/elements/directories/{id}/` 的说明改为子树级联（含其下页面与元素）；PRD-04 的目录删除行为说明与已知问题第 5 条按新口径更新。验证：文档所列端点与方法同 `apps/element_locator/urls.py` 一致，且不再出现「页面浮回项目根」。
