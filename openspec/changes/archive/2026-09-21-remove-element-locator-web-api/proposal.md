## Why

元素定位页面目前把 **Android 页面 / Web 元素 / API 接口** 并列为三个系统项目，但 Web 与 API 两域与本平台「Android UI 自动化」主线没有闭环价值：这两域的叶子在前端除元素定位详情页自身外无任何消费方，其分组写通路早已按 `element-locator-projects` 判定为 **HTTP 410**。

更关键的是，Web/API 的模型被三处**外部能力**顺带依赖，使「元素定位」承担了本不属于它的职责：

- `apps/dashboard/views.py` 用 `WebElement` / `ApiEndpoint` 出「Web元素 / API接口」KPI
- `frontend/src/modules/workflow` 用 `/elements/web-groups/`、`/elements/web/`、`/elements/api-endpoints/` 支撑画布「关联 API 接口」
- `tools/seed_api_endpoints.py` 把**平台自身的 API** 存进 `ApiGroup` / `ApiEndpoint` 作为「接口资产目录」

本次把这三域一并下线，让元素定位回归单一的 Android 页面库，并让上述三处职责各自消失或另择载体。

## What Changes

### 1. 前端元素定位页面：三项目 → 仅 Android

- `ProjectList.vue`：项目卡片仍由 `GET /elements/projects/` 驱动，但页面只应出现 `android` 一个项目
- `components/LocatorTree.vue`：新建文件标签固定为「新建页面」，三类域标签分支删除
- `components/LocatorFilePanel.vue`：删除 Web 表单（`WEB_LOCATOR_TYPES`）、API 表单（`API_METHODS`）及 `saveWeb` / `saveApi` / `loadDetail` 中的 web/api 分支
- `types.ts`：`LocatorProjectCode` 收敛为 `'android'`；删除 `WEB_LOCATOR_TYPES`、`API_METHODS`、`WebElementDetail`、`ApiEndpointDetail`；`LocatorFileKind` 收敛为 `'page'`
- `api.ts`：删除 8 个 web/API 封装（`apiGetWebElement`、`apiGetApiEndpoint`、`apiCreateWebElement`、`apiUpdateWebElement`、`apiDeleteWebElement`、`apiCreateApiEndpoint`、`apiUpdateApiEndpoint`、`apiDeleteApiEndpoint`）
- `routes.ts`：删除 `/elements/web`、`/elements/api` 两条兼容重定向
- `composables/useLocatorTree.ts`：`addFile` / `removeFile` 的 web/api 分支与 `FILE_KIND_BY_CODE` 按域映射删除

### 2. 后端 `element_locator` 下线 Web/API 域

- 删除模型 `WebGroup` / `WebElement` / `ApiGroup` / `ApiEndpoint` / `WebPageFlow`，连带五张表 `el_web_groups` / `el_web_elements` / `el_api_groups` / `el_api_endpoints` / `el_web_page_flows`
- 删除对应 `serializers.py` 序列化器、`views_drf.py` 五个 ViewSet、`urls.py` 五条 router 注册（`web-groups` / `web` / `api-groups` / `api-endpoints` / `web-flows`）、`admin.py` 五处注册
- 删除 `api.py` 中 WebElement / WebPageFlow / WebGroup 的写函数；删除 `api_projects.py`、`api_directories.py` 中的 web/api 文件计数、树构建、移动与批量删除分支
- **新增迁移删除上述五张表 —— 既有 Web/API 数据将不可恢复**
- 保留：`LocatorProject` / `LocatorDirectory` / `Page` / `Element` / `PageFlow`（Android 跳转流）

### 3. workflow 模块下线 Web 页面关联与 API 接口关联

- `workflow/api.ts`：删除 `listWebGroups` / `listWebGroupElements`
- `workflow/data/pageCatalog.ts`：删除 `mapWebGroup` 与 WebGroup 素材拉取分支、删除 `fetchApiEndpoints` 与 `ApiEndpointRef`
- `components/vueflow/NodeContextMenu.vue`：删除「关联 Web 页面…」菜单项（其数据源正是 `listWebGroups` / `listWebGroupElements`）；删除「关联 API 接口…」菜单项、`apiEndpoints` 拉取与接口选择器
- `components/vueflow/PageFlowVueFlow.vue`：删除 `handleLinkApi`、`ApiNode` 的新建入口与 `store.addApiPort` 调用
- `stores/workflowStore.ts`：删除 `linkApiEndpoint`、`addApiPort` 及其暴露
- 删除 `ApiNode` 节点类型：`types/workflow.ts` 的联合类型、`registry/nodeRegistry.ts` 注册项、`composables/useVueFlowAdapter.ts` 映射、`components/vueflow/PageFlowNode.vue` 的 `isApi` 渲染分支
  - **依据（核实所得，非推测）**：`nodeRegistry.ts` 注释写明「API 节点：无默认端口，关联 API 端点后从 schema 动态生成」，其 `defaultInputs` / `defaultOutputs` 均为空；`addApiPort` 全仓唯一调用点在 `PageFlowVueFlow.vue` 的接口选择器流程内。即 **ApiNode 获得端口的唯一途径就是本次要删除的接口关联**，保留它只会留下一个无端口的不可用节点
- 结果：页面流画布只保留 Android 页面素材与其节点类型（`PageNode` / `PopupNode` / `StartNode` / `EndNode`）

### 4. 接口资产目录能力退役

- 删除 `tools/seed_api_endpoints.py`
- 删除 `tests/graybox/unit` 中该目录的守护面：`test_api_path_callers.py` 的 `catalog` 面与其规模下限
- 退役 `openspec/specs/api-endpoint-catalog` 能力（该 spec 的全部需求随之移除）
- `test_api_path_callers.py` 由**四面**收敛为**三面**（前端 API 层 / tests 调用面 / YAML 用例），`api-path-convention` 的调用面枚举同步

### 5. dashboard KPI 去掉 Web元素 / API接口

- `apps/dashboard/views.py`：删除 `WebElement` / `ApiEndpoint` 的 import 与两个 breakdown 条目
- `frontend/src/modules/dashboard/DashboardView.logic.ts`：删除 `'web'` / `'api'` 两个 KPI 定义

### 6. 测试同步

- `frontend/tests/element-locator/p0/api.spec.ts`：由 18 个收敛为 10 个存活封装
- `tests/graybox/unit/test_element_locator_views_split.py`、`test_element_locator_group_writes_removed.py`、`test_element_locator_drf_writes.py`、`tests/arch/test_view_write_convergence.py`：删除 web/api 断言
- `tests/graybox/unit/test_api_path_callers.py`：撤销 catalog 面，并按实测重登记 `frontend` 面规模下限

### 7. **BREAKING**

- 元素定位由三项目变为单项目；`/api/elements/web/`、`/web-groups/`、`/api-groups/`、`/api-endpoints/`、`/web-flows/` 全部消失（子路径一律 404）
- `api-endpoint-catalog` 能力退役：接口资产目录不再存在，接口测试不再能从该目录选用资产
- workflow 原型中已保存的「页面 → API 接口」关联数据成为无效引用（需一并清理，见 design）

## 明确移出本变更范围

- **Android 域 `PageFlow`（页面跳转流）保留**：它既非 Web 也非 API，属 Android 域能力，本次不动
- **dashboard 的「Web用例 / API用例」（`web_automation` / `api_testing`）保留**：那是**用例类型**，来自 case-manager，与元素定位的 Web/API 域无关
- **`frontend/src/modules/element-locator/AGENTS.md`（0 字节）**：仍按前次指示只记录、不解决
- `element-locator` 页面上其余既有死分支（`back` emit、`hideIdentity`、`activeFileId` 高亮链路、`reload` 暴露等）：另开

## 关联文档

- 需求编号：`PRD-04-元素定位`（本次为能力下线，需求本身需同步收窄）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-projects`：由「exactly three locator projects（android/web/api）」收窄为**仅 android 单项目**；叶子类型由三域收敛为 `page`；「Legacy group write path retired」需求随 WebGroup/ApiGroup 删除而移除；「Leaf identity preserved on migration」收窄为 Android 页面
- `api-path-convention`：端到端调用面的枚举去掉「端点资产目录」一面。因 `openspec validate` 不允许 MODIFIED 丢弃既有场景，故以「移除旧的『端到端调用方遵循唯一写法』+ 新增收窄后的『前端与测试调用面遵循唯一写法』」表达，守护由四面收敛为三面（见 design D10）
- `api-endpoint-catalog`：**整能力退役** —— 该 spec 全部需求进入 REMOVED（含 Reason 与 Migration）

## Impact

- **前端 8 个文件**：`element-locator` 的 `types.ts` / `api.ts` / `routes.ts` / `composables/useLocatorTree.ts` / `components/LocatorTree.vue` / `components/LocatorFilePanel.vue`；`workflow` 的 `api.ts` / `data/pageCatalog.ts` / `components/vueflow/NodeContextMenu.vue` / `components/vueflow/PageFlowVueFlow.vue` / `stores/workflowStore.ts`；`dashboard/DashboardView.logic.ts`
- **后端 8 个文件**：`element_locator` 的 `models.py` / `serializers.py` / `views_drf.py` / `urls.py` / `admin.py` / `api.py` / `api_projects.py` / `api_directories.py`；`dashboard/views.py`；新增 1 个迁移
- **工具 1 个**：`tools/seed_api_endpoints.py` 删除
- **测试 6 个**：`frontend/tests/element-locator/p0/api.spec.ts` 及 `tests/graybox/unit` 4 个 + `tests/arch` 1 个
- **规格 3 个**：`element-locator-projects`（改）、`api-path-convention`（改）、`api-endpoint-catalog`（删）
- **数据**：五张表与其全部数据删除，不可恢复；workflow 原型中的 API 关联引用需清理
- **接口**：`/api/elements/` 下 web / web-groups / api-groups / api-endpoints / web-flows 及其子路径全部 404
- **恢复方式**：代码可 `git revert`；**数据不可自动恢复**（需数据库备份，或重跑迁移前手工导出）
