## Why

元素定位项目工作台的目录树**没有任何搬运入口**：`frontend/src/modules/element-locator/components/LocatorTree.vue` 只有「新建目录 / 新建页面 / 重命名 / 删除」右键菜单，后端 `POST /api/elements/move/` 虽已实现却**全仓无前端调用方**（PRD-04 亦记录该端点无调用）。因此用户一旦把页面建错位置（例如本想放进「测试目录」却建在项目根），只能删除重建，已采集的元素资产随之丢失。

## What Changes

- 目录树支持**拖动移动**：桌面端按住节点即可拖动（复用案件管理 `ProjectTree.vue` 既有的 `el-tree` draggable 口径），触摸端**长按 1s** 进入拖动。
- **落点规则**：只有目录节点与「项目根」区域可作落点；目录可拖入目录（可互相嵌套），页面与目录都 MUST NOT 落入页面（文件不能包含文件）；目录 MUST NOT 拖入自身或其子孙。
- 拖到「项目根」区域即移回根（`directory_id = null`）。
- 新增**批量选择**模式：勾选多个目录/页面后，拖动其中任一已勾选节点、或点工具栏「移动到…」选择目标目录，**整批**移动；勾选目录时其被勾选的后代自动去重。
- 后端新增批量移动端点 `POST /api/elements/batch-move/`，**原子**：任一节点非法则整批不落库，错误码沿用既有单件移动口径（400/404/409）。
- 拖动落点后立即移动并刷新树，成功/失败均有提示；失败时树保持原状。
- 批量选择模式新增**删除**：勾选多个目录/页面后整批删除，**原子**（全有或全无）。
- **删除目录改为真级联**：删除目录时连同其下全部子目录、页面与页面元素一并删除，页面**不再浮回项目根**；右键单条删除与批量删除统一同一口径，前端「删除目录将同时删除其下全部内容」的确认文案由此变准（PRD-04 已登记该文案与行为不一致）。
- **不改**：元素工作台（页元素表）、目录/页面的新建·重命名入口、检查器快照保存链路、`el_` 表结构与迁移（**不**把 `Page.directory` 改成 CASCADE）。

## 关联文档

- PRD-04（元素定位）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-projects`：项目目录树新增「拖拽移动」「批量勾选移动」「批量移动接口契约」「批量勾选删除」「删除目录级联删除其下内容」与「批量删除接口契约」六项需求——触摸端长按 1s 进入拖动、目录可嵌套而文件不可嵌套、支持移回项目根、非法落点被拒、批量移动与批量删除原子且不产生重复落库、删目录连带删除其下页面与元素。

## Impact

- 后端：`apps/element_locator/api_directories.py`（新增 `batch_move_items` / `batch_delete_items`，`delete_directory` 改为子树级联）、`apps/element_locator/api.py`（re-export）、`apps/element_locator/views_projects_drf.py` 与 `urls.py`（新增 `POST batch-move/` 与 `POST batch-delete/`）
- 前端：`frontend/src/modules/element-locator/api.ts`（批量移动 / 批量删除封装）、`components/LocatorTree.vue`（拖动、长按、勾选、根落点、移动到弹窗、批量删除）、`composables/useLocatorTreeMove.ts`（拖动与勾选编排）、`components/MoveToDirectoryDialog.vue`、`ProjectWorkspace.vue`（接线与成功后重载树）
- 测试：后端新增 `tests/graybox/integration/test_locator_batch_move.py` 与 `test_locator_batch_delete.py`；前端在 `frontend/tests/element-locator/p0/` 增补 api 封装用例
- 文档：按项目文档约定补记新端点与目录级联删除口径
- **不动**：`el_` 表与迁移、`Page.directory` / `LocatorDirectory.parent` 的 `on_delete` 语义、检查器导入链路、元素表能力
