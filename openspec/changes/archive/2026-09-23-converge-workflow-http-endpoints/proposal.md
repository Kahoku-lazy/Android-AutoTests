## Why

页面流后端目前有**两套**同义实现：`apps/workflow/views.py` 的 13 条 legacy 平铺视图与 `apps/workflow/views_api.py` 的三个 ViewSet。只有 `*-/create/`、`documents/import/` 四条字面量路径真的走 legacy（其余 9 条早已被 router 覆盖），但为维持这套并存，URL 表要手工排序、返回体有两种形状（平铺 `{status, prototype}` 与标准信封 `{status, data}`）、前端要按调用分别读不同字段，而且刚刚就因此出过一次 405 抢占事故（已由 `fix-workflow-create-route-shadowing` 修复）。

重复实现没有任何一方是"另一方的兼容层"——它们是两份并行代码，改一处必须记得改另一处。本次按用户决策「彻底收敛成一套」把它们合成一套。

排查中另发现三处收敛必须一并处理的缺陷（否则收敛即回归，或把已有坏行为固化下来）：

1. `WorkflowDocumentDetailSerializer.directory_id` 实际是**只读**字段（DRF 把 FK 的 attname 当只读），因此 router 路径创建/更新文档时 `directory_id` 被静默丢弃——实测 `POST /api/workflow/documents/` 带 `directory_id` 建出的文档归属为 `null`。收敛后前端「新建页面流」会落不到选中目录，必须先修。
2. router 的文档更新按「未提交即置空 / 必填即拒绝」处理，与 legacy PUT 的合并语义不同，实测两个后果：**只提交标题（界面「重命名页面流」正是这样）返回 400「该字段是必填项。」**，重命名失败；**带画布内容提交但未带描述时，描述被清空**（`'原描述'` → `''`，静默丢数据）。收敛删除 legacy 后，这套语义就是唯一实现，必须补齐。
3. 前端 `libraryStore` 两处按 `res.data.document` 读取 router 响应（保存、改名），而 router 返回的是信封 `{status, data}`——`res.data.document` 恒为 undefined，一直静默走本地兜底时间戳。

## What Changes

- **BREAKING**（仅平台内调用面）：删除 4 条 legacy 写地址 `POST /api/workflow/prototypes/create/`、`/directories/create/`、`/documents/create/`、`/documents/import/` 中的 `/create/` 三条，改由集合路由 `POST /api/workflow/{prototypes|directories|documents}/` 承担；导入改由 router 动作路由 `POST /api/workflow/documents/import/` 承担（路径不变，实现换人）。三条 `/create/` 地址将返回 404。
- 后端删除 `apps/workflow/views.py` 全部 13 个 legacy 函数视图，`urls.py` 收敛为「只有 router」；`apps/AGENTS.md` §1.3 的「workflow legacy 平铺信封」特例条目随之删除。
- 修复文档写入字段语义：`WorkflowDocumentDetailSerializer.directory_id` 改为可写；文档更新改为**按提交字段合并**——只改提交了的字段，未提交的 `title` / `doc_type` / `config` / `description` 保持原值，`directory_id` 传值即改归属、显式 `null` 表示移到根、未传则不动（即 legacy PUT 的既有语义，收敛后不能丢）。
- 前端调用面统一：创建类改走集合路由，全部读标准信封 `{status, data}`；修掉两处 `res.data.document` 的错误读法。
- 附带清理：删除无任何引用、只被自己递归使用的 `WorkflowDirectoryTreeSerializer`。
- **非目标**：不改 `apps/workflow/api.py` 的任何校验与写库语义；不改响应字段名；不动 AI 侧同进程调用（`wf_api`）；不重建前端产物（`frontend/dist` 为 gitignore 的构建产物）；不改 `report_generator` 的平铺下载特例。

## 关联文档

- PRD-09（工作流工作台；需求总纲登记为「无子 PRD」，接口口径 `API-工作流.md`）
- 前置变更：`fix-workflow-create-route-shadowing`（本变更删除其新增的「legacy 写端点必须可达」要求）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workflow-http-envelope`: 移除「Legacy 平铺写端点必须可达」要求；新增「页面流写操作只有一套路由且返回标准信封」与「文档目录归属在创建/更新时可写可清空」两条要求

## Impact

- 后端：删 `apps/workflow/views.py`；改 `apps/workflow/urls.py`（只剩 router）、`apps/workflow/views_api.py`（导入动作 `url_path`、文档创建/更新归属语义、`destroy` 保持信封）、`apps/workflow/serializers.py`（`directory_id` 可写、删死序列化器）
- 前端：`frontend/src/modules/workflow/api.ts`（4 个函数路径/方法）、`composables/usePrototypes.ts`、`stores/libraryStore.ts`（5 处信封读法）
- 测试：新增收敛契约用例（旧地址 404 / 新地址信封 / 归属字段生效 / 前端源码不残留旧字面量）；既有 `test_workflow_prototype_envelope.py`、`test_workflow_directory_update.py`、`test_api_path_callers.py` 必须继续通过；`test_api_path_callers.py` 的调用面规模下限需按实际重登记
- 数据：无模型变更、无迁移、不改写存量数据
- 其它：`apps/AGENTS.md` §1.3 删除 workflow 特例；`frontend/dist`（未入库）需在部署时重建
