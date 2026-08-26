# PRD-09 — 工作流工作台 (Workflow Workbench)

> 关联模块：`apps/workflow/` · 前端：`frontend/src/modules/workflow/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.9（可视化编排工具）
> 关联上游：[`PRD-04-元素定位`](./PRD-04-元素定位.md)（页面树 / Web 分组 / API 接口只读目录）· [`PRD-05-用例管理`](./PRD-05-用例管理.md)（步骤编排与用例定义主权归其承担；本模块积木用例已下线）
> 关联下游：[`PRD-06-执行引擎`](./PRD-06-执行引擎.md)（页面流经其执行）
> 版本：v5.3 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v5.3 | 2026-08-21 | 正文清理 Blockly/test_case 残留（§2.2/§2.4 收缩为已下线注记）：文头 v5.2 决策与正文对齐；补页面流语义摘要 F-03-03；偏差登记更新（DRF 信封/config 命名）；文件索引按代码真相重列 |
| v5.2 | 2026-08-19 | **下线积木测试用例**：移除 Blockly 编辑器 / `doc_type=test_case` / 用例库双向桥接；工作流仅保留目录 + VueFlow 页面流；后端迁移清库并拒绝新建/导入 test_case |
| v5.1 | 2026-08-19 | 补齐各 F「职责与边界」声明（资源库与用例目录边界、同步后用例主权、页面流编排不执行、导入导出范围） |
| v5.0 | 2026-08-19 | 按 PRD-03 设备检查器格式重构：移除设计目录/数据流/验收汇总/实施状态/已知问题旧章节，补齐十章 + 附录A；同步代码真相（wf_ 两表 + doc_id 自然键、双路由体系 12 legacy + DRF ViewSet、Blockly 18 块 8 分组、VueFlow 端口体系、跨模块违规已修复、真实运行时未实现） |
| v4.0 | 2026-07-27 | 前端 JS 时代基线（目录树 + Blockly + VueFlow + 用例桥接 + 31 项验收） |

---

## 1. 功能定位

工作流工作台是平台的**页面流可视化编排中枢**：用户通过 VueFlow 节点图编排页面跳转流，配合文件系统风格的资源管理。页面由左侧目录+文件树与右侧主区（目录看板 / VueFlow 编辑器二选一）构成。

**核心职责**：

- **资源库**：目录树 + JSON 文档（**仅页面流** `page_flow`）服务端持久化（`wf_` 两表，`doc_id` 自然键）
- **VueFlow 页面流**：节点注册表驱动、端口连线验证、右键菜单
- **导入导出**：`workflow-doc-v1` envelope（页面流快照；不再接受 `testcase-scratch-v1`）

> **已下线**：Blockly 积木测试用例（`doc_type=test_case`）、与用例管理的双向同步/导入。测试步骤编排请使用用例管理（PRD-05）。

工作流工作台是**管理模块（有写操作）**：目录与文档落库，写库全部经 `api.py`；前端状态用 Pinia（资源库 + VueFlow 节点图）。

---

## 2. 功能详细规格

### 2.1 模块一：资源库与目录树

**F-01-01 目录管理**

**功能实现逻辑**：用户在左侧目录树创建 / 重命名 / 删除 / 移动目录（长按拖拽），展开折叠状态 localStorage 持久化。

**详细功能点**：

- **层级校验**：同级名称唯一（`UNIQUE(parent, name)`）；移动不能移到自己或子孙节点内
- **级联删除**：删除目录级联删除其子目录与文档
- **拖拽移动**：`POST /workflow/directories/{id}/move`（parent_id）

**职责与边界**：目录/文档仅存工作流编排资源（wf_ 两表）；用例目录树（cm_）归用例管理（PRD-05），两者独立、不同步。

**验收方式**：目录 CRUD 完整；移入自身/子孙被拦截；删除父目录后子目录与文档一并移除；刷新后展开状态保持。

**F-01-02 文件浏览器**

**功能实现逻辑**：右侧卡片网格展示当前目录的文档，hover 显示操作按钮（重命名 / 删除 / 移动）。

**验收方式**：按目录过滤展示；hover 操作可用；空目录显示空态。

**F-01-03 文档 CRUD（JSON 持久化）**

**功能实现逻辑**：页面流以 JSON 文档落库（`doc_type` 仅 `page_flow`）。`doc_id` 为业务自然键，创建时自动生成（`WF-PF-YYYYMMDD-HHMMSS-XXXX`），导入导出时作为跨环境唯一标识；`config_json` 保存编排内容（VueFlow 节点图）。

**详细功能点**：

- **upsert**：`POST /workflow/documents/create`（无 doc_id 新建、带 doc_id 更新）
- **详情 / 更新 / 删除**：`GET/PUT/DELETE /workflow/documents/{doc_id}`
- **移动**：`POST /workflow/documents/{doc_id}/move`（directory_id）

**验收方式**：新建返回 doc_id 且刷新后仍在；同 doc_id 重复保存为更新不产生重复记录；移动后归属正确。

### 2.2 模块二：Blockly 测试用例编辑器

**已下线（v5.2）**：Blockly 积木测试用例（`doc_type=test_case`）与用例库双向同步已下线，步骤编排请使用用例管理（PRD-05）。F-02-01 ~ F-02-04 保留为下线占位（避免后续交叉引用断裂），不再维护详细规格与验收。

### 2.3 模块三：VueFlow 页面流编辑器

**F-03-01 节点图编排**

**功能实现逻辑**：ComfyUI 风格节点图编辑器，节点从注册表按类名创建（`nodeRegistry.ts`：PageNode / PopupNode / StartNode / ApiNode / EndNode）。画布支持缩放、平移、小地图。

**详细功能点**：

- **StartNode 4 模式**：app（启动应用）/ page（进入页面）/ url（打开链接）/ api（调接口）
- **节点端口**：entry（进入）/ navigation（跳转）/ popup_trigger（弹窗触发）/ popup_fixed（固定弹窗）/ popup_close（关闭弹窗）/ data（数据）

**组件**：`PageFlowVueFlow.vue` + `PageFlowNode.vue` + `workflowStore.ts` + `useVueFlowAdapter.ts`。

**职责与边界**：页面流仅做可视化编排与持久化，不直接执行；真实执行经执行引擎（PRD-06）——当前为未实现项（§4.3 登记）。

**验收方式**：5 类节点可创建；StartNode 4 模式可选；画布缩放/平移/小地图正常。

**F-03-02 连线验证**

**功能实现逻辑**：连线校验端口类型兼容；**Android / Web 域不可互连**（跨域连线拦截）。

**详细功能点**（端口颜色）：

| 端口 | 颜色 |
|------|------|
| entry | 蓝 `#5b9cf5` |
| navigation | 紫 `#a78bfa` |
| popup_trigger / popup_fixed | 红 `#f87171` |
| popup_close | 灰 `#8a8a96` |
| data | 回退蓝 `#5b9cf5` |

**验收方式**：类型不兼容连线被拒绝；Android/Web 域连线被拦截。

**F-03-03 页面流语义摘要**

**功能实现逻辑**：将页面流节点图转换为 AI 可读的结构化摘要——页面归属关系、跳转入口、页面下元素（含来源标注）、起点→终点路径列表。供 AI 助手（PRD-08）读取页面流结构，而非面向用户在画布展示。

**详细功能点**：

- **数据来源**：以文档 `config_json`（nodes/links 快照）为准，不实时 join 元素库；元素来源按 ID 前缀标注（snapshot / web_snapshot / builtin_pool / unknown）
- **触发方式**：由 AI 助手工具调用触发（后端 `api.py` 只读数据出口），非用户手动触发
- **降级**：任何字段缺失均安全降级；悬空连线、未知节点类型等异常写入解析告警，绝不抛错；路径提取防环、限深、限量

**职责与边界**：纯只读派生，不写库、不改节点图；元素目录不实时回查，以快照为准。

**验收方式**：给定页面流可稳定产出含节点/连线/路径的摘要；异常图（悬空连线、未知类型）不报错且告警可读。

**F-03-04 右键菜单**

**功能实现逻辑**：节点右键菜单（Teleported）支持关联页面/API、重命名、删除。

**组件**：`NodeContextMenu.vue`。

**验收方式**：菜单操作生效；关联页面/API 后节点展示关联信息。

### 2.4 模块四：导入导出

**F-04-01 从用例库导入**

**已下线（v5.2）**：从用例管理导入 `test_case` 文档（原 `ImportCasesDialog.vue` / `caseBridge.ts`）已随积木用例一并下线，F-04-01 保留为占位。

**F-04-02 JSON 导入导出**

**功能实现逻辑**：支持页面流 JSON 文件导入导出（`libraryStore.importDoc` / `exportDoc`，`index.vue` 提供文件选择与下载）。导入识别 `workflow-doc-v1` envelope 与裸页面流快照；`overwrite=true` 覆盖同 `doc_id` 文档。旧版 `testcase-scratch-v1` 与 `doc_type=test_case` 导入被拒绝。

**职责与边界**：仅 JSON envelope 文档级导入导出；不导出可执行任务；用例定义迁移归用例管理（PRD-05）。

**验收方式**：导出文件可再导入还原；同 `doc_id` 覆盖导入生效；`testcase-scratch-v1` 导入被拒绝并提示。

**F-04-03 首次初始化**

**功能实现逻辑**：空库首次进入时 `bootstrapIfEmpty` 自动创建「默认目录」，**不预置示例文件**。

**验收方式**：新库首次进入出现默认目录；无示例文件。

---

## 3. 布局与视觉设计

> 全部颜色/字号引用 Doodle Craft 主题令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)）。

### 3.1 主页面布局

```
┌───────────────────────────────────────────────────────┐
│ WorkbenchHeader（标题 + 面包屑 + 导入/保存/导出）        │
├──────────────┬────────────────────────────────────────┤
│ 目录+文件树   │ 主区（二选一）                          │
│ WorkflowDir   │ ├ 未打开文件：目录看板                   │
│ Tree          │ │   WorkflowFileBrowser（卡片网格）      │
│ （右键/长按）  │ └ 打开文件：VueFlow 节点图编辑器        │
└──────────────┴────────────────────────────────────────┘
```

- 两栏布局：左侧目录+文件树 → 右侧主区（目录看板 / VueFlow 编辑器二选一）
- 目录树：右键菜单（新建/重命名/删除）+ 长按拖拽移动 + 展开折叠
- 编辑器：VueFlow 页面流画布（无 Blockly、无双 Tab）

### 3.2 组件规格

| 元素 | 规格 |
|------|------|
| 目录树 | 树形嵌套（目录 + 文件）+ 右键菜单 + 长按拖拽 |
| 文件卡片 | 卡片网格，hover 显示操作按钮 |
| VueFlow 画布 | ComfyUI 风格节点 + 彩色端口 + 小地图 |
| 端口颜色 | entry 蓝 / navigation 紫 / popup 红 / popup_close 灰 |

### 3.3 边界状态（场景）

| 场景 | 行为 |
|------|------|
| 空库首次进入 | 自动创建「默认目录」 |
| 目录非空删除 | 二次确认后级联删除 |
| 移入自身/子孙 | 拦截提示 |
| 同名目录/文档 | 409 或提示重名 |
| 连线类型不兼容 | 连线被拒绝 |
| 导入 envelope 版本不支持 | 报错提示，不写入 |
| 请求失败 | ErrorState 错误态 + 重试 |

---

## 4. 后端功能逻辑

### 4.1 双路由体系（共存）

`apps/workflow/urls.py` 同时注册两套路由：

| 体系 | 路径特征 | 信封 | 消费方 |
|------|------|------|------|
| legacy 视图（`views.py`） | 无尾斜杠（12 端点） | `{status, ...}` | **前端当前消费** |
| DRF ViewSet（`views_api.py`） | 带尾斜杠（16 端点：目录 7 + 文档 9） | `{status, data}`（全局 `EnvelopeJSONRenderer` 包信封） | 已注册，前端未切换 |

> ⚠️ 偏差：两套端点并行，前端仍走 legacy 路径（含 `/create`、`/{id}/move`、`/import`、`/export` 子路径）；DRF 化收敛为待办技术债（已登记）。DRF 文档列表序列化器不含 config，详情序列化器做 `config` ↔ `config_json` 双向转换。

### 4.2 目录树与文档口径

- **目录**：自引用树（`parent` CASCADE），同级名唯一；移动防自身 / 防子孙；删除级联子目录与文档
- **文档**：`doc_id` 业务自然键（`WF-PF-YYYYMMDD-HHMMSS-XXXX`，仅 `page_flow`），`config_json` 存编排内容（节点图）；`directory` 外键 SET_NULL（删除目录后文档归未分类）
- **写库收敛**：View / ViewSet 仅分发，全部读写经 `api.py`（20 个函数白名单）

### 4.3 已知偏差登记

| 偏差 | 说明 |
|------|------|
| 真实运行时未实现 | VueFlow 页面流仅可视化编排与持久化，不执行：无后端 run 端点、无设备集成；真实执行由执行引擎（PRD-06）承担 |
| DRF 未收敛 | 双路由并行，前端走 legacy（平铺 `{status, ...}`）；DRF 路由已被全局 `EnvelopeJSONRenderer` 包 `{status, data}` 信封，双信封并存，收敛为待办技术债 |
| pageCatalog 裸客户端 | `data/pageCatalog.ts` 的 API 接口目录（`fetchApiEndpoints`）仍动态裸 import `@/shared/api-client` 请求 `/elements/api-endpoints`（bypass 本模块 api.ts，待修）；页面/元素/Web 分组已走 api.ts |
| config vs config_json 命名不一 | 数据库字段为 `config_json`（TextField），前端与 DRF 详情序列化器使用 `config`（JSON 对象），由 `serializers.py` 双向转换；legacy 视图返回 `config` |

---

## 5. API 接口功能

鉴权：全部端点需 JWT Bearer。legacy 响应 `{status, ...}` + snake_case；DRF 路由经全局 `EnvelopeJSONRenderer` 包 `{status, data}` 信封（已登记）。状态码：400 参数非法 / 404 不存在 / 409 冲突。

### 5.1 端点总览（legacy 12 端点，前端消费）

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/workflow/directories` | 目录列表（`directories` + 递归 `tree`） | ✅ |
| 2 | POST | `/api/workflow/directories/create` | 新建目录 | ✅ |
| 3 | POST | `/api/workflow/directories/{dir_id}` | 更新 / 删除（action=update\|delete） | ✅ |
| 4 | POST | `/api/workflow/directories/{dir_id}/move` | 移动目录 | ✅ |
| 5 | GET | `/api/workflow/documents` | 文档列表（`?directory_id=&doc_type=`） | ✅ |
| 6 | POST | `/api/workflow/documents/create` | 新建 / 更新文档（upsert） | ✅ |
| 7 | GET | `/api/workflow/documents/{doc_id}` | 文档详情（含 config） | ✅ |
| 8 | PUT | `/api/workflow/documents/{doc_id}` | 更新文档 | ✅ |
| 9 | DELETE | `/api/workflow/documents/{doc_id}` | 删除文档 | ✅ |
| 10 | POST | `/api/workflow/documents/import` | 导入 envelope（`?overwrite=`） | ✅ |
| 11 | GET | `/api/workflow/documents/{doc_id}/export` | 导出（`?download=`） | ✅ |
| 12 | POST | `/api/workflow/documents/{doc_id}/move` | 移动文档 | ✅ |

> DRF ViewSet 并行注册（16 端点，带尾斜杠：目录 ModelViewSet + move = 7，文档 ModelViewSet + import/export/move = 9）：`/directories/`、`/directories/{id}/`、`/directories/{id}/move/`、`/documents/`、`/documents/{doc_id}/`、`/documents/import/`、`/documents/{doc_id}/export/`、`/documents/{doc_id}/move/`。前端未消费。

### 5.2 目录（WorkflowDirectory）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `parent_id` | number | ID / 父目录（可空） |
| `name` | string | 目录名（同级唯一，必填） |
| `sort_order` | number | 排序权重 |
| `created_at` / `updated_at` | string | 时间戳 |

### 5.3 文档（WorkflowDocument）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `doc_id` | string | 业务自然键（唯一；`WF-PF-YYYYMMDD-HHMMSS-XXXX`，仅页面流） |
| `title` | string | 标题（必填） |
| `doc_type` | string | `page_flow`（`test_case` 已下线，新建/导入拒绝） |
| `config_json` | string(JSON) | 编排内容（VueFlow 节点图） |
| `directory_id` | number \| null | 所属目录（SET_NULL） |
| `description` | string | 描述 |
| `created_at` / `updated_at` | string | 时间戳 |

### 5.4 导入导出 envelope

- **envelope 格式**：`workflow-doc-v1`（含 doc_id / doc_type / title / config_json / directory 等）；兼容裸页面流快照；`testcase-scratch-v1` 与 `doc_type=test_case` 导入被拒绝
- **导入**：`POST /documents/import`，`overwrite=true` 覆盖同 doc_id；重复 doc_id 且未覆盖 → 409
- **导出**：`GET /documents/{doc_id}/export`（`download=1` 触发文件下载）

### 5.5 跨模块代理（前端转调元素目录，只读）

| 用途 | 端点 |
|------|------|
| 页面树 / 页下元素 | `GET /api/elements/pages`、`/pages/{id}/items` |
| Web 分组 / 元素 | `GET /api/elements/web-groups`、`/web?group_id=` |
| API 接口目录 | `GET /api/elements/api-endpoints`（经 `pageCatalog.ts` 裸客户端，非 api.ts） |

### 5.6 契约变更

| 版本 | 变更 |
|------|------|
| v4.0 | 服务端 JSON 持久化落地：wf_ 两表 + legacy CRUD 端点 + envelope 导入导出 |
| v4.x | 新增 DRF ViewSet 并行注册（16 端点）；前端仍走 legacy |
| v5.0 | 端点总览按代码真相校正为 legacy 12 + DRF 16；登记双信封差异；无字段契约破坏 |
| v5.2 | `doc_type` 收窄为 `page_flow`：`test_case` 新建/导入拒绝，wf_documents 清库（迁移 0002） |
| v5.3 | DRF 路由经全局 `EnvelopeJSONRenderer` 包 `{status, data}`（legacy 平铺并存）；新增页面流语义摘要数据出口（无独立 HTTP 端点） |

> 页面流语义摘要（F-03-03）为纯后端 AI 只读数据出口（`api_digest.py`，经 `api.py` 再导出），无独立 HTTP 端点。

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `wf_directories` | wf_ | 工作流资源目录树（自引用，同级名唯一） |
| `wf_documents` | wf_ | 页面流 JSON 文档（`doc_type` 仅 page_flow，doc_id 唯一，config_json） |
| `el_pages` / `el_elements` 等 | el_ | 只读：页面树 / 元素目录（经 element-locator，主权 PRD-04） |
| `cm_case_directories` / `cm_test_definitions` | cm_ | 已下线：用例库桥接移除，本模块不再读写（用例定义主权 PRD-05） |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|------|
| 性能 | 目录列表 | 单查询返回扁平列表 + 递归树 |
| 可靠性 | 编辑器自动保存 | 编辑内容防抖落库，刷新不丢 |
| 兼容性 | 导入 envelope | 兼容 workflow-doc-v1 / 裸页面流快照 2 种格式；testcase-scratch-v1 拒绝 |
| 一致性 | doc_id | 全局唯一自然键，跨环境导入导出可识别 |
| 一致性 | 跨模块调用 | 元素目录只读一律经本模块 api.ts 代理，组件不直连他模块 |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| Blockly 积木测试用例（`doc_type=test_case`） | v5.2 已下线；步骤编排归用例管理（PRD-05） |
| 真实运行时 / 设备执行（页面流直接执行） | 未实现：VueFlow 页面流仅编排与持久化；真实执行由 PRD-06 承担（差异已登记 §4.3） |
| 用例定义持久化主权 | 用例定义归用例管理（PRD-05） |
| 多智能体 / AI 编排 | 由 AI 助手（PRD-08）承担 |
| DRF 路由收敛切换 | 双路由并行保留（前端仍走 legacy），收敛为待办技术债 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | doc_id 自然键唯一，导入导出以此为跨环境标识 | `apps/workflow/api.py` |
| C-02 | 写库收敛：View / ViewSet → api.py → ORM（20 函数白名单） | `apps/workflow/api.py` |
| C-03 | 双路由体系共存：legacy（前端消费）+ DRF ViewSet（未切换） | `apps/workflow/urls.py` |
| C-04 | 响应 legacy `{status, ...}`；DRF 经全局 EnvelopeJSONRenderer 包 `{status, data}`（登记偏差） | `views.py` / `views_api.py` |
| C-05 | 前端跨模块调用经本模块 api.ts 代理（元素目录只读） | `frontend/src/modules/workflow/api.ts` |
| C-06 | 目录移动防自身/防子孙；删除级联 | `apps/workflow/api.py` |
| C-07 | 颜色/字号引用 Doodle Craft 令牌；端口色为协议字面量 | `types/workflow.ts` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/workflow/index.vue` | 页面编排（目录树 + 目录看板 / VueFlow 编辑器 + 导入导出 + 自动保存） |
| 前端 | `frontend/src/modules/workflow/api.ts` | 数据层（13 workflow + 4 元素只读代理） |
| 前端 | `frontend/src/modules/workflow/constants.ts` | 模块常量（节点类型 / 默认名称 / 文案） |
| 前端 | `frontend/src/modules/workflow/stores/libraryStore.ts` | 资源库 CRUD + 导入导出（doc_id 权威，config 缓存） |
| 前端 | `frontend/src/modules/workflow/stores/workflowStore.ts` | VueFlow 节点图状态 |
| 前端 | `frontend/src/modules/workflow/composables/useVueFlowAdapter.ts` | 节点/边转换 + 连线验证 |
| 前端 | `frontend/src/modules/workflow/registry/nodeRegistry.ts` | 节点类映射 |
| 前端 | `frontend/src/modules/workflow/types/workflow.ts` | 端口类型 / 连线规则 / 颜色 / 图数据类型 |
| 前端 | `frontend/src/modules/workflow/data/pageCatalog.ts` | 页面/元素/Web 分组目录加载器（API 接口目录经裸客户端） |
| 前端 | `frontend/src/modules/workflow/components/WorkflowDirTree.vue` / `WorkflowFileBrowser.vue` | 目录+文件树 / 目录看板 |
| 前端 | `frontend/src/modules/workflow/components/vueflow/` | PageFlowVueFlow / PageFlowNode / NodeContextMenu |
| 后端 | `apps/workflow/urls.py` | 双路由（legacy + DRF router） |
| 后端 | `apps/workflow/views.py` / `views_api.py` | legacy 视图 / DRF ViewSet |
| 后端 | `apps/workflow/serializers.py` | DRF 序列化器（config ↔ config_json） |
| 后端 | `apps/workflow/api.py` | 读写白名单 + envelope 导入导出 + 语义摘要再导出 |
| 后端 | `apps/workflow/semantics.py` / `api_digest.py` / `semantics_paths.py` | 页面流语义摘要 / AI 数据出口 / 路径摘要 |
| 后端 | `apps/workflow/models.py` | wf_ 2 表定义 |
| 路由 | `config/urls.py` | `api/workflow/` |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 目录/文档资源管理、VueFlow 页面流编排、JSON 导入导出 |
| 我不能做什么 | 真实执行用例（PRD-06）、管理用例定义主权（PRD-05）、管理设备（PRD-02）、管理元素资产（PRD-04，仅只读目录） |
| 如需越界 | 页面/元素/Web/API 目录经 element-locator 只读接口 |
| 数据可见性 | 工作流资源为平台共享库，不按用户隔离 |
