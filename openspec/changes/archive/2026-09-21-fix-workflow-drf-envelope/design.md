## Context

见 proposal.md - Why。约束：`urlpatterns = router.urls + legacy_patterns` 使重叠路径永远先命中 DRF ViewSet；`EnvelopeJSONRenderer` 把 2xx 的 `Response(...)` 包成 `{status: true, data: <原 data>}`。前端 axios 的 `response.data` 即该信封。legacy 独有路径（如 `POST .../create/`、`POST .../import/`）仍是 Django `JsonResponse` 平铺，无 `data` 层。用例管理已按 `{status, data}` 消费；页面流列表仍读 `prototypes`。

实测 `data` 形状（ViewSet 原样 + 信封）：

```
GET /prototypes/              -> data = Prototype[]
GET /prototypes/{id}/         -> data = Prototype
GET /directories/?prototype_id= -> data = {directories, tree}
GET /documents/?prototype_id= -> data = Document[]   (ModelViewSet.list，不是 {documents: ...})
GET /documents/{doc_id}/      -> data = Document
GET /documents/{doc_id}/export/ -> data = {envelope}
POST .../create/              -> 平铺 {status, prototype|directory|document}  （本变更不改）
```

## Goals / Non-Goals

**Goals:**

- 前端读路径与上表 `data` 形状一一对齐，列表成功不再误报失败，目录/文档成功不再被 `|| []` 吃成空树
- `api.ts` 用 `DjangoResponse<T>` 标明各端点的 `T`，与 case-manager 同构
- 用测试锁住原型列表信封，防止再次把平铺字段当成功条件

**Non-Goals:**

- 不改 `EnvelopeJSONRenderer`、不改 ViewSet 返回形状去迁就旧前端
- 不清退仍可达的 `/create/` 等 legacy 写路径；不把写操作改到 `POST /prototypes/`（可后续独立变更）
- 不处理 `evaluator` 等同款 `router + legacy` 模块
- 不改 workflow `api.py` 写库与 ORM

## Decisions

**D1：只改前端读路径，后端信封保持现状。**

理由：赢家路径已经是 ARCH-09 的标准信封；再改 ViewSet 包一层 `{prototypes: ...}` 会变成 `{status, data: {prototypes}}`，与前端旧代码仍对不上，也会与 case-manager 分叉。备选「把 legacy 排到 router 前面」会让文档写的 DRF 路径全部失效，否决。

**D2：目录与文档按各自真实 `data` 读取，不发明统一 `{items: []}`。**

理由：DirectoryViewSet.list 显式返回 dict，DocumentViewSet.list 走默认数组。前端必须分形状处理，不能假设都有 `documents` 键。备选「改 DocumentViewSet.list 包一层 documents」会扩大后端 diff，本变更不做。

**D3：写路径继续走 `/create/` 平铺信封。**

理由：这些路径不与 router 重叠，创建原型今天仍可用；混改读写会把「列表失败」与「创建 405/信封」缠在一起。`addPrototype` 继续判断 `data.prototype`。

**D4：契约测试以后端响应形状 + 前端源码字段为双重断言。**

理由：仅测后端永远绿（后端本来就对）；仅靠手测会漏目录空树。最少：解析 `GET prototypes/` 的 envelope；扫描 `usePrototypes` 成功分支读取 `data.data`（或等价解构）而非 `data.prototypes`。

## 模块防火墙自检

- 跨 App import：本变更不新增任何后端 import
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 写库仍只经 `apps/workflow/api.py`：View 层不改写路径
- 前端仍只经 `workflow/api.ts` → `djangoClient`：不直连数据库
- 无新跨模块依赖

## Risks / Trade-offs

- [只改列表、漏改详情/目录] → 用户点进原型仍失败或空树；tasks 按 D2 形状表全覆盖读路径
- [把写路径也改成 `data.data` 而请求仍打 `/create/`] → 创建失败；写路径保持平铺字段
- [文档 list 被误当成 `{documents}`] → 空树；以 ViewSet 默认 list 数组为准，任务含对照测试或源码断言
- [API-工作流.md 仍写「两种信封都可达」] → 读者会再写错前端；实现时修正「重叠 GET 只达 router」一句，不扩写整份 API 手册

## Migration Plan

- 纯前端热更新即可；无数据迁移、无破坏性 URL 变更
- 回滚：还原 `usePrototypes` / `index.vue` / `libraryStore` / `api.ts` 即可恢复旧（错误）行为

## Open Questions

（无。读写分流与各端点 `data` 形状已由代码核实，不阻塞 tasks。）
