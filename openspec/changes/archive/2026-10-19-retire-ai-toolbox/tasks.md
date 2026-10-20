## 1. 侧栏与页面入口

- [x] 1.1 `sidebarNavConfig.ts`：`AI 助手` 改为无 children 的普通项（`path: "/ai-assistant"`），删除「平台小助手」「AI工具箱」两子项与 `/ai-assistant/toolbox` 颜色映射；验证：侧栏渲染为单一入口，点击直达 `/ai-assistant/agents`（`/ai-assistant` 已有 redirect）
- [x] 1.2 `modules/ai-assistant/index.vue`：删除 `viewMode` / `VIEW_BY_PATH` / `VIEW_META` / `ToolboxPanel`，页头固定为「平台小助手」；验证：`npm run build` 通过
- [x] 1.3 `index.logic.ts` 与 `constants.ts`：删除 `viewMode` 与 `skillViewerRoute` / `toolDebugRoute`；验证：全仓 grep 这些名字零命中
- [x] 1.4 `routes.ts`：删除 `/ai-assistant/toolbox`、`/ai-assistant/toolbox/skills/:skillName`、`/ai-assistant/toolbox/tools/:toolName` 三条路由；验证：访问这些路径不渲染任何页面（走 404 兜底）

## 2. 前端工具箱文件

- [x] 2.1 删除页面与组件：`ToolboxPanel.vue`、`ToolboxPanel.style.css`、`SkillViewerPage.vue`、`SkillViewerPage.style.css`、`ToolDebugPage.vue`、`ToolDebugPage.style.css`；验证：文件不存在，全仓 grep 组件名零命中
- [x] 2.2 删除组合式与纯函数：`useToolbox.ts`、`useToolboxAssembly.ts`、`usePlatformConfig.ts`、`usePlatformTools.ts`、`useToolDebug.ts`、`useSkillViewer.ts`、`helpers/toolbox-assembly.ts`、`helpers/tool-debug-label.ts`、`helpers/skill-markdown.ts`、`api/toolbox.ts`；验证：全仓 grep 这些模块名零命中
- [x] 2.3 删除守护工具箱的 6 个前端测试（`ToolboxPanel-tool-debug`、`ToolboxPanel-sources`、`toolbox-assembly-sources`、`ToolDebugPage-device-options`、`useToolbox`、`useToolDebug`）；验证：`npm run test` 无模块解析失败
- [x] 2.4 `shared/types/ai.ts`：删除 `ViewMode` 与 `ToolboxListResponse`；验证：`npm run build` 通过

## 3. 后端端点与视图

- [x] 3.1 删除 `views_toolbox_drf.py`、`views_tool_debug_drf.py`、`views/tool_gateway.py`、`views/__init__.py`（整个 views 包）；验证：`python manage.py check` 通过
- [x] 3.2 `urls.py`：删除 toolbox 路由注册、`platform-tools/*`、`platform-config/*`、`available-tools/`、legacy `tools/*` 路径与相关 import；验证：`python manage.py check` 通过，`GET /api/ai/toolbox/` 等返回 404
- [x] 3.3 `views_drf.py`：删除 `AvailableToolsAPIView`、`PlatformToolToggleAPIView`、`PlatformConfigAPIView` 及 docstring 中的旧路径；验证：`ruff check apps/ai_assistant` 通过

## 4. 后端数据与模块

- [x] 4.1 `api.py`：删除平台配置、平台工具开关、共享工具箱相关的 10 个函数与 `__all__` 条目；验证：全仓 grep 这些函数名零代码命中
- [x] 4.2 删除 `apps/ai_assistant/tools.py` 与 `skills_catalog.py`；验证：全仓 grep `apps.ai_assistant.tools` / `skills_catalog` 零命中
- [x] 4.3 `models.py`：删除 `AISharedTool`、`AIPlatformTool`，以及 `AIAgent.skills_config` 与 4 个 `enable_*` 字段；`serializers.py` 与 `api.create_agent/update_agent` 同步移除；验证：`python manage.py check` 通过
- [x] 4.4 生成迁移 `0055_retire_ai_toolbox`；验证：`python manage.py makemigrations --check --dry-run` 输出 `No changes detected`，迁移含两表删除与五个字段删除

## 5. 网关与配置

- [x] 5.1 删除 `gateway/internal_token.py`，并从 `MIDDLEWARE` 去掉其注册；验证：`python manage.py check` 通过，全仓 grep `InternalToolTokenMiddleware` 零命中
- [x] 5.2 `gateway/middleware.py` 的 `PUBLIC_PREFIXES` 去掉 `/api/ai/tools/` 且更新注释；验证：全仓 grep `"/api/ai/tools/"` 零命中
- [x] 5.3 `config/settings.py` 删除 `AI_TOOL_GATEWAY_TOKEN` 与相关注释，`.env.example` 同步删除；验证：全仓 grep `AI_TOOL_GATEWAY_TOKEN` 零命中

## 6. 文档与门禁

- [x] 6.1 接口文档：`dev_docs/DEV_TEST` 整棵目录已被并行重构删除（含 `API-AI助手.md`），无文件可改；验证：`dev_docs` 全目录 grep `toolbox|platform-tools|available-tools|platform-config` 零命中
- [x] 6.2 `frontend/src/modules/ai-assistant/AGENTS.md`：删除装配台段落，入口改为单一入口并标注工具箱已下线；验证：文档不再出现「装配台」与 `/ai-assistant/toolbox` 操作描述
- [x] 6.3 门禁：`python manage.py check`、`makemigrations --check`、`ruff check/format`、`pytest tests/arch -q`（24 passed）、`gen_arch_stats --check-boundaries` 全绿
- [x] 6.4 前端：`npm run build` 通过；`npm run typecheck` 仅剩既有 `useTaskPublish` 测试漂移（`ATTACH_ACCEPT`，与本单无关）；`npm run test` 为 413 passed / 4 failed，4 条均落在既有任务发布测试
