## Why

AI 工具箱（装配台）已只剩「平台业务工具 / 自定义 Skill」两个来源，而 SOP 的工具集由 `engines/agents/tools_config.py` 固定装配，装配台的开关从未影响过任务执行；它同时是平台侧工具调试与 `/api/ai/tools/*` 内部网关的唯一消费面。产品决定删除工具箱，侧栏只保留单一「AI 助手」入口，点击即直达平台小助手页。

## What Changes

- **BREAKING** 侧栏：`AI 助手` 变为直达 `/ai-assistant/agents` 的单一入口，移除「平台小助手」「AI工具箱」两个子项。
- **BREAKING** 前端删除工具箱视图、Skill 查看页、工具调试页与全部支撑文件（16 个）及 3 条路由；`viewMode` 状态与工具箱 DTO 一并移除。
- **BREAKING** 后端删除 `/api/ai/toolbox/*`、`/api/ai/platform-tools/*`、`/api/ai/platform-config/*`、`/api/ai/available-tools/`。
- **BREAKING** 删除内部工具网关 `/api/ai/tools/*`：`gateway/internal_token.py`、其 MIDDLEWARE 注册、`AI_TOOL_GATEWAY_TOKEN` 配置与 JWT 豁免前缀。
- **BREAKING** 删除 `ai_shared_tools`、`ai_platform_tools` 两张表，以及 `AIAgent.skills_config` 与 `enable_workspace_tools` / `enable_business_tools` / `enable_mcp_tools` / `enable_skills` 四个字段（一次迁移）。
- 删除 `apps/ai_assistant/tools.py` 与 `skills_catalog.py`：平台侧工具函数（含 OCR、页面流查询、包名发现）原先只经工具箱调试页与内部网关注入，两者同时下线后无任何消费方；SOP 执行/验收使用 `engines/agents` 自带工具，不依赖本模块。
- 文档同步：AI 助手接口文档摘除工具箱 / 平台工具 / 网关章节，模块 AGENTS 去掉装配台描述。

## 关联文档

产品口头决策「删除 AI 工具箱、侧栏只留单一 AI 助手入口」，无对应 PRD 编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-platform-tool-debug`: 整个能力下架（8 条需求全部移除）。
- `ai-shared-skill-upload`: 整个能力下架（4 条需求全部移除）。
- `ai-page-flow-listing`: 整个能力下架（`list_page_flows` 随平台工具删除）。
- `ai-screen-vision`: 移除 OCR 相关 3 条需求（工具随平台工具删除）；截图两条保留（引擎自带 `screenshot_page`）。
- `ai-device-action`: 移除「包名发现」与「平台侧设备工具保持不变」两条（平台侧工具已不存在）。
- `sop-task-run`: 改写工具装配口径——不再有装配台可影响工具集。
- `evaluator-retirement`: 侧栏不变式改为「AI 助手只有一个入口，无子项」。
- `frontend-doodle-subpage-nav`: 导航模版去掉「侧栏子项」一类，AI 助手不再有子路由切换。
- `ai-assistant/workbench-header-copy`: 页头口径收窄为只剩智能体看板；已下线路由不再渲染页头。
- `admin-managed-shared-agent`: 智能体可写能力去掉「导入工具箱项」。
- `ai-executor-output`: 「平台不再提供单角色调试对话」的核对面从工具箱改为平台入口。

## Impact

- 前端：`shared/components/sidebarNavConfig.ts`、`shared/types/ai.ts`、`modules/ai-assistant/{routes.ts,index.vue,index.logic.ts,constants.ts}` 与 16 个工具箱文件。
- 后端：`apps/ai_assistant/{urls.py,views_drf.py,api.py,models.py,serializers.py,views_toolbox_drf.py,views_tool_debug_drf.py,skills_catalog.py,tools.py,views/tool_gateway.py,views/__init__.py}`、`gateway/{middleware.py,internal_token.py}`、`config/settings.py`。
- 数据：两张表 + 五个字段物理删除，**不可逆**。
- 配置：`AI_TOOL_GATEWAY_TOKEN` 从 settings 与 `.env.example` 移除。
- 文档：`dev_docs/DEV_TEST/接口文档/API-AI助手.md`、`frontend/src/modules/ai-assistant/AGENTS.md`。
- 测试与门禁：`manage.py check`、`makemigrations --check`、`ruff`、`pytest tests/arch`、`gen_arch_stats --check-boundaries`、`npm run build`。
