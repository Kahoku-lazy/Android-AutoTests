## 1. 原型列表与详情读路径

- [x] 1.1 给 `frontend/src/modules/workflow/api.ts` 的 GET 原型列表/详情补上 `DjangoResponse<T>` 类型（列表 `T` 为数组，详情 `T` 为对象），验证：`npx vue-tsc --noEmit` 或 `npm run build` 对该文件无类型错误
- [x] 1.2 改 `usePrototypes.loadPrototypes`：成功条件改为 `data.status && Array.isArray(data.data)`，列表取 `data.data`；写路径 `addPrototype` 仍读平铺 `data.prototype`。验证：源码成功分支不再出现 `data.prototypes`；`npm run build` 通过
- [x] 1.3 改 `workflow/index.vue` 的 `bootWorkbench`：成功时从 `data.data` 取 `name`，不再判断 `data.prototype`。验证：源码无 `data.prototype` 读路径（创建接口除外）

## 2. 目录 / 文档读路径

- [x] 2.1 改 `libraryStore.refreshFromServer`：目录取 `dirRes.data.data.directories`（信封内层）；文档取 `Array.isArray(docRes.data.data) ? docRes.data.data : []`。验证：不再用 `dirRes.data.directories` / `docRes.data.documents`；空数组与缺字段不再被顶层 `|| []` 掩盖
- [x] 2.2 改 `fetchDocumentConfig`（及同文件其它 GET 文档处）：从 `res.data.data` 读 `config` / `title` / `updated_at`。验证：打开页面流不再读 `res.data.document`
- [x] 2.3 改 `exportDoc`：从 `res.data.data.envelope` 取导出体。验证：源码导出成功分支不读顶层 `res.data.envelope`

## 3. 契约测试与文档

- [x] 3.1 增加 graybox 测试：登录后 `GET /api/workflow/prototypes/` 的 JSON 为 `{status: true, data: <list>}`，且无顶层 `prototypes` 键。验证：`pytest tests/graybox/unit/test_workflow_prototype_envelope.py`（或选定路径）通过
- [x] 3.2 增加守护断言：`usePrototypes.ts` 列表成功分支包含 `data.data` 且不含 `data.prototypes`。验证：同一 pytest 文件或相邻 unit 测试通过
- [x] 3.3 在 `API-工作流.md` 总览注明：与 router 重叠的 GET 只达标准信封，legacy 列表行不可达。验证：该段与 `apps/workflow/urls.py` 的 `router.urls + legacy_patterns` 一致

## 4. 关单门禁

- [x] 4.1 前端构建：`npm run build` 通过
- [x] 4.2 后端：`python manage.py check` 与 `ruff check apps/workflow`（本变更若未改 Python 实现则可记「未改后端源码，check 仍绿」）
- [x] 4.3 浏览器：打开 `/workflow` 有原型时出卡片、无原型时空态；点进原型能看到目录树；打开一条页面流能水合画布。验证：不再出现「原型列表加载失败」（需登录态）
