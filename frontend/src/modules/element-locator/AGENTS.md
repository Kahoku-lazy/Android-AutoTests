# element-locator 前端模块约束

> **AGENTS 层级**：一级约束 —— 根 `AGENTS.md` 优先于本文件；本文件优先于本模块下级目录。
> 通用前端规范见 `frontend/AGENTS.md`，这里只登记本模块的增量。

## 模块范围

1. 只服务「Android 定位库」单项目：项目 code 恒为 `android`，叶子类型恒为 `page`（枚举真相源在 `types.ts`）。
2. 三段式页面：`ProjectList.vue`（项目列表）→ `ProjectWorkspace.vue`（目录工作台）→ `LocatorFileView.vue`（文件详情）。目录与文件的增删改只在工作台，元素行的增删改只在详情页。
3. HTTP 只经本模块 `api.ts`（内部走 `shared/api-client`）；组件与 composable 不得直连 axios / fetch。

## 契约特例（登记）

1. **信封双轨**：`projects/`、`directories/`、`batch-move/`、`batch-delete/` 走 DRF `{status,data}`；`pages/`、`pages/{id}/items/`、`pages/{id}/elements/`、`items/{id}/`、`items/batch-delete/` 是 legacy 平铺响应。`api.ts` 用 `Envelope<T>` 与 `FlatResponse<T>` 两种返回类型区分，不得互相套用。
2. **wire DTO 真相源是 `types.ts`**：改接口先改 DTO 再改 `api.ts`；视图模型（如 `PageElementRow`）留在 composable，不要把呈现派生字段塞回 DTO。
3. **校验防线在后端**：`helpers/elementRowValidation.ts` 是后端 `apps/element_locator/element_fields.py` 的同口径副本，只做即时提示；口径变更必须双边同步。

## 交互约定

1. 目录树拖拽是双通道：桌面走 `el-tree` 原生 DnD（`allow-drop` 只允许落进目录），触摸走「长按 1s + `elementFromPoint` 命中测试」；两条通道都收敛到 `POST /elements/batch-move/`，判定只写在 `composables/useLocatorTreeMove.ts`。
2. 元素表格单元格默认纯文本，**双击**才进入编辑态；校验不通过就地提示并恢复原值。
3. 元素表恒定七列（缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点）；resource-id 与坐标只参与去重判定，不做列展示。

## 关单附加项

1. 门禁：`cd frontend && npm run build && npm run lint && npm run lint:styles && npx vitest run tests/element-locator/p0`。
2. 涉及写库 / 端点变化时，另跑后端门禁与 `python tools/gen_arch_stats.py --check-boundaries`。
3. 触摸拖拽类改动必须显式声明人工验收范围（真机触摸无法由单测覆盖）。
