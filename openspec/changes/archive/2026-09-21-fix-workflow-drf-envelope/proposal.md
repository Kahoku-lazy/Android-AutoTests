## Why

页面流原型列表页在 HTTP 成功时仍显示「原型列表加载失败」。根因不是接口宕掉，而是 `apps/workflow/urls.py` 把 DRF `router.urls` 放在 legacy 之前：`GET /api/workflow/prototypes/` 实际命中 ViewSet + `EnvelopeJSONRenderer`，返回 `{status, data}`；前端 `usePrototypes` 仍按 legacy 平铺读 `data.prototypes`，成功体被当成失败。同一错位会立刻阻断进入原型、拉目录/文档、打开画布。

## What Changes

- 前端页面流模块按**实际命中的 router 路径**解析标准信封 `{status, data}`（与用例管理 `useProjects` 同构），不再把 `prototypes` / `prototype` / `directories` / `documents` / `document` / `envelope` 当作顶层字段。
- 对齐 `workflow/api.ts` 的 TypeScript 信封类型，避免运行时把 `undefined` 判成加载失败或静默空列表。
- 补契约测试：断言 `GET /api/workflow/prototypes/` 的成功体是 `{status: true, data: array}`，且前端消费路径读取 `data` 而非 `prototypes`。
- 不在本变更内清退全部 `/create/` 等仍可达的 legacy 写路径；那些路径仍走 `JsonResponse` 平铺信封，读写分流在 design 中写明。

## 关联文档

PRD-09（工作流工作台）；ARCH-09 双口径信封（router `{status, data}` / legacy 平铺）为既有约束，本变更让前端与 router 赢家对齐，不改写后端信封渲染器。

## Capabilities

### New Capabilities

- `workflow-http-envelope`: 页面流工作台对 router 命中的 CRUD 读路径必须按标准信封取 `data`；成功且 `data` 形状正确时不得展示「加载失败」。

### Modified Capabilities

（无。`api-path-convention` 只管尾斜杠；本变更不改路径写法。）

## Impact

- 前端：`frontend/src/modules/workflow/composables/usePrototypes.ts`、`index.vue`、`stores/libraryStore.ts`、`api.ts`
- 后端：行为不变（ViewSet + EnvelopeJSONRenderer 已是 GET 列表/详情的真实实现）；不改 `api.py` 写库路径
- 测试：`tests/graybox` 或前端契约测，覆盖原型列表信封与消费字段
- 文档：实现阶段按门禁同步 `API-工作流.md` 中「双路径并存、legacy 无尾斜杠」的过期表述（若与代码不符）
