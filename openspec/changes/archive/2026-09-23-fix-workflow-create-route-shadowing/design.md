## Context

动机见 `proposal.md - Why`。方案需要的当前事实（均为排查阶段实测）：

1. `apps/workflow/urls.py` 的真相源是单行 `urlpatterns = router.urls + legacy_patterns`，router 注册了 `prototypes` / `directories` / `documents` 三个 ViewSet。
2. DRF `DefaultRouter` 的详情路由是 `^prototypes/(?P<pk>[^/.]+)/$` —— `<pk>` 匹配任意非斜杠片段，因此 `prototypes/create/` 会以 `pk='create'` 命中详情路由；`documents` 的 `lookup_value_regex = r"[-\w]+"` 同理吃掉 `create` / `import`。
3. 详情路由的动作白名单只有 `get / put / patch / delete`，POST 不在其中 → DRF 返回 405「方法 "POST" 不被允许。」，前端把该 message 直接弹出。
4. 实测 `django.urls.resolve` 结果：`/api/workflow/prototypes/create/` → `WorkflowPrototypeViewSet`（`pk='create'`）、`/directories/create/` → `WorkflowDirectoryViewSet`、`/documents/create/`、`/documents/import/` → `WorkflowDocumentViewSet`（`doc_id='create'` / `'import'`）。
5. 13 条 legacy 路径里只有 4 条「字面量写路径」是**功能上必需但被抢占**的；其余 9 条（集合列表、`<int:id>` 详情、`move`、`export`）已被 router 同名/同义路由覆盖。
6. 扫描前端 34 个调用点，命中错误视图的有 7 处：4 条字面量 create/import，加上 3 处 POST 打详情路由（原型改名、目录改名、目录删除，写在模板字面量里，路径含 `${id}`）。
7. `shared/renderers.py` 的 `EnvelopeJSONRenderer` 只包装 2xx，且 204 无响应体时渲染器不参与 —— 前端因此读不到 `status`，会把成功的删除判成失败（`WorkflowDocumentViewSet.destroy` 已因同样理由被覆写为返回 `Response({})`）。

## Goals / Non-Goals

**Goals:**

- 页面流整族写操作（新建原型 / 新建目录 / 新建页面流文档 / 导入 / 目录改名 / 目录删除 / 原型改名）恢复可用。
- 不改变任何对外可见的路径、字段名与信封形态：读路径继续走 router 标准信封，legacy 平铺信封特例保持原样。
- 用一条守护用例把「方法 ∉ 命中视图白名单」这类抢占回归钉死在默认单元套件里，而不是依赖人眼。

**Non-Goals:**

- 不合并 legacy 与 router 两套实现（重复实现是既有债务，本次只恢复可达性；收敛另立变更）。
- 不删除当前已被 router 覆盖的 9 条 legacy 路由定义与对应视图函数（删代码会让本变更的 diff 无法逐行追溯到「修 405」这一需求）。
- 不改前端界面、组件、画布逻辑；不动已正常的列表 / 详情 / 保存 / 移动 / 删除原型。
- 不改动 `apps/workflow/api.py` 的任何写库语义。

## Decisions

### D1：把 4 条字面量写路径**显式前置**到 router 之前，而不是整体反转顺序

`urlpatterns = literal_write_patterns + router.urls + legacy_patterns`，其中 `literal_write_patterns` 只含 `prototypes/create/`、`directories/create/`、`documents/create/`、`documents/import/`。

**备选一（未采纳）：整体反转成 `legacy_patterns + router.urls`。** 会被现有守护与契约否掉：`GET /api/workflow/prototypes/` 必须继续命中 ViewSet 的标准信封（`tests/graybox/unit/test_workflow_prototype_envelope.py` 明确断言顶层无 `prototypes` 键）；且 legacy 的 `directories/<int:dir_id>/` 只接受 POST，前置后会打断 `PATCH` 目录改名（`test_workflow_directory_update.py` 的 4 条用例全部依赖 router 详情路由）。

**备选二（未采纳）：前端改走 router 集合 / 详情路由，删掉 legacy 写端点。** 需要把创建类响应从平铺改成读 `data`，牵动 `usePrototypes.ts` 与 `libraryStore.ts` 三处读法，而且 legacy 平铺信封是本仓明文认可的特例（`apps/AGENTS.md` §1.3），改造成信封式被禁止。改动面比本方案大，与用户选定的「最小改动」不符。

### D2：目录删除必须返回信封非空体

`WorkflowDirectoryViewSet` 覆写 `destroy`，删除成功后返回 `Response({})`，与 `WorkflowDocumentViewSet.destroy`（已有注释说明「避免默认 204 空体让前端判失败」）保持一致。这样前端 `deleteNode` 的目录分支继续用 `res.data?.status` 判成功，无需放宽判定逻辑。

**备选（未采纳）**：前端目录删除分支改成「2xx 即成功」。会把「服务端返回 `status:false` 但状态码 2xx」这类失败也吞掉，与文档分支的显式判定不一致。

### D3：目录改名 / 删除 / 原型改名改走标准方法，而不是新增 legacy 端点

`frontend/src/modules/workflow/api.ts` 三处改为 `PATCH` / `DELETE` / `PATCH`。router 侧实现已存在且已被单测覆盖（`perform_update` 的单写路径 + 零落库失败语义），改前端调用方法比新增/搬移后端路由更小、更符合 REST 约定。

**备选（未采纳）**：把 legacy `directories/<int:dir_id>/` 前置以保住 POST 调用形态。会同时打断 router 详情路由的 PATCH/DELETE 契约（4 条既有用例 + 上条 D2 的理由）。

### D4：守护用例挂在既有调用面扫描器上，记录方法而不新写扫描器

`tests/graybox/unit/test_api_path_callers.py` 已按「调用形态」跨行扫描三个面并已处理模板字面量（`${...}` → `1` 占位）与规模下限。扩展 `Caller` 记录 HTTP 方法（正则加一个捕获组），新增断言：解析命中的视图若带 router 动作白名单（`match.func.actions`），则方法必须在该白名单内；函数视图跳过。

**备选（未采纳）**：新写一个只扫 workflow 模块的守护。会因为「只覆盖出事的模块」而漏掉同类问题，且重复实现既有扫描器（含规模下限、例外清单等机制）。

### D5：方法断言只对带白名单的视图生效

函数视图的允许方法在运行期才确定（各 legacy 视图手写 `if request.method != "POST"`），静态不可判定；`APIView` 的 `http_method_names` 与 `allowed_methods` 也不是路由条目属性。因此断言范围限定为 router 生成的视图，避免给出「看起来全覆盖、实则误判」的假守护。这条边界写进 delta spec 的场景里。

## 模块防火墙自检

- **跨 App import**：无新增。只改 `apps/workflow` 内部（`urls.py` 顺序、`views_api.py` 的 destroy 覆写）与前端同一模块内调用。
- **写库路径**：无新增写库。所有写操作仍经 `apps/workflow/api.py`（`create_prototype` / `create_directory` / `upsert_document` / `update_directory` / `delete_directory` / `update_prototype`），View / ViewSet 只做分发。
- **前端 → 后端**：路径与字段名不变，只改 3 处 HTTP 方法与读信封的位置；不新增端点、不改 snake_case 约定。
- **前端不直连数据库**：不涉及。
- **表前缀 / 响应信封**：无模型改动、无迁移；legacy 平铺信封与 router 标准信封各自保持现状。

## Risks / Trade-offs

- [前置 4 条字面量路径后，若将来有人把 `create` 当成主键值使用会撞车] → 该资源主键为自增整型，`create` / `import` 不可能是合法主键；`prototypes/create/` 与 router 详情路由的冲突是本次显式修掉的对象。
- [方法断言可能对既有调用面报出其它模块的新违规，扩大改动面] → 排查阶段已用同一规则扫描 frontend/src 全部 34 个调用点，命中错误视图的 7 处**全部**在 workflow 模块内，其它模块零命中；断言只对带白名单的 router 视图生效，不会把函数视图误判。
- [目录删除由 204 改为带体 200，可能影响非前端消费方] → 全仓 `DELETE /api/workflow/directories/` 的调用方只有前端 `libraryStore.deleteNode`；`tests/` 内无用例依赖 204。
- [PATCH 目录改名时若前端漏传 `parent_id` 会把目录移到根] → router 侧语义已固化并被 4 条既有用例覆盖（缺省 `parent_id` 不动父级、显式 `null` 移到根），前端只传 `{name}` 正好落在「不动父级」分支；本变更不新增该风险，但要在验收里跑既有用例确认。
- [两套实现继续并存，未来仍可能出现新的抢占] → 本变更新增的方法白名单断言会在任何「前端方法打错路由」时立即失败；实现合并作为独立技术债另立变更处理。

## Migration Plan

1. 后端：`apps/workflow/urls.py` 拆出 `literal_write_patterns` 并前置；`WorkflowDirectoryViewSet.destroy` 覆写返回 `Response({})`。
2. 前端：`api.ts` 三处调用方法改为 PATCH / DELETE / PATCH。
3. 测试：扩展 `test_api_path_callers.py` 记录方法 + 新增断言；跑 `tests/graybox/unit` 全量确认既有 workflow 契约用例不回归。
4. 验证：`python manage.py check`、`ruff check`、`pytest tests/graybox/unit -q`；手工/端到端验收页面流 7 个写操作。
5. 回滚：纯路由顺序 + HTTP 方法 + 视图返回体改动，无数据库迁移、无数据改写，`git revert` 即回滚。
