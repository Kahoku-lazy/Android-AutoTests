# case-manager 前端代码检查 — 缺陷表

> **SPEC**：`dev_docs/03-设计与架构/SPEC-case-manager前端代码检查.md`  
> **检查日期**：2026-08-11  
> **修复日期**：2026-08-11（P0+P1 已落地，部分 🟡 仍 open）  
> **范围**：`frontend/src/modules/case-manager/` + `apps/case_manager/urls.py`

---

## 模块结论

| 模块 | 结论 | 摘要 |
|------|------|------|
| M1 types | 有条件通过 | multi/single 主体与 `schema_config.py` 对齐；行级 `auth.type:'none'` 偏宽；UI/Web/Storage 无契约 |
| M2 api | **不通过** | **编辑锁/可见性 URL 与后端 urls 不一致**；YAML 下载路径错误 |
| M3 composables | 有条件通过 | 无信封误读、无直连 client；脏路由守卫注册时机错误；WS 无条件覆盖；锁仅 unmount 释放 |
| M4 components | **不通过** | UI 详情 StepViewer prop 错；storage 误用 API 编辑器；列表选中态不同步；布局/字段缺口 |
| M5 根模块 | **不通过** | storage 路由错误；`index` 不读 `query.tab`；CaseEditor `status:false` 静默 |
| M6 全链路 | **阻塞** | 锁链路、storage CRUD、UI 详情步骤、WS 覆盖未保存 — 均阻塞验收 |

---

## 缺陷表

| # | 严重度 | 模块 | 文件 | 现象 | 根因 | 建议修复 | 状态 |
|---|--------|------|------|------|------|----------|------|
| 1 | 🔴 | M2 | `api/uiAutomation.ts` L42-62 vs `apps/case_manager/urls.py` L74-78 | 前端请求 `/api/cases/definitions/{id}/lock\|unlock\|case-lock\|case-unlock\|visibility`，后端注册为 `/api/cases/cases/{id}/...` | urls 路径写成 `cases/<id>/...`，与 docstring（`definitions/{id}/lock`）及前端不一致 | 后端改为 `definitions/<str:case_id>/lock` 等（与 views_lock docstring 一致），或两端统一到同一路径 | fixed |
| 2 | 🔴 | M5/M4 | `routes.ts` L50-60；`ApiCaseEditor` + `useApiConfigJson` | storage 新建/编辑指向 `ApiCaseEditor`，实际打 `/cases/api-testing/definitions` | 无独立 Storage 编辑器，路由复用错误 | 恢复/实现 Storage 编辑器与 `api/storage`；路由改回正确组件 | fixed |
| 3 | 🔴 | M4 | `components/ui/UiCaseList.vue` L53；`StepViewer.vue` L5-7 | UI 用例详情传 `:case-definition="c"`，StepViewer 只认 `steps` → 永远「暂无步骤」 | prop 名不匹配 | 改为 `:steps="c.steps_data \|\| []"`（对齐 WebCaseList） | fixed |
| 4 | 🔴 | M3/M4 | `useCaseEditingSocket.ts` L42-43；`ApiCaseEditor.vue` L41-48 | WS `case_updated` 无条件 `load()`，覆盖未保存编辑 | 回调无 dirty 判断 | 有未保存改动时确认/忽略，或暂停自动刷新 | fixed |
| 5 | 🔴 | M4 | `CaseList.vue` 行选/卡片选中 | 列表点选用例只本地 `loadCaseDetail`，不同步父级 `activeCaseId` | 缺 emit select | emit 选中事件，`index.vue` 更新 `activeCaseId`（及目录） | fixed |
| 6 | 🟠 | M3/M5 | `useDirtyGuard.ts` L17-26；`CaseEditor.vue` L92 | `onBeforeRouteLeave` 在 `onMounted→setup()` 内注册，违反 Vue Router「须在 setup 同步调用」 | 守卫注册时机错误 | 在 composable 顶层直接注册 leave 守卫；`setup` 只管 beforeunload | fixed |
| 7 | 🟠 | M2/M4 | `UiCaseList.vue` L34 | YAML 下载打开 `/api/cases/export/yaml/{filename}`，后端下载是 `/api/cases/exports/{filename}` | 路径拼错 | 改为 `/api/cases/exports/${latest.filename}`，或封装 `downloadExport` | fixed |
| 8 | 🟠 | M4 | `WebCaseEditor.vue` L95-129 | 加载失败仅 `console.error`；`status:false` 无提示 → 空白表单 | 缺错误分支 | ElMessage / ErrorState；status false 明确提示 | fixed |
| 9 | 🟠 | M4 | `WebCaseEditor.vue` L98-112 vs 保存逻辑 | 初次加载未写入 `updated_at`，乐观锁 409 形同虚设 | 漏字段 | load 时写入 `updated_at`；保存带 `_client_updated_at` | fixed |
| 10 | 🟠 | M4 | `WebCaseEditor.vue` L113-116 | 未处理 `d.locked` 创建者持久锁，可能仍可编辑 | 锁分支不完整 | 对齐 `useEditLock` 的 locked 分支 | fixed |
| 11 | 🟠 | M5 | `CaseEditor.vue` L98-116 | `getDefinition` 返回 `status:false` 时无提示，仍落 initialForm | 只处理 status true | else 分支 ElMessage + 可返回列表 | fixed |
| 12 | 🟠 | M4 | `CaseList.vue` L55-63, L73-75 | `getDef` 失败或 status false 时保留上一条 `selectedCase`，与树 ID 错位 | 失败未清空/提示 | 失败清空或 ErrorState，并提示 | fixed |
| 13 | 🟠 | M4 | `CaseList.vue` L132 `goToAll` | 「全部用例」只 `refresh-tree`，不清详情、不 `clear-case` | 漏 emit | 调 `clearDetail()` 或同时 emit clear-case | fixed |
| 14 | 🟠 | M4 | `CaseCard.vue` L21-31 | single 格式 API（`meta/cases`）步骤数恒为 0 | 只认 `config_json.steps` | `cases?.length` 优先或并列展示「N 条用例」 | fixed |
| 15 | 🟠 | M4 | `ApiCaseEditor.vue` L115-136 | 保存无 409 冲突引导（UI/Web 编辑器有） | catch 只 toast | 对齐 CaseEditor 409 弹窗/刷新 | fixed |
| 16 | 🟠 | M4 | `ApiCaseEditor.vue` L75-86 | single 校验缺 `request.path`（后端 `minLength:1`） | 校验弱于 Schema | 保存前校验 path 非空 | fixed |
| 17 | 🟠 | M5 | `index.vue`；`ApiCaseEditor` L123-126 | 保存后 `query: { tab: 'api' }`，工作台不读 query.tab | 深链无效 | index 读 `route.query.tab` 设 activeTab | fixed |
| 18 | 🟠 | M3 | `useEditLock.ts` + 各编辑器 | 编辑锁主要在 `onUnmounted` 释放；关标签/刷新可能泄漏至超时 | 无 beforeunload 释放 | beforeunload/pagehide 尝试 release（或缩短服务端超时+心跳） | fixed |
| 19 | 🟠 | M3 | `useStepRunner.ts` | 批量跑步骤不校验 `debugDevice`，单步有校验 | 分支不一致 | `runStepsRange` 入口同样校验 | fixed |
| 20 | 🟠 | M4 | `StorageCaseList.vue` L10-18 | 列表缺 steps/expected_result 等业务字段；无自定义 detail | 列定义过简 | 补列与 detail slot（在有正确编辑器后） | fixed |
| 21 | 🟠 | M4 | `CaseList` 自定义 `#cell-*` | 自定义单元格绕过纯文本 tooltip，长 ID/URL/标题截断反馈弱 | slot 内容无 title/ellipsis | 关键列加 `:title` 或 el-tooltip | fixed |
| 22 | 🟡 | M1 | `types/api-config.ts` `AuthConfig` / `CaseInput.auth` | TS 允许 `type:'none'`；后端行级 auth 仅 bearer/basic/api_key 或 null | 类型宽于 Schema | 行级 auth 用不含 none 的类型或 `null` | fixed |
| 23 | 🟡 | M1 | `types/` 目录 | UI/Web/Storage 无 types，易漂移 | 覆盖不全 | 记债；改模型时再补 | open |
| 24 | 🟡 | M2 | `api.ts` L9-11 | `fetchStepTypes` 仍直接 import client，未下沉 `api/` | facade 不纯 | 迁入 `api/*.ts` 再导出 | open |
| 25 | 🟡 | M2 | `api.ts` re-export | 未导出 `connectDebugDevice`/`disconnectDebugDevice`/`downloadExport` | facade 不全 | 补导出或保持「只从子模块引」并文档化 | open |
| 26 | 🟡 | M3 | `useTreeDragDrop.ts` | `longPressTimer` 无 onUnmounted 清理 | 泄漏风险 | unmount clearTimeout | fixed |
| 27 | 🟡 | M3 | `useBatchSelect.ts` | 部分 checkedId 找不到 node 时静默少移；失败仍清空勾选 | UX | 提示「部分无效」；失败保留选择 | open |
| 28 | 🟡 | M3 | `useCaseManager.ts` | 混杂常量/工具，非典型 composable | 归类 | 可迁 `constants`/`utils`（非必须） | open |
| 29 | 🟡 | M4 | `ApiCaseEditor` single UI | 只读展示仍有保存/删除按钮，易误操作 | 按钮未按 format 禁用 | single 隐藏写操作或明确禁用 | open |
| 30 | 🟡 | M4 | `CaseCard.vue` toggleLock | catch 空，失败无提示 | 静默 | ElMessage.error | fixed |
| 31 | 🟡 | M5 | `step-utils.ts` 别名 | 旧 type 别名只修 icon，`stepSummary` switch 仍退化为原始 type | 摘要不全 | summary 也走 alias | fixed |

---

## M1 对齐摘要（types ↔ schema）

| 项 | 结果 |
|----|------|
| multi 顶层 required | ✅ 一致 |
| multi step required `url/method/assert` | ✅ 类型有；校验在 ApiCaseEditor（缺 method 显式校验可接受，有默认 GET） |
| extract name/path | ✅ Schema + 前端 validateBeforeSave |
| single meta/request/cases | ✅ 结构一致 |
| `isSingleFormat` | ✅ 与后端同为 `meta` + `cases` |
| 默认工厂 | ✅ 与 `get_default_*` 同形（空 steps/cases 仅作草稿，保存靠业务校验） |
| Auth 行级 | 🟡 见 #22 |

---

## M2 路径对齐摘要

| 前端 | 后端 urls | 结果 |
|------|-----------|------|
| `/cases/directories*` | `directories*` | ✅ |
| `/cases/definitions*` | `definitions*` | ✅ |
| `/cases/api-testing|storage|web/definitions*` | 对应 path | ✅ |
| `/cases/definitions/{id}/lock` 等 | `cases/{id}/lock` 等 | 🔴 #1 |
| `/cases/step-types`、`export/yaml`、`exports` | 有 | ✅（下载 URL 见 #7） |
| devices / elements / runner | 跨模块 | ✅ 集中在 uiAutomation helpers |

---

## M6 已知风险复验

| 风险（笔记/SPEC） | 复验结果 |
|-------------------|----------|
| 编辑页把信封当 definition | CaseEditor/Web/useApiConfigJson 均用 `data.definition` → **已缓解**（CaseEditor status false 仍静默 #11） |
| WS 覆盖未保存 | **仍在** #4 |
| 返回列表不清 activeCaseId | clearDetail 会 clear-case；**goToAll 仍不清** #13；列表点选不同步 #5 |
| 前端校验弱于 Schema | multi 已加强；**single 缺 path** #16；composable.save 本身无校验（靠编辑器） |
| 表格 overflow tooltip | AppTable 默认 true；**自定义 cell 仍弱** #21 |
| Web 缺 409 | Web 有 409 处理；**缺 load updated_at** #9；**Api 缺 409** #15 |
| storage → ApiCaseEditor | **仍在** #2 |

---

## 建议修复优先级

1. **P0（阻断）**：#1 锁 URL、#2 storage 路由、#3 UI StepViewer prop、#4 WS 覆盖  
2. **P1**：#5/#13 选择态同步、#6 路由脏守卫、#7 YAML 下载、#8–12 加载/乐观锁错误处理  
3. **P2**：#14–21 体验与校验补齐  
4. **P3**：#22–31 类型收紧与气味

---

## 检查执行勾选

```
[x] M1 types
[x] M2 api + api.ts
[x] M3 composables
[x] M4 components
[x] M5 routes / index / CaseEditor / step-utils
[x] M6 代码级全链路与已知风险复验（未跑完整手工 E2E）
[x] 缺陷表定稿
```
