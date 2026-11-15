## Why

`engines/agents` 一个包同时承担了六件事：角色装配、模型工厂、事件落库、计费、语音会话、RAG 与用例编写/YAML 校验，88 个文件 14106 行，不是「Model + Harness」的单一职责。平台侧已在 `engines/backend_bridge` + `engines/ae_harness` 建起新链路（平台对话卡、计费副本、SOP 装配均已迁移），但旧包仍被 5 个后端 app 的 22 处 import 与 `engines/device` 的反向依赖绑住，两套实现并行维护，向量库（`rag/store.py` 与 `knowledge/store.py` 均声明 `SQLiteVectorStore`）与 adb 工具已出现整段克隆。继续放任会出现第三份实现，现在收口。

## What Changes

- **BREAKING** 删除 `engines/agents` 整包（88 文件 / 14106 行）：`config/`、`models/`、`assistant/`、`agent_builders.py`、`role_sys_prompts.py`、`tools/`、`tools_config.py`、`middleware/`、`messaging/`、`event_log.py`、`event_sink.py`、`workflow/`、`rag/`、`knowledge_chat/`、`realtime_vocie/`。
- 平台任务执行链改由 `engines/backend_bridge/workflow/sop_ui.py` 提供；步骤一律来自 `engines/ae_harness/workflow/sop/steps/*.yaml`；`task_list` 不再 import 旧包。
- **BREAKING** 任务清单不再有「任务详情」：一行任务跑完直接产出一份 HTML 报告（落 `engines/backend_bridge/reports/paths.py` 的 `REPORT_ROOT`），页面从任务列表直接跳到该报告。原有的任务详情报告（轮次 / 用例分解 / 事件面板）停止提供。
- **BREAKING** 任务事件落库链路随旧包一起退役：不再写 `task_events` / 事件缩略图；`EventRecord`、事件折叠与 `TaskEventSink` 不再被任务执行使用。用量与费用仍写既有账本，口径不变。
- 平台 SOP 补齐取消能力（原 `workflow/platform_run.request_cancel`），基于 `ae_harness` 的 `CancelToken` / `CancelMiddleware`。
- **BREAKING** 知识助手整体下线：`backend/apps/knowledge_assistant`、前端 `modules/knowledge-assistant`（含麦克风采集与音频播放）、路由 `/knowledge-assistant`、侧栏「知识库助手」入口、语音与文字问答引擎实现一并退役。知识库只保留 `engines/ae_harness/knowledge/` 的只读检索原语。
- **BREAKING** 用例 YAML 模型下线：`workflow/case_file.py`、`case_goal_workflow.py`、`case_artifact*.py`、`step_brief.py` 删除；`case_manager` 与 `task_list` 的 YAML 导入/校验入口下线，用例步骤改走 SOP steps YAML。
- **BREAKING** 角色配置统一到 `ae_harness` 的 `models.yaml` + `prompts/*.md`；四分段（ModelConfig / RoleConfig / ToolsConfig / ReactConfig）、`role_loader.py`、`agent_config.yaml` 下线。
- `config/data/app_info/`（应用短卡）与 `config/data/log_keywords/`（型号日志关键词）迁入 `ae_harness`，保留执行者提示词的应用上下文与验收者的日志证据能力。
- `engines/device` 不再依赖 `agents.event_log`，改经 `utils.logs`。
- 文档与规格落点同步：`engines/AGENTS.md` 一级子包删 `agents/`，依赖边界收敛为 `backend → backend_bridge → ae_harness` 单向；`engines/backend_bridge/AGENTS.md` 承接事件落库与取消。

## 关联文档

无关联 PRD 编号。原因：本次是架构收敛与能力下线，需求来源为需求方在本次会话给出的四项明确决定——文字问答会话去掉、语音与实时语音去掉、模型与角色配置不迁移（知识库改采 `ae_harness` 中的）、用例 YAML 模型去掉。

约束依据：根 `AGENTS.md`「平台架构定位」与 `engines/AGENTS.md`。本次触及 `engines/AGENTS.md` 的一级子包清单、依赖边界与红线条目，按根 `AGENTS.md` 行为规范 4，变更申请四要素写在 `design.md` 第 1 节，需需求方确认后才可动代码。

## Capabilities

### New Capabilities

- `engines-agents-retirement`: 约定 `engines/agents` 整包下线后的边界——平台只有一条 Agent 落点（`backend_bridge`）、原语只有一份（`ae_harness`）、设备引擎不得反向依赖 Agent 包、下线能力的残留检查口径。

### Modified Capabilities

- `agent-harness`: 「角色经 AgentRoleFactory 装配」「提示词唯一配置入口」「模型配置唯一装载入口」「工具唯一分配入口」「Harness 四分段留在配置层」等需求的落点从 `engines/agents` 改为 `ae_harness` 原语；「engines 零 Django / apps 依赖」保持不变并新增对 `engines/device` 反向依赖的约束。
- `backend-bridge-agent`: 新增「平台任务事件落库归本包」与「平台运行可取消」两条需求；原有「平台角色只经 ae_harness 原语装配」不变。
- `knowledge-assistant-voice`: 全部需求 REMOVED——语音问答能力整体下线。
- `knowledge-assistant-text-chat`: 全部需求 REMOVED——文字问答能力整体下线。
- `appliance-case-authoring`: 全部需求 REMOVED——用例编写流水线依赖用例 YAML 产物格式，随 YAML 模型下线。

## Impact

- 引擎：删除 `engines/agents/`（88 文件 / 14106 行）与 6 类配置资产（`app_info`、`log_keywords`、`prompts`、`models.yaml`、`knowledge_bases.yaml`、`skills`）。
- 引擎扩写：`engines/backend_bridge/` 从 15 文件 / 1007 行增至约 25 文件 / 2500 行（新增事件落库、折叠、取消、用例模型或下线确认）。
- 后端：`backend/apps/task_list/{task_runner,api,event_store,attachments,task_reports}.py`、`backend/apps/case_manager/{api_yaml,api_definitions}.py`、`backend/apps/ai_assistant/views_drf.py`、`backend/config/settings.py` 注释。
- 后端下线：`backend/apps/knowledge_assistant/`（8 文件）、`backend/apps/case_manager` 的 YAML 导入/导出入口、`task_list` 的 YAML 附件与用例标题入口。
- 前端：删除 `frontend/src/modules/knowledge-assistant/`（17 文件）、`router.ts` 与 `shared/components/sidebarNavConfig.ts` 中的路由与侧栏项；用例库页面的 YAML 导入/导出控件。
- 依赖方向：`backend → backend_bridge → ae_harness` 单向；`engines/device`、`engines/vision` 对 `engines/agents` 的引用清零。
- 测试：68 个引用 `engines.agents` 的测试文件需改落点或随能力删除；新增 `tests/engines/backend_bridge/` 事件落库与取消用例。
- 附带清理：`utils/check_gates.py` 的 `VENDORED` 失效路径、`.agents/skills/{engines-agents-style-check,engines-docstring-check}` 的 `skill-creator` 跳过路径、`dev_docs/project-viz/tools/gen_board_data.py` 的 agents 采集、`dev_docs/ARCH_PRD/ARCH-Engines架构.md` 目录描述。
- 未决（不阻塞立单，阻塞 B3 实施）：`case_manager` 用例库在 YAML 通道下线后的数据来源，见 `design.md` 第 6 节决策点。
