## Why

页面流模块整体不再需要（2026-11-17 会话确认）。它占 1 个后端 App、3 张表、约 5k 行前端代码与 6 份专属规格，但三张表实测 **0 行数据**，AI 侧页面流工具（`list_page_flows` / `get_page_flow` / `save_page_flow`）已在此前退役变更中删除，`engines/` 零代码引用，全仓唯一业务消费点只剩仪表盘一张 KPI 卡。继续保留意味着为无人使用的能力维护整套代码、规格与门禁。

## What Changes

- **删除后端 App** `backend/apps/workflow/`（models / api / api_digest / semantics / semantics_paths / serializers / views_api / urls / admin / apps 与 6 个迁移），注销 `INSTALLED_APPS`、`config/urls.py` 路由与 Swagger TAGS 的 workflow 项。**BREAKING**：`/api/workflow/*` 全部端点（prototypes / directories / documents 的 CRUD 与 import / export / move）消失。
- **删除数据**：新增一条 `RunSQL` 迁移 drop 三张表 `wf_prototypes` / `wf_directories` / `wf_documents`（实测 0 行，数据不保留）。沿用 retire-inspector-and-element-locator 的顺序：App 目录仍在时加迁移 → `migrate` → 再删目录与注册。
- **删除前端模块** `frontend/src/modules/workflow/`（21 个文件），拆除接线：`router.ts` 路由、`main.ts` 的 tokens.css 引入、侧栏「页面流」导航项与 MOD_COLORS 映射。**BREAKING**：`/workflow` 与 `/workflow/prototypes/:id` 路由消失；侧栏「数据」分组变为 设备管理 / 串口日志。
- **仪表盘联动**（唯一业务消费点）：删后端 `_workflow_stats()` 与 stats 响应的 `workflow` 键、前端「工作流」KPI 入口卡、`DashboardStats` DTO 字段与 `useDashboardStats` 映射。**BREAKING**：stats 契约变更，前后端必须同批落地。
- **卸载依赖**：`@vue-flow/core` / `background` / `controls` / `minimap` 四个包（全仓唯一消费方即本模块），package-lock 同步。
- **测试同步**：删 `tests/page_flow/`（其中 `test_xpath_text_matches.py` 原拟迁至 `tests/device/unit/`，实施中发现被测方法 `AndroidControl.get_text_matches` 已随 engines 历史重构删除、用例早已失效，经需求方确认一并删除）；删 `frontend/tests/workflow/` 6 个 P0 spec；`pytest.ini` 删 `workflow` marker；arch 契约测试删页面流负向例外（指向已不存在的文件，当前门禁红的原因之一）并重登记前端扫描量下限、删 `/api/workflow` 前缀项；仪表盘 3 个测试文件删 workflow fixture / 断言 / 顶层键。
- **门禁同步**：`utils/gen_arch_stats.py` 删 `wf_` 表前缀登记；`utils/check_openapi_coverage.py` 删 EXCLUDED 的 `/api/workflow/`；`utils/frontend-whitelist.json` 删 5 条 workflow 体积白名单；`openspec/openapi.yaml` 基线**手工删除 workflow 段**（13 条 path + 8 个 schema + tag + doc_type 枚举；不整份重新生成，避免混入工作树中并行改动的 schema 差异）。
- **共享样式死代码清理**：`shared/styles/workbench-theme.css` 的 `.workflow-workbench` 选择器（保留 `.wb-shell`）。**保留** `--c-workflow` 颜色令牌与共享色名映射（共享天蓝色，10+ 处共享组件消费，非模块私有）。
- **规格同步**：6 份页面流专属规格整份退役；15 份共享规格删除页面流要求 / 场景 / 措辞（详见 Capabilities）。
- **文档同步**：README 模块地图、ARCH-平台架构设计、PRD-平台总需求 mermaid、自测与检测指令 marker 列举、frontend/tests 三份规划文档的 workflow 行；`frontend/AGENTS.md` 的 `@vue-flow` 技术栈项与 stores 注释、`tests/AGENTS.md` 模块表（事实性描述同步，非红线条款）。

## 关联文档

无 PRD 需求编号：需求来自 2026-11-17 会话确认——删除页面流模块并同步删除所有代码。删除范围与影响面已经探索并由需求方逐项确认：仪表盘 KPI 联动删除、误放测试迁移保留、遗留 AI 规格只删页面流措辞（整份退役另立单）、与并行改动并行推进（只提交本变更文件）、project-viz 历史快照保留不重新生成。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

**整份退役（6 份，全部 Requirement 移除）**

- `workflow-http-envelope`: 页面流 HTTP 信封与写路由契约整体退役（6 条要求）
- `page-flow-node-cap`: 画布节点数量上限契约整体退役（4 条要求）
- `page-flow-node-placement`: 画布新建节点落点契约整体退役（4 条要求）
- `page-flow-overlay-containment`: 画布光标锚定浮层视口收敛契约整体退役（4 条要求）
- `page-flow-start-node`: 起点节点模式与语义摘要契约整体退役（2 条要求）
- `ai-page-flow-listing`: `list_page_flows` 列表契约整体退役（1 条要求；实现已随 retire-ai-toolbox 删除，规格属遗留，本单正式下线）

**需求级修改（15 份）**

- `ai-device-planner-tools`: 移除 3 条页面流要求（planner 工具子集 / 提示词阅读指引 / 摘要只含页面与节点关系）；保留 log_check 2 条（其实现路径措辞的历史遗留另立单处理）
- `ai-intent-routing`: 移除 `workflow`（工作流工作台）意图类别及其识别场景，视觉模型路由列表去掉 workflow
- `ai-platform-task`: 自动放行工具列表去掉 `create_page_flow` / `save_page_flow`，executor 工具域描述去掉「工作流」
- `ai-engine-protocol`: 工具注入场景的示例「如页面流文档」换为用例文档
- `device-log-read-tool`: 「规划模型不受影响」场景去掉「仍仅为页面流工具」断言，只保留「不含任何日志工具」
- `serial-log-page`: 侧栏位置由「页面流之后」改为「数据分组末尾、设备管理之后」，顺序场景同步
- `platform-load-budget`: 「列表计数一次聚合」收窄为用例项目列表，删除原型列表要求与场景
- `frontend-doodle-sketch-card`: 删除「两处资源列表消费 SketchCard」要求，新增「用例项目列表消费 SketchCard」（页面流原型列表随模块删除）
- `frontend-doodle-kpi-card`: entry 变体示例场景由「仪表盘工作流卡」换为「在线设备卡」
- `frontend-doodle-subpage-nav`: 单页模块枚举与模版范围注记去掉页面流
- `frontend-l5-overlay`: 删除 4 个 workflow 画布覆盖层场景；删除确认场景换为用例管理目录树（ElMessageBox 实证存在）；右键菜单场景去掉画布节点 / 连线措辞
- `frontend-l2-page-region`: 4 条要求去掉 `/workflow` 示例路由与 `.workflow-workbench` 等价锚点；共享骨架要求删除画布例外条款与场景
- `frontend-l3-container`: 退役「画布类页面登记例外」要求（唯一例外即页面流画布）；2 个场景去掉 `/workflow`
- `frontend-l3-content-block`: 主题作用域措辞去掉 `.workflow-workbench` 等价锚点
- `frontend-l0-design-tokens`: 图表色表场景去掉 workflow 节点色表举例；「共享皮肤不依赖模块作用域令牌」去掉 `.workflow-workbench` 措辞与 `modules/workflow/tokens.css` 场景

## Impact

- **后端**：`backend/apps/workflow/`（删除）、`backend/apps/dashboard/views.py`、`backend/config/settings.py`、`backend/config/urls.py`；新增一条删表迁移。
- **前端**：`frontend/src/modules/workflow/`（删除）、`router.ts`、`main.ts`、`shared/components/sidebarNavConfig.ts`、`shared/styles/workbench-theme.css`、`shared/types/dashboard.ts`、`modules/dashboard/`（index.vue / useDashboardStats.ts）、`package.json` / `package-lock.json`。
- **测试**：`tests/page_flow/`（删除，1 个文件迁移）、`tests/pytest.ini`、`tests/AGENTS.md`、`tests/arch/unit/test_api_path_callers.py`、`tests/arch/unit/test_channels.py`、`tests/dashboard/unit/test_dashboard_load_budget.py`、`frontend/tests/workflow/`（删除）、`frontend/tests/dashboard/` 2 个 spec、`frontend/tests/` 3 份规划文档。
- **门禁 / 工具**：`utils/gen_arch_stats.py`、`utils/check_openapi_coverage.py`、`utils/frontend-whitelist.json`、`openspec/openapi.yaml`。
- **文档**：`README.md`、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`dev_docs/ARCH_PRD/PRD-平台总需求.md`、`backend/apps/自测与检测指令.md`、`frontend/AGENTS.md`（事实性描述）。
- **Non-Goals（明确不动）**：
  - `engines/ae_harness/workflow/`、`engines/backend_bridge/workflow/`（SOP 编排，同名不同物）；ai_assistant 的 `AISopWorkflow` / `sop-workflows` API / 前端 SOP 组件与测试；`shared/types/ai.ts` 的 `workflow_id` / `workflow_name`。
  - `--c-workflow` 颜色令牌、AppCard 色名映射、sketchCard cycle 色板、motion.css、git-branch 图标注册（共享资产）。
  - 历史迁移（ai_assistant 0038 / 0041 / 0046 等含页面流字样，迁移历史不可改写）与 `openspec/changes/archive/**`。
  - 遗留 AI 规格（ai-intent-routing / ai-platform-task / ai-device-planner-tools 的 log_check 部分 / device-log-read-tool 的工具箱措辞）的**整份退役**——本单只删页面流措辞，整份退役另立单。
  - `dev_docs/project-viz/` 生成看板数据：保留历史快照，不重新生成。
  - arch 门禁中 11 条与页面流无关的路由解析失败（工作树并行改动造成）：本单不修，CI 全绿需待并行改动收口。
  - 并行变更 `queue-workflow-tasks` / `bug-table-identity-and-noshadow` 的任何文件。
