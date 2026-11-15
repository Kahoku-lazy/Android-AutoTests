## 1. 规则与门禁先行（B0）

- [x] 1.1 改 `engines/AGENTS.md`：一级子包删 `agents/`，依赖边界写明 `backend → backend_bridge → ae_harness` 单向，删除以 `agents/` 为落点的红线条目（工具命名、`tools_config` 分配、`role_sys_prompts` 提示词入口、`AgentRoleFactory` / `agent_builders` 装配）。验证：`git diff -- engines/AGENTS.md` 人工核对四条红线不再指向已删目录
- [x] 1.2 改 `engines/backend_bridge/AGENTS.md`：定位补「事件落库、运行取消、报告与用量」；改掉「`workflow/` 待建」的过期描述。验证：`git diff -- engines/backend_bridge/AGENTS.md`
- [x] 1.3 改 `engines/ae_harness/AGENTS.md`：目录结构补 `agents/config/app_info/` 与 `log_keywords/`；删「无任何代码 import 本包」的过期陈述。验证：`git diff -- engines/ae_harness/AGENTS.md`
- [x] 1.4 在 `utils/check_gates.py` 加退役检查：全仓无 `engines.agents` 导入、`backend/apps` 无 `knowledge_assistant` 路由。检查按「允许清单递减」加入，当前状态下必须全绿。验证：`python -m utils.check_gates --only engines-agents-style` 与 `python run.py check` 均通过

## 2. 解反向依赖

- [x] 2.1 `engines/device/android/recent_apps.py` 的 `from engines.agents.event_log import write_line` 改为 `utils.logs.agent_event_log`。验证：`python -m pytest -c tests/pytest.ini tests/device -q` 通过，且 `grep -rn "engines.agents" engines/device` 无输出
- [x] 2.2 全仓扫描 `engines/vision`、`engines/uart_log` 是否仍引用 `engines.agents`（当前仅 docstring 提及），把 docstring 里的「调用方为 `engines.agents.tools.tool_ocr`」改为 `engines/ae_harness/tools` 或删除。验证：`grep -rn "engines.agents" engines/vision engines/uart_log` 仅剩无害注释或为空

## 3. 下线知识助手（B1）

- [x] 3.1 删 `backend/apps/knowledge_assistant/` 整个 app，并从 `backend/config/settings.py` 的 `INSTALLED_APPS`、根 `urls` 与 ASGI 路由中移除引用。验证：`python -c "import django; django.setup()"`（在 backend 环境下）无导入错误，`python run.py check` 通过
- [x] 3.2 删前端 `frontend/src/modules/knowledge-assistant/`（17 文件），移除 `router.ts` 的导入与路由、`shared/components/sidebarNavConfig.ts` 的侧栏项与图标映射。验证：`cd frontend; pnpm run type-check` 与 `pnpm run build` 通过，侧栏「AI 功能」分组只剩「AI 助手」
- [x] 3.3 删 `engines/agents/knowledge_chat/`、`realtime_vocie/`、`realtime_vocie_agent.py`、`workflow/voice/`。验证：`grep -rn "knowledge_chat\|realtime_vocie\|workflow.voice" engines backend` 无输出
- [x] 3.4 删 `engines/agents/rag/`，保留 `engines/ae_harness/knowledge/`；用源文档重建一次索引后删除 `data/rag_index/`。验证：`python -m engines.ae_harness.knowledge retrieve product_manuals "指示灯"` 返回命中，`git status` 不含索引文件
- [x] 3.5 删 `openspec/specs/knowledge-assistant-voice/`、`openspec/specs/knowledge-assistant-text-chat/` 与 `tests/knowledge/` 目录。验证：`python -m pytest -c tests/pytest.ini tests/knowledge` 报目录不存在属预期，`openspec list` 正常
- [x] 3.6 清理 `engines/agents/config/data/knowledge_bases.yaml` 与 `KNOWLEDGE_CHAT_PROMPT.md` 的残留引用。验证：`grep -rn "KNOWLEDGE_CHAT_PROMPT\|knowledge_bases" engines backend` 无输出

## 4. 平台任务链切换（B2）

- [x] 4.1 在 `engines/backend_bridge/workflow/` 新增取消模块：按 `task_id` 登记 `CancelToken`，提供 `request_cancel` / `bind_cancel` / `clear_cancel`，并由 `run_sop_once` 把 `CancelMiddleware` 挂进 `controls`。验证：新增 `tests/engines/backend_bridge/unit/test_sop_cancel.py` 全绿
- [x] 4.2 `backend/apps/task_list/task_runner.py` 改调 `backend_bridge.workflow.sop_ui.run_sop_once`：把报告定位（run 目录 + 文件名）写进任务结果，按运行结论映射任务终态，删掉对 `platform_run`、`event_sink`、`messaging.record` 的导入。验证：`python -m pytest -c tests/pytest.ini tests/task -q` 全绿
- [x] 4.3 `backend/apps/task_list/{api,event_store}.py`：取消改调新入口；任务执行不再绑定 sink、不再写事件明细行。验证：`python -m pytest -c tests/pytest.ini tests/task/api/test_task_cancel_dispatch.py -q` 全绿
- [x] 4.4 下线任务详情报告接口：移除 `/api/tasks/{id}/report/` 与其视图/序列化/契约，删除对应前端任务详情页。验证：`cd frontend; pnpm run typecheck` 通过，OpenAPI 基线重生成后 `openapi-schema` 门禁通过
  - 后端（已查证）：删 `views.py` 的 `TaskReportAPIView`（HEAD 第 296–338 行，**勿连带切掉 339–393 的 `TaskMediaAPIView` / `TaskDrainAPIView`**，此前切多导致排空接口 405）；删 `_report_body`（29–41）与 `_REPORT_CACHE_TTL` / `_REPORT_TERMINAL_STATUSES`（24–26）；删 `urls.py` 的 `report/` 路由；重生成 `openspec/openapi.yaml`；删测试 `tests/report/integration/test_report_envelope.py`、`tests/task/api/test_task_report_{cancelled,durations,interrupt}.py`、`tests/task/api/test_task_case_authoring.py`、`tests/engines/agents/unit/test_sop_event_stream.py`，并去掉 `tests/arch/unit/test_api_path_callers.py` 里指向 `test_report_envelope.py` 的例外条目
  - 前端（已查证）：删 `/tasks/:id` 路由与 `TaskDetailPage.vue`(404 行)；删详情专用 `components/{CaseStepList,RoundProcess,StepLogCheck,StepLogEvidence,TaskAttemptCard}.vue`(含 .style.css)、`composables/useReportPoll.ts`、`helpers/report-steps.ts`；**保留** `helpers/task-detail.ts`（`TaskBoard.vue:20` 仍在用 `formatTaskCost` / `formatTaskDuration`）；删 `api/tasks.ts` 的 `fetchTaskReport`
- [x] 4.5 前端任务清单改为直达报告：行点击打开 `backend_bridge` 的报告（走既有报告读取接口），不再进详情页。验证：`cd frontend; pnpm run typecheck && npx vitest run tests/task-list` 通过
  - 接线（已查证）：`TaskBoard.vue:117` 现为 `router.push(taskDetailRoute(taskId))`，改为在任务结果带 `report_run` / `report_name` 时打开 `/api/ai/agent-reports/<run>/<name>/`；需让任务列表序列化带出这两个字段（从 `Task.result` 的 JSON 派生，不新增表字段）
- [x] 4.6 合并提示词：执行者取 `ae_harness` 版为基线，验收者取 `agents` 版为基线，写入 `engines/ae_harness/agents/config/prompts/`，并在本任务勾选处记录差异比对结论。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness -q` 全绿
  - 比对结论：`UI_EXECUTOR_PROMPT.md` 保留 harness 版（9945 B，含锚点与工具说明，比 agents 版 6042 B 新）；`UI_VERIFIER_PROMPT.md` 改用 agents 版（4793 B / 2061 字，判据更厚），覆盖 harness 原 3835 B 版；`CASE_WRITER` / `CASE_VERIFIER` 两份完全一致，随用例编写流水线在 B3 一起删除
- [x] 4.7 迁 `app_info/` 与 `log_keywords/` 到 `engines/ae_harness/agents/config/`，并在 `ae_harness` 增加按 token 读取短卡与按机型读取关键词的读取口。验证：新增单测覆盖「短卡命中 / token 缺失报错 / 关键词按机型命中」，全绿
  - 实际范围：`app_info/` 目录在 Govee 业务资产清理后**已无文件**，随包删除、不迁移；只迁 `log_keywords/H6810.md`，读取口 `agents/config.py:load_log_keywords`（型号白名单 + 缺失降级为空串），单测 `tests/engines/ae_harness/unit/test_agents_config.py`
- [x] 4.8a 真机跑通「执行 + 验收」全链路（设备 RF8N21MSW7A）：`python manage.py run_ui_sop "回到桌面"` → phase=completed，两步各 1 次尝试即通过；报告 `logs/agents/backend_bridge/20261115_184315/20261115_184315_sop_ui.html`（1.06 MB）+ jsonl（272 KB）；用量 input 81499 / output 1716 / cache_hit 70016，入账 12 条（execution_id=20261115_184315）
- [x] 4.8b 平台任务链路真机验证：提交一条真实任务，确认 `Task.status` / `cost_*` / `result.report_run+report_name` 三处正确，且任务列表「报告」按钮能打开该报告。验证：任务详情接口返回的 `report_run`/`report_name` 与磁盘报告一致 —— **实测**：任务 209（agent 617 / RF8N21MSW7A）70.1 s 完成，`status=completed`，`cost_total=0.02157444`，token 94209/2194/83072，`report_run=20261115_184602`、`report_name=20261115_184602_sop_ui.html`、磁盘文件存在；列表行 `serialize_agent_task_row` 同时带出 `report_run`/`report_name`/`deepseek_cost=0.02157444`

## 5. 用例 YAML 通道下线（B3，需先过决策点）

- [x] 5.1 **决策点（阻塞后续）**：与需求方确认 `case_manager` 用例库在 YAML 通道下线后的数据来源（只读历史 / 改录 SOP steps / 在 `backend_bridge` 重建用例模型），把结论写进 `design.md` 的 Open Questions。验证：`design.md` 该条标记为已决，且 5.2 起按结论执行
- [ ] 5.2 删 `engines/agents/workflow/{case_file,case_goal_workflow,case_artifact,case_artifact_facts,case_artifact_render,step_brief}.py`。验证：`grep -rn "case_file\|case_goal_workflow\|case_artifact\|step_brief" engines backend` 无输出
- [x] 5.3a 把 `api_definitions._normalize_steps` 对 `parse_step_hints` 的依赖换成后端自带的 `_parse_step_hints`（anchor 必须是对象；log 固定 sku/port/keywords，单关键词收敛成列表，port 非整数报错）。验证：`python -m pytest -c tests/pytest.ini tests/case -q` → 141 passed（4 个失败为既有，已确认 HEAD 上同样失败）
- [x] 5.3b1 下线「YAML 导入用例库」：删 `api_yaml.py`(347 行) + `api.py` 三处再导出 + `views_drf.import_yaml` 视图与 `import-yaml/` 路由 + `management/commands/import_case_yaml.py` + 前端 `ImportYamlDialog.vue` 与 `ProjectWorkspace` 的导入按钮/处理函数 + `api.ts` 的 `importYaml`/`YamlImportResult`；后端同时删掉 `_platform_case_config`（改用例执行靠导出 YAML，已随通道下线）。验证：`django check` 通过、`pnpm typecheck` 通过、OpenAPI 基线重生成后两个门禁绿、`tests/task + tests/case` 211 passed（4 个既有失败）
- [ ] 5.3b2 前端任务发布弹窗移除「选用例执行」入口（`task-list/components/PlatformCasePicker.vue` 与 `CASE_SOURCE_*` 常量、`usePlatformCases`），后端已不再读取 `case_ids`。验证：`pnpm typecheck` + `vitest tests/task-list` 通过，发布弹窗无平台用例选择
- [ ] 5.3c 删 `engines/agents/workflow/case_file.py`，并把 `task_list/{attachments,task_reports}.py` 两处 `validate_platform_yaml` 调用一并处理
  - **执行顺序陷阱（已查证，勿按字面整文件删）**：`api_definitions.py`(335 行) 是**用例定义 CRUD**（create/get/update/delete + 枚举与必填校验），只有 `_normalize_steps`(110–127) 内部调用 `parse_step_hints`；整文件删除会连带打掉用例库。正确做法：把 `_normalize_steps` 里的 `parse_step_hints` 换成后端本地可选字段校验（anchor / log / reason），其余函数全部保留。`api_yaml.py`(347 行) 才是 YAML 导入/导出模块，连同路由与前端控件整体删除。
  - 允许顺序：先删 `api_yaml.py` + 路由 + 前端导入导出控件（自成一体）→ 再改 `api_definitions._normalize_steps` → 最后才删 `engines/agents/workflow/case_file.py`。
- [ ] 5.4 删 `backend/apps/task_list/{attachments,task_reports}.py` 的 `validate_platform_yaml` 调用与 `task_runner.py:254` 的用例编写入口。验证：`python -m pytest -c tests/pytest.ini tests/task -q` 全绿
- [ ] 5.5 删 `openspec/specs/appliance-case-authoring/` 与 `openspec/specs/case-manager-yaml-sync/`（按 5.1 结论确认后者范围），删对应 `tests/case/` 用例。验证：`openspec validate --all` 通过

## 6. 整包删除与文档收尾（B4）

- [ ] 6.1 删 `engines/agents` 余下全部内容（`config/`、`models/`、`assistant/`、`agent_builders.py`、`role_sys_prompts.py`、`tools/`、`tools_config.py`、`middleware/`、`messaging/`、`event_log.py`、`event_sink.py`、`workflow/`、`AGENTS.md`）与 6 类配置资产。验证：`git rm -r engines/agents` 后 `grep -rn "engines.agents" . --include=*.py` 无输出
- [ ] 6.2 退役门禁转为强制：`engines/agents` 目录必须不存在，`engines.agents` 导入出现即失败。验证：`python run.py check` 全绿；临时造一条 `import engines.agents` 应使检查失败（验证后删除）
- [ ] 6.3 清理 `utils/check_gates.py:160` 的失效 `VENDORED` 路径与 `.agents/skills/{engines-agents-style-check,engines-docstring-check}` 中 `skill-creator` 的跳过路径。验证：`python -m utils.check_gates` 通过，`grep -rn "engines/agents" .agents/skills utils` 无输出
- [ ] 6.4 更新 `dev_docs/project-viz/tools/gen_board_data.py` 的采集范围（去掉 `engines/agents`）与 `dev_docs/ARCH_PRD/ARCH-Engines架构.md` 的目录描述。验证：`python dev_docs/project-viz/tools/gen_board_data.py` 可运行并生成看板数据
- [ ] 6.5 处理 68 个引用 `engines.agents` 的测试文件：改落点到 `backend_bridge` / `ae_harness`，随能力删除的整文件删除。验证：`grep -rln "engines.agents" tests` 无输出，`python -m pytest -c tests/pytest.ini` 全绿
- [ ] 6.6 收尾门禁：`python run.py check` 24 项阻塞全绿，`openspec validate retire-engines-agents --strict` 通过
