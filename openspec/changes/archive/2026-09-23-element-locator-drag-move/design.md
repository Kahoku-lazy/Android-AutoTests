## Context

- 现状（代码事实）：`frontend/src/modules/element-locator/components/LocatorTree.vue` 只有右键菜单（新建目录 / 新建页面 / 重命名 / 删除），**没有**拖动与勾选；`composables/useLocatorTree.ts` 负责目录与页面的 CRUD 并在每次写操作后 `loadTree()` 重载。
- 后端**已有**单件移动 `apps/element_locator/api_directories.py#move_item`（`kind=directory|page`，目标 `parent_directory_id`，`None` = 项目根）与 DRF 端点 `POST /api/elements/move/`；但 `frontend/src/modules/element-locator/api.ts` 没有对应封装，全仓无调用方。
- 目录树数据来自 `api_projects.get_project_tree`：目录取自 `LocatorDirectory`（`project`+`parent`），页面取自 `Page.directory_id`；`Page.parent/is_folder` 是旧文件夹树遗留字段，本变更不改其语义。
- 可复用范式：`frontend/src/modules/case-manager/components/ProjectTree.vue` 已在同一 `el-tree` 上实现 `draggable` + `allow-drop` + `node-drop` + 批量勾选（`selectMode`，目前仅用于批量删除）。
- 约束：前端组件单文件 ≤ 500 行（`frontend/AGENTS.md`），超限先拆样式层再拆逻辑层；写库必须收敛到 `apps/element_locator/api.py`；DRF 视图响应由 `EnvelopeJSONRenderer` 自动包成 `{status, data}`，手写 `JsonResponse` 才是 legacy 平铺。

## Goals / Non-Goals

**Goals:**

- 桌面指针可直接拖动节点，触摸端长按满 1 秒后拖动，落点限定为目录节点与项目根。
- 目录可嵌套目录，页面（文件）不可承载任何节点；目录不可落入自身或子孙。
- 批量勾选（目录与页面混合）后整批移动到指定目录，去重与原子性由后端保证。

**Non-Goals:**

- 不做同级排序（`sort_order` 重排）：落点只决定目标目录，MUST NOT 实现 before/after 插入排序。
- 不做跨项目移动（当前只有一个系统项目 `android`）。
- 不改 `el_` 表结构（无迁移）、不改元素工作台与检查器保存链路。
- 不引入第三方拖拽库（新增依赖需另立变更）。

## Decisions

### D1 桌面用 `el-tree` 原生拖动，触摸端单加长按 1 秒的指针拖拽

桌面指针沿用 `el-tree` 的 `draggable` + `allow-drop` + `@node-drop`（与案件管理 `ProjectTree.vue` 同口径，零新拖拽协议）。原生 HTML5 拖放**不会被触摸输入触发**，因此触摸端另实现一条路径：`touchstart` 记录节点并启动 1 秒计时，`touchmove` 超过阈值即取消计时（视为滚动），计时到点进入拖动态；拖动态中用 `document.elementFromPoint` 命中行并高亮目标，`touchend` 落点。

备选：（a）鼠标/触摸统一自研 pointer 拖拽——改动面大、要自己处理滚动与 ghost，风险高；（b）长按后弹「移动到…」选择器——不满足「拖动」的验收口径。

### D2 落点只接受 `inner` 到目录节点，以及独立的「项目根」行

`allow-drop` 仅在 `type === 'inner'` 且落点节点是目录时返回 true；页面节点与 before/after 一律拒绝并提示「只能放到目录或项目根」。项目根落点由树体顶部一行常驻的「项目根」条承担，绑定原生 `dragover`/`drop`（桌面）与命中测试（触摸），目标目录为 `null`。

备选：把 before/after 映射成「落到该节点的父目录」——落点与视觉位置不一致，容易误移，且会掩盖「不支持排序」的事实。

### D3 拖动即时移动，不弹二次确认

落点有效即调用移动并刷新树，成功/失败各一条提示；失败时树保持原状。理由是拖动本身已是显式意图，且误移后可用同一功能搬回。「移动到…」弹窗提供显式确认路径。

### D4 批量移动用一个原子端点，单件拖动即 1 项的批量

新增 `batch_move_items(items, parent_directory_id)`（api 层）与 `POST /api/elements/batch-move/`（DRF），整批包在 `transaction.atomic()` 内：任一项抛错则整批回滚，错误经既有 `_raise_or_conflict` 映射（`LookupError`→404、`ConflictError`→409、`ValueError`→400）。前端单件拖动与批量勾选走同一封装，减少一条路径。

备选：前端循环调既有 `POST /api/elements/move/`——多次往返、无法原子回滚，会出现半移动状态。

### D5 勾选去重放在后端

后端先取一次目录父子映射（`LocatorDirectory.objects.values_list('id','parent_id')`）与页面的目录归属，凡「祖先目录已在本批集合中」的后代（目录或页面）一律剔除后再落库，并把剔除数计入返回。这样前端只管提交原始勾选集合，HTTP 入口与将来其它调用方（AI 工具等）口径一致。

### D6 补齐 `move_item(kind=page)` 的同级重名校验

现状目录移动靠 `(project, parent, name)` 唯一约束兜底，而**页面移动完全不校验同级重名**（只 `page.directory = target`）。本变更要求「同级同名被拒」，故在 `move_item` 的 page 分支加一次 `Page.objects.filter(label=..., directory_id=target, is_folder=False).exclude(id=...).exists()` 预检。该函数当前无调用方，补齐不破坏既有行为；放在 `move_item` 而非只放批量入口，是为了让单件拖动与批量走同一口径。

### D7 目录选择器用模块内私有组件

新增 `components/MoveToDirectoryDialog.vue`：只渲染目录（含「项目根」选项）供选择目标目录。仓库内没有现成的「目录选择」共享件，且目前只有元素定位需要，故**不**提升到 `shared/`（避免无消费方的跨模块共享件）。

### D8 逻辑拆出组件，避免超 500 行

`LocatorTree.vue` 当前约 410 行，加入拖动、长按、勾选与弹窗接线后必然超限，故按 `frontend/AGENTS.md` 把编排逻辑拆到 `composables/useLocatorTreeMove.ts`（拖拽态、长按计时、命中测试、勾选集合、移动提交与错误处理），组件只保留渲染与事件绑定。批量删除复用同一份勾选状态，提交动作留在组件内（删除不需要拖拽态），因此该 composable 不因新增删除而改名。

### D9 目录级联删除在 api 层显式实现，不改外键

删除目录 MUST 连带删除其下页面与元素。现状 `Page.directory` 是 `SET_NULL`，删目录只会级联删子目录、页面浮回项目根。修法是在 `delete_directory` 内先按一次目录父子映射求出子树 id 集合，**先删**子树内页面（元素随 `Element.page` 的 CASCADE 一并删除），**再删**子树目录，整体包 `transaction.atomic()`。

备选：把 `Page.directory` 改成 `on_delete=CASCADE`。否决——需要迁移，且会让「删目录」在任何入口（含 admin、脚本）都变成删除页面，影响面超出本变更，也让媒体回收语义更隐蔽。

### D10 批量删除用新端点，不动既有 `files/batch-delete/`

新增 `POST /api/elements/batch-delete/`，入参 `{items: [{kind, id}]}`（与 `batch-move/` 同形，复用同一套祖先去重），返回 `{deleted, pages, elements}`——分别是删除的顶层节点数、实际删除的页面数、实际删除的元素数。既有 `POST /api/elements/files/batch-delete/`（只收 `kind=page`、返回 ORM 级联总数、当前零调用方）**保持原样**。

备选：改造既有端点的入参与返回。否决——那会改动已登记契约（接口文档与视图拆分门禁都在册），且其 `deleted` 口径本身就是被登记的问题，改它属于另一个变更。

### D11 删除不清理媒体文件

删除页面/目录时**不**触碰磁盘：元素定位媒体目录 `locator/pages/<page_id>/` 下的截图与缩略图沿用现状，孤儿副本由 `maintain_locator_media --prune` 回收。理由是删除链路保持纯数据库操作，避免与「快照媒体仍被引用」的判定耦合（该判定属于设备检查器）。

## 模块防火墙自检

- 跨 App import：本设计**不新增**任何跨 App import。后端改动全部落在 `apps/element_locator` 内（`api_directories.py` / `api.py` / `views_projects_drf.py` / `urls.py`），复用本模块 `api_projects` 的 `ConflictError` / `_resolve_target_directory` 口径。
- 写库收敛：新增写路径 `batch_move_items` / `batch_delete_items` 与改造后的 `delete_directory` 均位于 `apps/element_locator/api_directories.py`（api 层），View 只做分发与错误码映射到 HTTP；不出现 View 直写 ORM。
- 前端唯一 HTTP 出口：新增批量移动封装加入 `frontend/src/modules/element-locator/api.ts`（内部走 `shared/api-client`），不在组件里直调 axios/fetch。
- 无新增 WS / AI / 引擎依赖，不触碰 `engines/`；前端不直连数据库；仪表盘不做写操作。

## Risks / Trade-offs

- [触摸长按与列表滚动冲突] → `touchmove` 位移超过阈值立即取消 1 秒计时；进入拖动态后仅做命中高亮与落点，滚动被抑制。
- [桌面原生拖放与自研触摸路径互相触发] → 首次检测到触摸输入即关闭 `el-tree` 的 `draggable`，两条路径互斥。
- [批量移动半成功] → 后端 `transaction.atomic()` 保证全有或全无；前端任一失败即重载树，界面回到服务端真实状态。
- [移动后树的展开态丢失] → 移动完成后 `loadTree()` 重载，`default-expanded-keys` 回到顶层目录；影响仅限视觉，可接受。
- [重名判定口径不一致] → 目录沿用唯一约束 + 显式预检，页面按 `(directory_id, label)` 预检（根为 `directory_id IS NULL`）；两者都在 `move_item` 内，批量与单件共用。
- [旧文件夹树遗留页面的位置] → `get_project_tree` 把 `directory_id IS NULL` 的页面一律展示在项目根，本设计的落点与重名判定也以 `directory_id` 为准，与展示口径一致。
- [删除语义变更影响既有入口] → `delete_directory` 同时服务单条右键删除与批量删除，口径统一；前端确认文案、接口文档与 PRD-04 的目录删除口径三处同步，并用集成测试钉住「页面不浮回项目根」。
- [大批量子树删除的查询次数] → 子树 id 用**一次** `values_list('id','parent_id')` 在内存展开，页面删除走单条 `id__in` 批量语句，不逐节点递归查询。
