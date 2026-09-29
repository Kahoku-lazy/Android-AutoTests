## 1. 配对逻辑收敛到共享纯函数

- [x] 1.1 新增 `engines/ai/agentscope/logcheck.py`：把 `extract_action_time` 与 `build_executor_log_check` 从 `workflow.py` 迁入并去掉下划线前缀，模块 docstring 写明「点击↔截图配对与切片口径的唯一真相源，任务链路与调试台共用」。验证：`python -m pytest tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 全绿（导入路径同步调整）。验证结果：迁移后 23 项通过（executor_log_check 13 / workflow 10）；测试导入改为 `engines.ai.agentscope.logcheck`，并顺带清掉 `workflow.py` 里不再使用的 `_ACTION_TIME_PATTERN`。
- [x] 1.2 `engines/ai/agentscope/workflow.py` 改为从新模块 import 使用（`_step_action_times` 等既有私有名与对外行为保持不变）。验证：`python -m pytest tests/graybox/unit -k "workflow or log_evidence or executor_log_check" -q` 全绿；`python -m ruff check engines/ai` 通过。验证结果：`ruff check` + `ruff format --check` 全通过；`workflow.py` 内 `build_executor_log_check` / `extract_action_time` 各只剩引用一处，无残留私有定义。

## 2. 调试对话接线（开窗 → 对话 → 读窗 → 响应）

- [x] 2.1 `apps/ai_assistant/model_debug.py` 的 `run_role_chat`：需要设备的角色在 `role_obj.ask()` 之前取 `ensure_log_evidence()` 并 `open_window(device, label="model-debug")`；对话后从**全量** `tool_usage` 用共享纯函数算出 `clicks`（`skip_results=0`），有点击且有提供者时 `read_window(device, window_id, action_times=[各点击时刻])` 取证据，响应新增 `log_check`（形状 `{"clicks": [...], "log": <证据块>|None}`；无点击时不出现该键）。验证：新增 `tests/graybox/unit/test_ai_debug_log_check.py` 断言「有点击 → 带 clicks 与 log」「无点击 → 无该键」「provider 为 None → clicks 照旧、log 为 None」，且 `open_window` 调用发生在 `ask()` 之前（桩记录调用顺序）。验证结果：5 项通过；调用顺序断言为 `["open", "ask", "read"]`，读窗入参为 `("DEV-1", "w-debug", [点击时刻])`。
- [x] 2.2 无端口监听 / 采集未启用时 MUST NOT 打开端口：桩掉 `ensure_log_evidence()` 返回 `None`，断言响应仍 200、`clicks` 非空、`log` 为 None，且未调用任何开关写入口。验证：同上文件的对应用例。验证结果：`test_chat_without_listening_port_keeps_clicks_without_log` 通过（提供者为 None → 不开窗、不读窗，`log` 为 `None`）；本变更不触碰 `log_port_service` 的任何写入口。
- [x] 2.3 `apps/ai_assistant/views_model_debug_drf.py` 透传该键（不裁剪、不改信封）。验证：`tests/graybox/unit/test_ai_model_debug.py` 与新增用例走 HTTP 端点断言响应含 `log_check`；`python -m pytest tests/graybox/unit/test_ai_model_debug.py -q` 全绿。验证结果：视图本就原样 `Response(run_role_chat(...))`，无需改动；新增 `test_chat_endpoint_passes_log_check_through` 走真实端点断言信封里 `data.log_check.clicks[0].action_time` 与 `data.log_check.log.conclusion` 均在；既有 `test_ai_model_debug.py` 26 项全绿。

## 3. 前端：调试台助手消息内呈现

- [x] 3.1 `api/toolbox.ts` 的 `ModelDebugReply` 与 `composables/useModelDebug.ts` 的消息 DTO 增 `log_check`（复用 `shared/types/ai.ts` 的 `TaskLogCheck`）并透传。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查无输出、退出码 0。
- [x] 3.2 `ModelDebugPage.vue`：在助手消息的「回复」区块之后按 `hasLogCheck(item.log_check)` 渲染既有 `StepLogCheck`（无该键 / 无点击时不渲染，不留空壳）。验证：新增 `frontend/tests/ai-assistant/p0/model-debug-log-check.spec.ts` 覆盖「有点击带日志 → 块可见且含时间点、截图路径与命中关键词」「未标记（无 log）→ 只有时间点与截图」「无该键 → 不渲染该块」「块内无按钮与输入控件」。验证结果：5 项通过（首条走真实 composable 的 `send()` 流程，验证响应 → 消息 → 渲染的透传链路）。顺带把「工具调用轨迹」单条展示上限由 160 字符放宽到 600，使 `action_time` 这类尾部字段不再被截掉。
- [x] 3.3 既有调试台用例回归：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts` 全绿（消息 DTO 变更不破坏既有断言）。验证结果：本变更相关 6 个用例文件共 64 项通过（useModelDebug 30 / model-debug-log-check 5 / task-log-check 9 / TaskAttemptCard 9 / task-detail 9 / useTaskDetail 2）。

## 4. 收口

- [x] 4.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant engines/ai`（相关路径）、`python -m pytest tests/graybox/unit/test_ai_debug_log_check.py tests/graybox/unit/test_ai_model_debug.py tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q`。验证：全部通过。验证结果：`manage.py check` 无问题、`No changes detected`、`ruff check` + `ruff format --check` 通过；相关后端用例 63 项通过（含 model_debug 26 / debug_log_check 5 / executor_log_check 13 / workflow_log_evidence 10 / wiring 12 / planner 指引 4，后三项为本变更同批回归）。
- [x] 4.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant src/shared/types` 无新增 error、`npx vue-tsc --noEmit` 通过。验证结果：prettier 全通过；eslint 10 warning / 0 error（全为存量）；`vue-tsc` 退出码 0。
- [x] 4.3 接口文档同步：`dev_docs` 的 AI 助手接口文档补上调试对话响应新增的 `log_check` 字段、语义与「读窗等待约 5 秒」的说明（契约对照：前端 DTO / 文档 / 实现三边一致）。验证结果：8.2h 小节的成功响应示例与字段表已含该键，端点速查表描述同步。
- [ ] 4.4 页面验收（用户侧，需重启后端）：在执行模型调试台选定设备，发一条会点开关的内容 —— 助手消息内应出现「日志检查」，含点击前时间点、点击后截图路径与点击后 5 秒内的日志（原始日志 + 命中标注）；把「无线端口」的监听关闭后再发一条，确认点击证据仍在、日志部分如实说明无日志证据。验证：用户目视确认。
