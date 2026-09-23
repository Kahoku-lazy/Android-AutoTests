## Why

页面流工作台的「新建原型」提交后弹出「方法 "POST" 不被允许」（HTTP 405），原型建不出来。

根因是路由抢占：`apps/workflow/urls.py` 把 DRF router 排在 legacy 平铺路径之前，router 的详情路由 `prototypes/<pk>/`（`<pk>` 为任意非斜杠片段）把字面量 `create` 当成主键吃掉，于是 legacy 的 create 视图永远不可达，而详情路由只接受查询/整体更新/局部更新/删除，POST 一律 405。

同一抢占还连带打断：新建目录、新建页面流文档、导入文档，以及前端用 POST 打详情路由的目录改名与目录删除。排查实测（`django.urls.resolve`）确认 7 个前端写调用点命中错误视图，其中 4 个已确认返回 405；正常的是原型列表/详情、删除原型、文档保存、节点移动。

## What Changes

- 后端 `apps/workflow/urls.py`：把 4 条「字面量写路径」（`prototypes/create/`、`directories/create/`、`documents/create/`、`documents/import/`）显式前置到 router 之前，恢复 legacy 平铺写端点可达；其余顺序不变，读路径仍走 router 标准信封。
- 后端 `WorkflowDirectoryViewSet`：删除目录改为返回信封非空体（`{status: true, data: {}}`），与文档删除的既有处理一致——默认 204 空体会让前端把成功判成失败。
- 前端调用面改走标准方法：目录改名 `PATCH`、目录删除 `DELETE`、原型改名 `PATCH`（不再用 POST 打详情路由）。
- 新增守护用例：把「调用面 (方法, 路径)」纳入既有 `api-path-convention` 守护——路径解析若命中 router 视图，该方法必须在该路由的动作白名单内，从根上堵住同类抢占回归。
- **非目标**：不合并 legacy 与 router 两套实现（重复实现保留，本次只恢复可达性）；不改任何响应字段名与前端界面；不动已正常的列表/详情/保存/移动/删除原型；不清理已失效的重复 legacy 路径定义（另立变更处理）。

## 关联文档

- PRD-09（工作流工作台；需求总纲登记为「无子 PRD」，接口口径 `API-工作流.md`）
- 既有规格 `workflow-http-envelope`（router 读路径信封）、`api-path-convention`（路径书写与解析守护）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workflow-http-envelope`: 新增写路径要求——legacy 平铺写端点必须可达（不得被详情路由抢占成 405）、目录改名/删除必须走标准方法与信封
- `api-path-convention`: 新增要求——调用面扫描出的方法必须在命中视图接受的方法集合内，不只要求「路径能解析」

## Impact

- 后端：`apps/workflow/urls.py`、`apps/workflow/views_api.py`
- 前端：`frontend/src/modules/workflow/api.ts`（3 处调用）、必要时 `frontend/src/modules/workflow/stores/libraryStore.ts` 的信封读取
- 测试：`tests/graybox/unit/test_api_path_callers.py`（扩展 Caller 记录方法 + 新增用例）；既有 `test_workflow_directory_update.py` / `test_workflow_prototype_envelope.py` 必须继续通过
- 数据：无模型变更、无迁移、不改写存量数据
- 接口契约：路由「谁先匹配」变化，但对外可见的路径、字段、信封形态不变（legacy 平铺信封特例保持）
