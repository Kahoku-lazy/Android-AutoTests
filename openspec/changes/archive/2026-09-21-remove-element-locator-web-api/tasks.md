## 1. 数据留档与后端模型删除（不可逆）

- [x] 1.1 应用迁移前留档：`python manage.py dumpdata element_locator --indent 2 -o temps/element_locator_backup.json`；验证：文件生成，且其中包含 `element_locator.webelement` / `element_locator.apigroup` / `element_locator.apiendpoint` / `element_locator.webgroup` / `element_locator.webpageflow` 五个 model 中所有非空者
- [x] 1.2 从 `apps/element_locator/models.py` 删除 5 个模型 `WebGroup` / `WebElement` / `ApiGroup` / `ApiEndpoint` / `WebPageFlow`；验证：`grep "^class "` 仅剩 `LocatorProject` / `LocatorDirectory` / `Page` / `Element` / `PageFlow`
- [x] 1.3 `python manage.py makemigrations element_locator` 生成删除迁移，并在该迁移 docstring 标注「删除 5 张表，数据不可恢复」；验证：新迁移文件含恰好 5 个 `DeleteModel`
- [x] 1.4 `python manage.py migrate` 应用；验证：`manage.py showmigrations element_locator` 全部已应用，且 `el_web_groups` / `el_web_elements` / `el_api_groups` / `el_api_endpoints` / `el_web_page_flows` 五张表不再存在
- [x] 1.5 【实施中新增，原任务清单遗漏】移除 web / api 两个系统项目行与其目录：delta 要求 `exactly one locator project with code android`，而 1.2 只删模型，DB 中仍留 3 行 `el_locator_projects`（android/web/api）与 3 行目录。已在 0015 迁移末尾追加 `RunPython(remove_web_api_projects, restore_project_rows)`；验证：`LocatorProject` 只剩 `android`、`LocatorDirectory` 由 3 → 1，且 `Page` 5 行 / `Element` 32 行不变（`Page.directory` 为 SET_NULL，页面未被连带删除）

## 2. 后端视图 / 序列化 / 路由 / admin / api 收敛

- [x] 2.1 `serializers.py` 删除 5 个序列化器（WebGroup / WebElement / ApiGroup / ApiEndpoint / WebPageFlow）；验证：`grep -E "WebGroup|WebElement|ApiGroup|ApiEndpoint|WebPageFlow"` 命中 0
- [x] 2.2 `views_drf.py` 删除 5 个 ViewSet 及其 import；验证：`grep "ViewSet" apps/element_locator/views_drf.py` 仅剩 `LocatorProjectViewSet` / `LocatorDirectoryViewSet` / `PageFlowViewSet`
- [x] 2.3 `urls.py` 删除 5 条 router 注册（`web-groups` / `web` / `api-groups` / `api-endpoints` / `web-flows`）；验证：`django.urls.resolve` 对 `/api/elements/web/`、`/api/elements/web-groups/`、`/api/elements/api-groups/`、`/api/elements/api-endpoints/`、`/api/elements/web-flows/` 全部抛 `Resolver404`，而 `projects` / `directories` / `flows` 仍命中
- [x] 2.4 `admin.py` 删除 5 处 `@admin.register`；验证：`grep -c "@admin.register"` 与剩余模型数一致
- [x] 2.5 `api.py` 删除 WebElement / WebGroup / WebPageFlow 的读写函数与相关 import；验证：`grep -E "WebElement|WebGroup|WebPageFlow"` 命中 0
- [x] 2.6 `api_projects.py` 删除 web / api 的 `file_count` 分支与树构建分支，叶子 `kind` 只留 `page`；验证：`grep -E "WebElement|ApiEndpoint|web_element|api_endpoint"` 命中 0，且项目树接口仍返回 android 目录与页面
- [x] 2.7 `api_directories.py` 删除 `web_element` / `api_endpoint` 的移动与批量删除分支，`kind` 收敛为 `directory|page`；验证：`grep -E "WebElement|ApiEndpoint|web_element|api_endpoint"` 命中 0，且非法 kind 仍以明确错误拒绝
- [x] 2.8 `python manage.py check` 与 `python manage.py makemigrations --check --dry-run`；验证：均退出码 0
## 2b. 【实施中新增】9.10 复验扫出的 Web/API 专用工具与遗留引用

> 起因：9.10 全仓复验已删标识符时，扫出 4 个此前未登记的 Web/API 专有载体。它们都直接引用已删模型，留着即"跑了必报错的脚本"。

- [x] 2b.1 删除 `tools/seed_web_elements.py`（790 行，唯一用途是创建 WebElement / WebGroup 记录）；验证：文件不存在，全仓无引用
- [x] 2b.2 删除 `tools/seed_api_schemas.py`（537 行，唯一用途是给 ApiEndpoint 回填 schema）；验证：文件不存在，全仓无引用
- [x] 2b.3 外科式清理 `tools/cli.py`（**非**整体删除——它同时承载 case / dir 两个域）：移除 `element` 域的全部子命令、`WebElement`/`WebGroup` import 与 `get_or_create_group`；验证：`def` 列表仅剩 ok/err/case_*/dir_*/main，`grep -E "WebElement|WebGroup|element_list"` 命中 0
- [x] 2b.4 清理 `apps/workflow/semantics.py` 的单域失效分支：`_NODE_TYPE_MAP` 去掉 `ApiNode`、`_element_source` 去掉 `web_snapshot`、`_element_domain` 收敛为恒 `android`（已先查库确认 4 篇文档无任何 `web_` 前缀元素 id，故该分支无生产者、无存量数据）；验证：`grep -E "ApiNode|web_snapshot|web_"` 命中 0；相关单测通过

## 3. dashboard 后端 KPI 收敛

- [x] 3.1 `apps/dashboard/views.py` 删除 `WebElement` / `ApiEndpoint` 的 import 与两个 breakdown 条目；验证：`grep -E "WebElement|ApiEndpoint"` 命中 0，且 KPI 接口返回的 breakdown 不再含 `web` / `api` 两项
- [x] 3.2 `python -m pytest -m "unit or integration"`；验证：退出码 0（本阶段）

## 4. 接口资产目录能力退役

- [x] 4.1 删除 `tools/seed_api_endpoints.py`；验证：文件不存在
- [x] 4.2 `tests/graybox/unit/test_api_path_callers.py` 移除 `catalog` 面：`ENDPOINT_CATALOG` 常量、`_scan_catalog_paths` 收集分支、`MIN_PER_SURFACE["catalog"]` 下限与「四面」表述；同时更新 `tests/AGENTS.md` 中记录该面的两处（本次改动造成的失真文档）；验证：守护内除「说明该面已退役」的注释外无 catalog 残留，面数由四收敛为三
- [x] 4.3 实测 `frontend` 面扫描量 **N = 102**（变更前 111），按 `floor(N*0.95) = 96` 重登记下限。**与计划估算的差异已查清**：计划按「元素定位 8 + workflow 2 + pageCatalog 1 = 11」估算，实测只降 9 —— 因为 `apiGetWebElement` / `apiGetApiEndpoint` 走 `client.get<DjangoResponse<T>>(...)` 泛型签名，而扫描器正则的泛型组 `(?:<[^<>()]*>)?` 匹配不了嵌套 `<>`，这两个调用点**在变更前就未被计入**；被扫到的删除量 = 元素定位 6 + workflow 2 + pageCatalog 1 = 9，与 111→102 吻合。已把该解释写进代码注释。验证：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 全绿
- [x] 4.4 确认与计数无关的扫描器健康守护未被削弱；验证：`test_multiline_call_sites_are_captured` 与 `test_exception_list_entries_are_real` 仍在且通过

## 5. 前端元素定位收敛为单 Android 项目

- [x] 5.1 `element-locator/types.ts`：`LocatorProjectCode` 收敛为 `'android'`、`LocatorFileKind` 收敛为 `'page'`，删除 `WEB_LOCATOR_TYPES` / `API_METHODS` / `WebElementDetail` / `ApiEndpointDetail`，`FILE_KIND_BY_CODE` / `FILE_KIND_LABELS` 收敛；验证：`grep -E "WEB_LOCATOR_TYPES|API_METHODS|WebElementDetail|ApiEndpointDetail|web_element|api_endpoint"` 命中 0
- [x] 5.2 `element-locator/api.ts` 删除 8 个 web/API 封装；验证：`export function` 计数为 10，且 10 个名字全在 `frontend/src` 内有生产消费者
- [x] 5.3 `element-locator/routes.ts` 删除 `/elements/web`、`/elements/api` 两条重定向；验证：`grep "/elements/web|/elements/api"` 命中 0
- [x] 5.4 `composables/useLocatorTree.ts` 的 `addFile` / `removeFile` 收敛为仅处理 `page`，清理已删封装 import；验证：`grep -E "web_element|api_endpoint|apiCreateWebElement|apiCreateApiEndpoint"` 命中 0
- [x] 5.5 `components/LocatorTree.vue`：`createFileLabel` 固定「新建页面」、`fileKindOf` 返回 `page`；验证：三类域标签分支与 `FILE_KIND_BY_CODE` 消费点全部消失
- [x] 5.6 `components/LocatorFilePanel.vue`：删除 Web 表单（`WEB_LOCATOR_TYPES`）与 API 表单（`API_METHODS`）及其 `saveWeb` / `saveApi` / `loadDetail` 分支，`page` 早返回保留；验证：`grep -E "WEB_LOCATOR_TYPES|API_METHODS|saveWeb|saveApi|apiGetWebElement|apiGetApiEndpoint"` 命中 0
- [x] 5.7 `ProjectList.vue` 的副标题与空态文案改为单项目口径（原「三个系统项目：Android 页面、Web 元素、API 接口」）；验证：页面副标题不再出现 Web/API 字样

## 6. workflow 收敛（Web 页面关联 + API 接口关联 + ApiNode）

- [x] 6.1 `workflow/api.ts` 删除 `listWebGroups` / `listWebGroupElements`；验证：`grep -E "/elements/web"` 命中 0
- [x] 6.2 `workflow/data/pageCatalog.ts` 删除 `mapWebGroup`、WebGroup 素材拉取分支、`fetchApiEndpoints` 与 `ApiEndpointRef`；验证：`grep -E "listWebGroup|fetchApiEndpoints|ApiEndpointRef|/elements/api-endpoints"` 命中 0
- [x] 6.3 `components/vueflow/NodeContextMenu.vue` 删除「关联 Web 页面…」与「关联 API 接口…」菜单项、`apiEndpoints` 拉取、`api` 模式的接口选择器；验证：`grep -E "openLink\('web'\)|openApiPicker|apiEndpoints"` 命中 0
- [x] 6.4 `components/vueflow/PageFlowVueFlow.vue` 删除 `handleLinkApi`、`ApiNode` 新建入口与 `store.addApiPort` 调用；验证：`grep -E "handleLinkApi|addApiPort|ApiNode"` 命中 0
- [x] 6.5 `stores/workflowStore.ts` 删除 `linkApiEndpoint` / `addApiPort` 及二者在 `return` 中的暴露；验证：`grep -E "linkApiEndpoint|addApiPort"` 命中 0
- [x] 6.6 删除 `ApiNode` 节点类型：`types/workflow.ts` 的 `WorkflowNodeType` 联合、`registry/nodeRegistry.ts` 注册项、`composables/useVueFlowAdapter.ts` 的 `isApiNode`/`apiMethod`/`apiUrl` 映射、`components/vueflow/PageFlowNode.vue` 的 `isApi` 分支与 API 样式；验证：`grep -w "ApiNode" frontend/src` 命中 0，且 `npm run typecheck` 无新增错误
- [x] 6.7 存量原型降级验证（D6）—— **实测结论：无残留可验**。查库：4 篇文档（`WF-PF-20260908-125346-IMLN` 含 PageNode/StartNode，`WF-PF-20260910-142401-MP9V` 空，`WF-PF-20260910-151245-F98K` 空，`WF-PF-20260910-162309-ALF3` 含 PageNode），**全部不含 `ApiNode`**；唯一可能承载 ApiNode 的 `api_flow` 文档已由 6b.7 删除。故 D6 的「不改写存量数据」由「无数据需改写」取代；优雅降级的静态依据（`applySnapshot` 不做节点类型校验、注册表查询均为可选链）保留在 design D6 备查
## 6b. 【实施中新增，经用户确认】接口流（api_flow）文档类型下线

> 起因：删除 `ApiNode` 时核实到「接口流」画布下 `addPage` / `addPopup` / `addStart` / `addEnd` 全部 early-return，唯一可添加节点就是 `ApiNode` —— ApiNode 一去，接口流即成为无法添加任何节点的空壳类型。经用户确认：一并下线该类型并删除存量 1 篇接口流。

- [x] 6b.1 前端 `workflow/constants.ts`：删除 `NODE_TYPES.API_FLOW`、`FlowDocType` 收窄为 `page_flow`、`FLOW_DOC_TYPES`、`isFlowDocType`、`NODE_TYPE_LABELS` 与 `DEFAULT_NAMES` 中的 API_FLOW 项、`API_FLOW_CREATED`；验证：`grep API_FLOW frontend/src` 命中 0
- [x] 6b.2 前端 `stores/libraryStore.ts`：删除 `createApiFlow` 与按 API_FLOW 分支的默认名/标签逻辑；验证：`grep -E "API_FLOW|createApiFlow" ` 命中 0，页面流创建路径不变
- [x] 6b.3 前端 `index.vue`：删除 `askCreateApiFlow` 与 `@create-api-flow` 绑定；验证：`grep -E "askCreateApiFlow|create-api-flow"` 命中 0
- [x] 6b.4 前端 `components/WorkflowDirTree.vue`：删除 API_FLOW 的图标/类型判定分支；验证：`grep API_FLOW` 命中 0
- [x] 6b.5 前端 `components/vueflow/PageFlowVueFlow.vue`：删除 `isApiFlow` 及其在各 `add*` 中的 early-return 守卫与模板 `v-if="!isApiFlow"`；验证：`grep isApiFlow` 命中 0，且页面流可正常添加 Page/Popup/Start/End 节点
- [x] 6b.6 后端 `apps/workflow/models.py`：删除 `TYPE_API_FLOW`、其 choices 项与 `SUPPORTED_TYPES` 中的对应项；`apps/workflow/api.py`：删除 `TYPE_API_FLOW` 分支；验证：`grep -E "TYPE_API_FLOW|api_flow" apps/` 命中 0
- [x] 6b.7 后端新增迁移：删除存量 `api_flow` 文档（当前 1 篇）；验证：`WorkflowDocument.objects.filter(doc_type="api_flow").count() == 0`，且 4 篇 `page_flow` 不受影响

## 7. dashboard 前端 KPI 收敛

- [x] 7.1 `frontend/src/modules/dashboard/DashboardView.logic.ts` 删除 `'web'` / `'api'` 两个 KPI 定义；验证：`grep -E "'web'|'api'"` 在 KPI 列表中命中 0，且页面 KPI 项与后端 breakdown 一一对应
- [x] 7.2 保留 `web_automation` / `api_testing`（用例类型，非本次范围）；验证：二者仍在 KPI 列表中

## 8. 测试同步

- [x] 8.1 `frontend/tests/element-locator/p0/api.spec.ts` 收敛为 10 个存活封装的用例；验证：`api.ts` 的 10 个导出与用例覆盖名字集合双向差集为空，`npx vitest run tests/element-locator` 输出 10 passed / 0 failed
- [x] 8.2 `tests/graybox/unit/test_element_locator_views_split.py` 删除 `api-groups` / `api-endpoints` 相关断言；验证：pytest 通过，且不再引用已删 ViewSet
- [x] 8.3 `tests/graybox/unit/test_element_locator_group_writes_removed.py` 更新（`WebGroupViewSet` / `ApiGroupViewSet` 已不存在）；验证：pytest 通过
- [x] 8.4 `tests/graybox/unit/test_element_locator_drf_writes.py` 删除 web / api 用例；验证：pytest 通过，`grep -E "WebElement|ApiEndpoint"` 命中 0
- [x] 8.5 `tests/arch/test_view_write_convergence.py` 删除 web / api 条目；验证：pytest 通过

## 9. 门禁与验收

- [x] 9.1 `python manage.py check` + `python manage.py makemigrations --check`；验证：均退出码 0
- [x] 9.2 `ruff check` + `ruff format --check`（相关路径）；验证：退出码 0
- [x] 9.3 `python -m pytest -m "unit or integration"`；验证：退出码 0
- [x] 9.4 `python -m pytest tests/graybox/unit -q`；验证：本变更相关测试全绿（既有 `test_ai_engine_config` 失败与沙箱 `PermissionError` 另行留痕，须证明与本变更无关）
- [x] 9.5 `npm run typecheck`；验证：与 element-locator / workflow / dashboard 相关的 error 为 0，错误集合不新增（变更前的既有 30 个 error 逐条比对）
- [x] 9.6 `npx vite build`（受限沙箱需 `danger-full-access`）；验证：退出码 0
- [x] 9.7 `npm run lint:styles`；验证：退出码 0
- [x] 9.8 `python tools/gen_arch_stats.py --check-boundaries`；验证：退出码 0（跨模块改动关单附加项）
- [x] 9.9 改动面核对：以 mtime 窗口 + 逐文件 `git status` 列出本变更触碰的文件；验证：与 `proposal.md` 的 Impact 段一致，且不含 `tokens.css`、Android 域 `PageFlow` 相关文件
- [x] 9.10 全仓复验已删标识符：`WebElement` / `ApiEndpoint` / `ApiGroup` / `WebGroup` / `WebPageFlow` / `ApiNode` / `seed_api_endpoints` / `apiGetWebElement` 等；验证：`apps/`、`frontend/src/`、`tools/` 命中 0（`openspec/` 历史归档与本次变更工件除外）

## 10. 验收留痕（apply 期实测，供归档核查）

- **3.2 / 9.3 / 9.4**：`7 failed, 324 passed, 79 deselected, 11 errors`（`-m "unit or integration"`）与 `7 failed, 278 passed, 11 errors`（`tests/graybox/unit`）。7 个 failed **全部**在 `test_ai_engine_config.py`，11 个 errors **全部**是沙箱 `PermissionError`（`test_env_loader` / `test_kb_files`）—— 与变更前完全同一集合，**0 个与本变更相关**。
- **9.5 typecheck**：30 个 error，与变更前**同一集合**（`tests/dashboard/*` 27 + `src/modules/case-manager/components/ProjectTree.vue` 3），**0 条**提及 element-locator / workflow / ApiNode / WebElement / ApiEndpoint。故口径为「本变更相关 error = 0 且不新增」。
- **9.7 lint:styles = exit 1，但与本变更无关**：全仓唯一硬失败是 `modules/device-inspector/components/SavedPagePicker.vue:118  999px`。该行**不存在于 HEAD**（`git show HEAD:<file> | Select-String 999px` 无结果），是**并发会话**当前正在改写的 `device-inspector` 文件引入的；本变更改动面（element-locator / workflow / dashboard / tests / tools）内零违规。按「只碰必须碰的」未顺手修。
- **9.9 改动面**：本变更在 git 中确认改动 **44 个文件** + 删除 5 个（`tools/seed_api_endpoints.py`、`seed_web_elements.py`、`seed_api_schemas.py`），并新增 2 个迁移。比 `proposal.md` Impact 段的估算多，原因是实施中经用户确认追加了「接口流（api_flow）类型下线」范围（见 6b 组）。审计期间另发现**并发会话**正改写 `frontend/src/modules/device-inspector/**`、`ai-assistant/index.vue`、`workflow/composables/usePrototypes.ts`、`shared/components/WorkbenchCrumbs.vue` 与新增 `tests/graybox/unit/test_workflow_prototype_envelope.py`（mtime 15:23–15:28），**均不在本变更改动面内**；已确认其新增测试通过、与本变更无冲突。
- **9.10 全仓复验的价值兑现**：该步扫出 4 个此前未登记的 Web/API 专有载体（`tools/seed_web_elements.py`、`tools/seed_api_schemas.py`、`tools/cli.py` 的 element 域、`apps/workflow/semantics.py` 的单域失效分支），已由 2b 组修复。
- **规模下限再登记（4.3 后续）**：`frontend` 面在本变更自身贡献 111→102 之后，因并发会话继续改写而实测降至 88；`tests` 面因本变更改写两个测试 + 并发改动降至 34。二者均已按 apply 当下实测重登记为 83 / 32（并在注释中写明该拆分）。**若并发会话继续删减调用点，该下限仍需再次重登记——这是共享工作区下的协调项，不是本变更的遗留缺陷。**
