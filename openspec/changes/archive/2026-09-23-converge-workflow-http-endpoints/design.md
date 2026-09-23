## Context

动机见 `proposal.md - Why`。方案需要的当前事实（均为排查阶段实测）：

1. `apps/workflow/urls.py` 现在是 `literal_write_patterns + router.urls + legacy_patterns`：4 条字面量写路径在前（`fix-workflow-create-route-shadowing` 的产物），9 条 legacy 路径在后。实测 `resolve` 结果：只有那 4 条真的走 legacy 函数视图，其余 9 条全部被 router 的同名 / 同义路由覆盖，`apps/workflow/views.py` 里对应的 9 个函数是**死代码**。
2. 两套实现的返回形状不同：legacy 平铺 `{status, prototype|directory|document}`，router 标准信封 `{status, data}`。
3. `apps/workflow/views.py` 共 13 个视图函数、279 行；全仓除 `urls.py` 外无任何 import 或 `reverse()` 引用（已 grep `*.py` 全树）。
4. `WorkflowDocumentDetailSerializer.directory_id` 实测类型是 **`ReadOnlyField`**（DRF 未把 FK 的 attname 当可写字段），因此 `POST /api/workflow/documents/` 带 `directory_id` 建出的文档归属为 `null`（活平台实测），`perform_update` 里 `validated_data.get("directory_id")` 恒为 `None` —— 更新归属静默失效。
5. router 的文档更新实测与 legacy PUT 语义不一致，两个后果都在活平台复现：
   - `PUT` 不带 `config`（界面「重命名页面流」正是这个 payload）→ **400「该字段是必填项。」**，重命名失败
   - `PUT` 带 `config` 但不带 `description`（界面「保存」正是这个 payload）→ **描述被清空**（`'原描述'` → `''`），静默丢数据
   即 `perform_update` 用 `validated_data.get(..., 默认空值)` 直传 api，把"未提交"当成了"置空"。
6. router 的动态列表路由先于详情路由注册：实测 `documents/_import/` 命中动作；把动作的 `url_path` 改成 `import` 后 `documents/import/` 也会命中动作，且文档 id 形如 `WF-PF-…`，与字面量 `import` 不可能冲突。
7. 前端 `libraryStore` 有两处按 `res.data.document` 读 router 响应（`savePageFlowPayload`、`renameNode`），而 router 返回信封 —— 这两处一直恒为 `undefined`，静默走本地 `nowIso()` 兜底。
8. 前端唯一的创建/导入读取点是：`usePrototypes.addPrototype`（`data.prototype`）、`libraryStore.createFolder`（`res.data.directory`）、`createFlowDoc`（`res.data.document`）、`importDoc`（`res.data.document`）。
9. `WorkflowDirectoryTreeSerializer` 只被 `get_children` 自己递归使用，无任何外部引用；目录树实际由 `wf_api.get_directory_tree` 产出。

## Goals / Non-Goals

**Goals:**

- 页面流 HTTP 写接口只剩 router 一套实现、一种信封；`apps/workflow/views.py` 整体消失。
- 收敛不引入任何用户可见回归：新建页面流仍落到选中目录，导入/改名/删除行为不变。
- 顺手修掉排查中暴露的既有失效：文档归属丢失、文档重命名 400、保存时描述被清空、前端错读 `res.data.document`。
- 用契约用例把「旧地址必须 404」「新地址必须是标准信封」「提交字段合并语义必须成立」钉住。

**Non-Goals:**

- 不动 `apps/workflow/api.py` 的业务校验与写库语义（本次只改 HTTP 层与序列化器的可写性）。
- 不为旧地址保留任何转发别名或过渡期（用户决策 A：旧地址直接 404）。
- 不改 `WorkflowPrototypeViewSet` / 目录 ViewSet 的既有行为，不动 AI 侧同进程调用。
- 不重建 `frontend/dist`（gitignore 的构建产物），不清理本模块其它历史残留。
- 不改 `report_generator` 的平铺下载特例（另一个模块的独立特例）。

## Decisions

### D1：直接删 legacy，不做转发别名

用户已确认选 A。删掉 `views.py` 与全部 legacy 路由后，URL 表只剩 router，两套实现与两种信封的问题从根上消失；转发别名会把"两套地址"固化成长期维护面，与本变更目标相悖。

**备选（用户可见后果）**：旧地址保留为转发别名 —— 外部脚本 / 旧链接不断，但 URL 表仍有两套入口、要额外用例守护转发，重复没有真正去掉。

### D2：导入改用 router 动作路由承接既有路径

`WorkflowDocumentViewSet` 的导入动作声明 `url_path="import"`，使 `POST /api/workflow/documents/import/` 由动作接管。这样导入路径对前端与任何既有脚本都不变，只是实现换人；其余三条 `/create/` 无此待遇（改走集合路由），符合"创建就是集合 POST"的 REST 语义。

理由：一次性把 4 条路径全改会让「前端路径变更」与「实现收敛」两件事耦合；导入的动作名 `_import` 本就是 router 未暴露的实现细节（实际暴露在 `/documents/_import/`），给它一个正式 `url_path` 是补齐而非新增。

### D3：文档更新改为「按提交字段合并」，`directory_id` 同时改为可写

序列化器侧：照 `WorkflowDirectorySerializer.parent_id` 的既有做法，把 `directory_id` 显式声明为 `serializers.IntegerField(allow_null=True, required=False)`，让 `validated_data` 真的带上它；`config` 声明 `required=False`（本 ViewSet 的写入从不由 `serializer.save()` 落库，`required` 只会把"局部提交"拦成 400）。业务校验（标题非空、doc_type 合法性、目录是否存在、是否跨原型）继续留在 `api.py`。

`perform_update` 侧：不再用 `validated_data.get(字段, 空值)` 直传 api，而是以 `self.request.data` 的**键存在性**为准合并到既有文档上：

- `title` / `doc_type` / `config` / `description`：提交了就用提交值，没提交保持既有值
- `directory_id`：提交具体值 → 改归属；显式 `null` / `""` → 移到根（`clear_directory=True`）；没提交 → 不动

这套语义正是被删除的 legacy `document_detail` PUT 的行为。之所以不能用 `validated_data` 判断"没提交"：DRF 的 `validated_data` 里不含未提交字段，`get(..., 默认值)` 会把"没提交"读成"提交了空值"——实测已造成重命名 400 与描述被清空。

**备选（未采纳）**：把 `directory_id` 留在只读、由前端改用 `POST /documents/{id}/move/`。会让「保存画布」这类本地全量 PUT 无法携带归属，且 `POST /documents/` 创建时仍丢归属 —— 收敛即回归。

### D4：前端创建类读 `data.data`，并修两处错读

`api.ts` 的创建类改走集合路由后，`usePrototypes` / `libraryStore` 的四个读取点改读 `data.data`；`savePageFlowPayload` 与 `renameNode` 的两处 `res.data.document` 改为 `res.data.data`。界面与交互零改动，只改数据取值。

### D5：删掉只被自身递归引用的 `WorkflowDirectoryTreeSerializer`

本变更的目标是"去掉重复实现"，这个序列化器既无调用方、又与实际产出目录树的 `wf_api.get_directory_tree` 重复，一并删除。验证方式：全树 grep 除自身递归外零引用。

### D6：旧地址必须真的解析不到——给原型 / 目录的主键加数字约束

删掉 legacy 路由后实测发现：`prototypes/create/`、`directories/create/` 会被 router 的**详情路由**接走（`<pk>` 匹配任意非斜杠片段，`pk='create'`），POST 得到 405、GET 甚至因 `int('create')` 抛 `ValueError` 变成 500。也就是说"删掉 legacy"并不自动等于"旧地址消失"。

故给 `WorkflowPrototypeViewSet` 与 `WorkflowDirectoryViewSet` 加 `lookup_value_regex = r"\d+"`：主键只匹配数字，字面量段不再进入详情路由，旧地址真正变成 404，同时顺带消除"非数字主键 → 500"。

`WorkflowDocumentViewSet` 不需要改：它的 `doc_id` 是自然键（`WF-PF-…`），`documents/create/` 会走详情路由但 `get_document('create')` 查不到 → 404（DELETE / PUT / GET 同理），只有 POST 是 405。规格场景因此写成「404 或 405 这类 4xx、且不得由第二套实现应答」，而不是硬写 404。

### D7：规格与约束文件同步

`apps/AGENTS.md` §1.3 的「workflow legacy 平铺信封」特例条目删除（特例随实现消失）；`workflow-http-envelope` 规格用 delta 移除上一变更新增的「Legacy 平铺写端点必须可达」，并以两条新要求取代。

## 模块防火墙自检

- **跨 App import**：无新增；删除的 `views.py` 只 import 本 App 的 `api.py`。
- **写库路径**：无变化，所有写仍只经 `apps/workflow/api.py`；ViewSet 不直接 ORM 写（`perform_update` 后按 id 重新取实例）。
- **前端 → 后端**：路径与字段名收敛到一套，snake_case 与信封约定不变；不新增端点。
- **前端不直连数据库**：不涉及。
- **表前缀 / 迁移**：无模型改动、无迁移。

## Risks / Trade-offs

- [旧地址 404 破坏外部脚本 / 旧链接] → 全仓已扫描：除前端源码（`frontend/src`）与未入库的 `frontend/dist` 外无任何调用方；用户已确认接受。回滚为 `git revert`。
- [收敛暴露的 `directory_id` 丢失若不同时修，就是功能回归] → 本变更先修字段可写性再切前端，并加「创建归属生效 / 更新归属 / 显式 null 移到根 / 未传不动 / 跨原型 4xx」五条契约用例。
- [前端错读信封键会静默失败（不报错、只是值不对）] → 加源码扫描断言（创建类必须读 `data.data`、不读平铺键），并在活平台上跑真实浏览器验收。
- [调用面守护的规模下限按路径字面量计数] → 本次只改路径字符串、不改调用点数量；若计数漂移，按实测值显式重登记并在 tasks 里记录原因。
- [router 动作路由与文档详情路由的匹配次序] → 已实测：动态列表路由先于详情路由，`documents/import/` 命中动作；`doc_id` 前缀 `WF-` 与 `import` 无冲突。契约用例再钉一次。
- [合并语义改成"未提交即保持"后，前端若指望"不传就清空"会行为变化] → 前端清空只发生在显式传 `null`（目录归属）；`title` / `doc_type` 是必填语义，未提交即保持不会清空任何东西；契约用例逐条覆盖三种提交形态。
- [新增的合并逻辑读 `self.request.data` 而非 `validated_data`，可能绕过序列化器校验] → 序列化器仍执行 `is_valid()`（类型与 `allow_null` 校验），业务校验（标题非空、doc_type 合法、目录存在与同原型）全部在 `api.py` 内，且 api 是唯一写库入口；契约用例覆盖非法 doc_type 与跨原型目录。
- [删除 279 行代码可能带走未被发现的隐性行为] → 逐条对照：9 条被 router 覆盖的死路径无行为损失；4 条字面量写路径的语义逐项映射到 router（创建走集合、导入走动作），`documents_import` 的 `overwrite`、`envelope`、`prototype_id` 三种入参写法在动作里都有对应实现（已有代码，非本次新增）；legacy PUT 的字段合并语义由 D3 承接。

## Migration Plan

1. 后端：`serializers.py` 先放开 `directory_id`、把 `config` 改为非必填（此时旧前端仍走 legacy，不受影响）；`views_api.py` 把文档更新改为按提交字段合并、并给导入动作补 `url_path`。
2. 后端：`urls.py` 收敛为只有 router，删除 `views.py`；`apps/AGENTS.md` 同步删特例条目。
3. 前端：`api.ts` 与三个读取文件改走新路径 / 新信封。
4. 测试：新增收敛契约用例，重跑单元套件与调用面守护。
5. 验收：活平台黑盒探针（含旧地址 404）+ 真实浏览器走完全部写操作。
6. 回滚：`git revert`；无迁移、无数据改写，回滚后旧地址立即恢复。

## Open Questions

（无）
