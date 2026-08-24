# PRD-05 — 用例管理 (Case Manager)

> 关联模块：`apps/case_manager/` · 前端：`frontend/src/modules/case-manager/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.5
> 关联上游：[`PRD-04-元素定位`](./PRD-04-元素定位.md)（测试点元素选取 XPath）· [`PRD-09-工作流工作台`](./PRD-09-工作流工作台.md)（积木同步为用例）
> 关联下游：[`PRD-06-执行引擎`](./PRD-06-执行引擎.md)（steps_json 执行输入）
> 版本：v7.5 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v7.5 | 2026-08-21 | 补 config_json 双格式（4 模块 + 单接口 meta/request/cases）；§5.5 标注 403/423 视图层口径漂移；登记 steps_json↔steps_data/steps_data_write 三层映射 |
| v7.4 | 2026-08-19 | 工作台顶栏随子项切换：标题/副标题按 4 类型子项（UI/Web/业务功能/API）分别展示 |
| v7.3 | 2026-08-19 | 导航重构：页内 4 类型 Tab 改为侧边栏「用例管理」分组子项（Android UI 自动化用例 / Web 自动化测试用例 / 业务功能用例 / API 接口用例），各自独立路由（/cases/ui、/cases/web、/cases/storage、/cases/api，/cases 重定向到 /cases/ui）；编辑器退出目标同步改为对应子路由 |
| v7.2 | 2026-08-19 | PRD/ARCH 分工回退：§4.1 移除私有函数名 `get_step_types_by_target` 与缓存实现，改产品口径并指向 ARCH-05 §3.2 |
| v7.1 | 2026-08-19 | 格式对齐 PRD-03：文头补关联上下游 PRD；校正端点/文件计数（legacy 26 条 path、DRF 6 个 ViewSet、views 文件 10 个、composables 16 个）；登记 StepType 枚举与 STEP_TYPE_META 内部漂移（screenshot/poll_text）；修正「YAML 批量导入」为 JSON `/definitions/batch`；补错误码与契约变更 |
| v7.0 | 2026-08-14 | 按仪表盘 PRD 格式重构：移除实现细节（行数/实施状态/已知问题），补齐功能详细规格、布局视觉、后端功能逻辑、API 字段级契约、数据来源表、非功能/非目标/约束/索引；校正 4 类用例（UI/Web/API/Storage）、步骤类型注册表 29 种、API 用例统一 config_json、协作字段 |
| v6.0 | 2026-07-27 | 裸 client 收敛到 api 子模块 |

---

## 1. 功能定位

用例管理是平台的**测试资产管理中枢**。用户在此创建、组织、编排 4 类测试用例（UI 自动化 / Web 自动化 / API 测试 / 功能业务），通过步骤编排器编写操作序列，并管理协作（编辑锁/持久锁/可见性/权限）。页面由左侧目录树 + 右侧内容区构成，4 类型切换在侧边栏「用例管理」分组子项。

**核心职责**：

- **组织**：二级目录树，按 4 类型独立缓存
- **编排**：步骤编排器（步骤类型注册表驱动，跨平台 29 种）
- **协作**：编辑锁（30min 超时）、持久锁、可见性控制、编辑权限
- **导入导出**：JSON 批量导入（≤500 条）/ YAML 导出
- **供给下游**：向执行引擎提供 `steps_json` 作为执行输入

---

## 2. 功能详细规格

### 2.1 目录树（F-01）

#### 2.1.1 目录树展示（F-01-01）

左侧目录树，按 4 类型独立缓存（切换侧边栏子项复用）。节点区分目录/用例，用例节点显示优先级标签（P0=红 / P1=黄 / P2=灰），禁用用例删除线+灰。

**组件**：`DirectoryTree.vue`。

#### 2.1.2 目录操作（F-01-02）

| 能力 | 说明 |
|------|------|
| 层级 | 二级目录（父 + 子），`UNIQUE(parent, name, case_type)` 同级名唯一 |
| 新建 | 目录 / 用例；子目录只能在目录下 |
| 重命名 | 同级名冲突 409 |
| 删除 | 含用例的目录二次确认 |
| 拖拽 | 长按 500ms 激活拖拽移动 |
| 批选 | 勾选 → 批量移动 |

**边界状态**：同级重名 409；父级非目录 400。

**验收标准**：目录 CRUD 完整；二级层级限制；批量移动不脱钩。

### 2.2 用例 CRUD（F-02）

4 类用例共享结构：工具栏（面包屑 + 计数 + 视图切换）→ 卡片/表格双视图。

#### 2.2.1 UI 自动化用例（F-02-01）

字段：title / category / description / steps_json（步骤 JSON）/ watchers（弹窗监控）/ package_name / priority / design_method / precondition / expected_result / metrics。

**组件**：`UiCaseList.vue` + `CaseEditor.vue` + `CaseCard.vue`。

#### 2.2.2 Web 自动化用例（F-02-02）

字段：title / url / precondition / steps（操作步骤）/ steps_json / custom_columns / rows（表格行）。Playwright 表格式编辑器。

**组件**：`WebCaseList.vue` + `WebCaseEditor.vue`。

#### 2.2.3 API 测试用例（F-02-03）

统一 `config_json`（双格式：4 模块 `case_info`/`steps`/`test_data`/`validation` 多步骤格式 + 单接口格式 `meta`/`request`/`cases`），替代扁平字段。

**组件**：`ApiCaseList.vue` + `ApiCaseEditor.vue`。

#### 2.2.4 功能业务用例（F-02-04）

表格式：title / precondition / steps / expected_result / custom_columns / rows。

**组件**：`StorageCaseList.vue` + `StorageCaseEditor.vue`。

**通用操作**：新建 → 跳转编辑器；点击卡片 → 详情面板；编辑锁状态实时显示（🔒/🔓）；30s 自动刷新。

### 2.3 步骤编排器（F-03）

#### 2.3.1 编排器（F-03-01）

步骤类型由注册表驱动（`STEP_TYPE_META`），前端 `GET /cases/step-types?target=xxx` 拉取。类型按目标平台分组：

| 目标 | 步骤类型 | 数量 |
|------|------|:--:|
| 通用（common） | click / long_click / swipe / wait / sleep / screenshot | 6 |
| Android | verify_text / adb_start_app / adb_kill_app / adb_wait_toast / adb_perf_element_time / adb_if_appear / adb_if_disappear / adb_loop_n / adb_loop_elements / adb_poll_text / wait_disappear | 11 |
| Web | web_navigate / web_fill / web_type / web_assert / web_wait / web_click / web_screenshot / web_step | 8 |
| API | api_request / api_assert / api_sleep / api_log | 4 |

> `StepType` 枚举（`models/step_types.py`）是唯一真相源，含 8 个 deprecated 旧类型（start_app/kill_app/perf_element_time/wait_toast/if_element_appear/if_element_disappear/loop_n/loop_elements），已由 `adb_*` 前缀新类型替代。
>
> ⚠️ 偏差：枚举与 `STEP_TYPE_META` 存在内部漂移——`screenshot` 仅在 META（不在枚举）、`poll_text` 在枚举（不在 META），前端注册表以 META 为准（已登记）。

**组件**：`StepEditor.vue` + `step-utils.ts`。步骤结构 `TestStep`（type/xpath/timeout/expected_text/direction/distance/children/selector/value/url/method/headers/body/extract/assertions/expected_status/request_schema/response_schema）。

#### 2.3.2 元素选取器（F-03-02）

从 element-locator 已保存测试点元素中按页面+别名搜索，嵌入 XPath。EventBus 接收 `add-step-to-case`（元素定位页发送的 XPath）。

### 2.4 YAML 导入导出（F-04）

UI 类型多选用例导出为 YAML（ID/标题/步骤 JSON/优先级/包名）；JSON 批量导入（`POST /cases/definitions/batch`，≤500 条/次，ID 冲突跳过或覆盖）。

**组件**：`export_yaml` / `batchImportDefinitions`。

### 2.5 协作管理（F-05）

#### 2.5.1 编辑锁 + 强制编辑（F-05-01）

| 规则 | 说明 |
|------|------|
| 获取 | 打开编辑器自动获取锁（30min 超时） |
| 冲突 | 他人编辑中只读 + 黄色横幅；423 冲突 |
| 释放 | 正常保存释放 / 超时自动释放 |
| 强制 | 创建者可强制踢出 |

#### 2.5.2 持久锁 + 可见性 + 权限（F-05-02）

| 机制 | 取值 |
|------|------|
| 持久锁（locked） | 创建者锁定，他人只读，仅创建者解除 |
| 可见性（visibility） | public / hidden / restricted（+ permitted_users） |
| 权限（permission） | edit / readonly / restricted（+ permitted_editors） |

---

## 3. 布局与视觉设计

> 颜色/字号引用 Doodle Craft 令牌（[`frontend/CLAUDE.md` §2](../../frontend/CLAUDE.md)）。模块色青绿 `--c-case` #4ECDC4。

### 3.1 页面布局

```
┌─────────────────────────────────────────────┐
│ 侧边栏：「用例管理」分组（可展开，4 子项）        │
│  UI / Web / 业务功能 / API 接口用例            │
├──────────┬──────────────────────────────────┤
│ WorkbenchHeader                              │
├──────────┬──────────────────────────────────┤
│ 目录树    │ 工具栏（面包屑/计数/视图切换）      │
│ (左 300px)│  ├ 卡片视图 / 表格视图             │
│          │  └ （按侧边栏子项切换类型）          │
└──────────┴──────────────────────────────────┘
```

### 3.2 组件规格

| 元素 | 规格 |
|------|------|
| 目录树 | el-tree 二级，右键菜单 + 长按拖拽 + 批选 |
| 用例卡片 | 优先级色条（P0红/P1黄/P2灰）+ 标题/创建人/修改时间/步骤数/锁状态 |
| 步骤编排器 | 类型分组选择器 + 动态字段 + HTML5 拖拽 + 单步试运行 |
| 优先级标签 | P0=红 / P1=黄 / P2=灰 |

---

## 4. 后端功能逻辑

### 4.1 步骤类型注册表

`models/step_types.py` 的 `STEP_TYPE_META` 注册表是唯一权威数据，按目标平台（common / android / web / api）分组；`GET /cases/step-types?target=` 供前端拉取（实现结构见 ARCH-05 §3.2）。

> ⚠️ META 与 `StepType` 枚举存在内部漂移（`screenshot` 仅 META / `poll_text` 仅枚举），见 §2.3.1 登记。

### 4.2 编辑锁（30min）

`editing_by` + `editing_since` 字段；超时 30min 自动释放；强制踢出（创建者）。

### 4.3 持久锁 / 可见性 / 权限

| 字段 | 语义 |
|------|------|
| `locked` | 持久锁（创建者控制） |
| `visibility` + `permitted_users` | 可见性（public/hidden/restricted） |
| `permission` + `permitted_editors` | 编辑权限（edit/readonly/restricted） |

### 4.4 目录唯一约束

`UNIQUE(directory, title)` 同目录标题唯一；`UNIQUE(parent, name, case_type)` 同级目录名唯一。

---

## 5. API 接口功能

鉴权：全部端点需 JWT Bearer 鉴权。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

> 双视图层共存：DRF ViewSets（6 个，含手工注册的 CaseActionsViewSet，新标准）+ legacy Django views（26 条 path 条目，旧前端），两者前缀不冲突。
>
> 前端消费：legacy 26 条 path 全部被前端消费（✅）——经模块根 `api.ts`（step-types）与 `api/` 5 子模块，导出文件下载经 `window.open` 直链（`UiCaseList.vue`）；DRF ViewSet 与 legacy 双注册中前端以 legacy 为主。

### 5.1 端点总览

| 资源 | 端点（路径） | 说明 |
|------|------|------|
| 目录 | `GET/POST /cases/directories`、`/directories/create`、`/directories/{id}`、`/directories/{id}/permission`、`/directories/batch-move` | 目录 CRUD + 权限 + 批量移动 |
| UI 用例 | `GET/POST /cases/definitions`、`/definitions/{case_id}`、`/definitions/batch` | UI 用例 CRUD + 批量 |
| 锁/权限 | `/definitions/{case_id}/lock`、`/unlock`、`/case-lock`、`/case-unlock`、`/visibility` | 编辑锁/持久锁/可见性（DRF CaseActionsViewSet + legacy） |
| Web 用例 | `GET/POST /cases/web/definitions`、`/{case_id}`、`/batch` | Web 用例 CRUD |
| API 用例 | `GET/POST /cases/api-testing/definitions`、`/{case_id}`、`/batch` | API 用例 CRUD |
| Storage 用例 | `GET/POST /cases/storage/definitions`、`/{case_id}`、`/batch` | Storage 用例 CRUD |
| 步骤类型 | `GET /cases/step-types?target=` | 步骤类型注册表 |
| YAML | `POST /cases/export/yaml`、`GET /cases/exports`、`/exports/{filename}` | 导出/下载 |

### 5.2 目录（CaseDirectory）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `parent_id` | number | ID / 父节点（二级） |
| `name` | string | 目录名（同级唯一） |
| `case_type` | string | ui_automation / storage / api_testing / web_automation |
| `sort_order` | number | 排序 |
| `created_by` | string | 创建者 |
| `allow_create` / `allow_delete` | boolean | 权限 |

### 5.3 用例（TestDefinition）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | CharField 主键（如 TC-login-001） |
| `case_type` | string | ui_automation / storage / api_testing / web_automation |
| `title` | string | 标题（同目录唯一） |
| `category` / `description` | string | 分类 / 描述 |
| `steps` / `steps_json` | string | legacy 步骤 / 结构化步骤 JSON |
| `watchers` | JSON | 弹窗监控 `[{xpath, action}]` |
| `enabled` | boolean | 启用 |
| `package_name` | string | 目标 App 包名 |
| `priority` | string | P0/P1/P2 |
| `design_method` / `precondition` / `expected_result` / `metrics` | string | IoT 扩展字段 |
| `directory_id` | number | 所属目录 |
| `created_by` / `updated_by` | string | 创建/修改者 |
| `editing_by` / `editing_since` | string | 编辑锁 |
| `locked` | boolean | 持久锁 |
| `visibility` / `permitted_users` | string | 可见性 + 白名单 |
| `permission` / `permitted_editors` | string | 权限 + 白名单 |

> ⚠️ 字段名三层映射（v7.5 登记）：模型字段 `steps_json` ↔ DRF 读字段 `steps_data`（`SerializerMethodField`）/ 写字段 `steps_data_write`（`JSONField(source="steps_json")`，`serializers.py:106-107`）——API 线缆对外用 `steps_data`/`steps_data_write`，模型层统一落 `steps_json`。

### 5.4 其余类型差异字段

| 类型 | 差异字段 |
|------|------|
| WebTestCase | `url`、`custom_columns`、`rows`（表格行） |
| StorageTestCase | `custom_columns`、`rows`（表格行） |
| ApiTestCase | `config_json`（双格式：4 模块 case_info/steps/test_data/validation + 单接口格式 meta/request/cases） |

### 5.5 错误码汇总

| 状态码 | 场景 |
|:--:|------|
| 400 | 必填字段为空（name / title 等）/ 父级非目录 / 目录层级超二级 |
| 403 | 无编辑权限（permission=readonly 或非白名单） |
| 404 | 目录 / 用例不存在 |
| 409 | 同级重名（目录 name / 用例 title）/ ID 冲突 |
| 423 | 他人编辑中（编辑锁冲突） |

> ⚠️ 实现口径漂移（v7.5 登记）：上表「无权限 403 / 编辑冲突 423」为产品口径。实际 legacy `api_lock.acquire_edit_lock` 对 readonly/restricted/owner 锁定/编辑中四类冲突**全部返回 423**（`api_lock.py:89/93/96/102`）；DRF `views_drf._raise_lock_error`（`views_drf.py:75-83`）将 423 等非 404/400 一律映射为 403（PermissionDenied）。故实际 HTTP 状态码随视图层（legacy vs DRF）漂移。

### 5.6 契约变更

| 版本 | 变更 |
|------|------|
| v7.0 | API 用例统一 `config_json`（4 模块）替代扁平字段；步骤类型注册表收敛为 `STEP_TYPE_META` 29 种 |
| v7.1 | 计数校正（legacy 26 条 path、DRF 6 ViewSet）；「YAML 批量导入」更正为 JSON `POST /cases/definitions/batch`；无字段契约破坏 |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `cm_case_directories` | cm_ | 二级目录树 |
| `cm_test_definitions` | cm_ | UI 自动化用例 |
| `cm_web_testcases` | cm_ | Web 自动化用例 |
| `cm_api_testcases` | cm_ | API 测试用例 |
| `cm_storage_testcases` | cm_ | 功能业务用例 |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| 容量 | YAML 导入 | ≤500 条/次 |
| 可靠性 | 编辑锁超时 | 30min 自动释放 |
| 一致性 | 步骤类型 | `STEP_TYPE_META` 单一真相源 |
| 兼容性 | 4 类型编辑器 | UI/Web/API/Storage 齐全 |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| 用例执行 | 由执行引擎承担，本模块只做定义 |
| 元素 CRUD | 由元素定位承担，本模块只读引用 |
| 设备管理 | 由设备管理承担 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 步骤类型唯一真相源 `StepType` 枚举 | `models/step_types.py` |
| C-02 | 同目录标题唯一、同级目录名唯一 | models UNIQUE 约束 |
| C-03 | 写操作收敛：View → api.py → ORM | `api.py` + 6 子模块 |
| C-04 | 响应统一 `{status, data}`，snake_case | 全部端点 |
| C-05 | 双视图层共存：DRF + legacy | `views_drf.py` + `views_*.py` |
| C-06 | 用例 ID CharField 主键（自定义 ID） | `models.py` |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/case-manager/index.vue` | 页面编排 |
| 前端 | `frontend/src/modules/case-manager/api.ts` | facade re-export |
| 前端 | `frontend/src/modules/case-manager/api/`（5 子模块） | directories/uiAutomation/storage/apiTesting/webAutomation |
| 前端 | `frontend/src/modules/case-manager/components/` | DirectoryTree/CaseEditor/StepEditor/StepViewer/CaseCard/WatcherPanel + 4 CaseList + 4 Editor |
| 前端 | `frontend/src/modules/case-manager/composables/`（16 个） | useCaseManager/useStepDragDrop/useEditLock 等 |
| 后端 | `apps/case_manager/models.py` + `models_web.py` + `models_storage.py` + `models_api.py` | 5 表定义 |
| 后端 | `apps/case_manager/views.py` + `views_*.py`（10 文件） | legacy + DRF 视图 |
| 后端 | `apps/case_manager/api_*.py`（7 文件） | 跨模块写操作 |
| 后端 | `apps/case_manager/urls.py` | 路由（DRF router + legacy） |
| 共享 | `models/step_types.py` | 步骤类型注册表 + TestStep |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 4 类用例 CRUD、步骤编排、目录组织、协作管理、YAML 导入导出 |
| 我不能做什么 | 执行用例（执行引擎）、元素 CRUD（元素定位）、设备管理（设备管理） |
| 如需越界 | 通过 api.py 向执行引擎（get_enabled_definitions）、dashboard（只读 count）、workflow/AI 提供数据 |
| 数据可见性 | 按 visibility/permission 控制，跨用户隔离 |
