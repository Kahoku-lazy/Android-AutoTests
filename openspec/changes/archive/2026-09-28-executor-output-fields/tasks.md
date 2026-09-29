## 1. 引擎契约：执行模型只回三字段

- [x] 1.1 `engines/ai/agentscope/workflow.py`：`ExecutionOutput` 换成 `result`（Literal PASS/FAIL）、`click_timer`、`screenshot` 三字段，去掉 `action` / `message`；`_execute_step` 的兜底对象与日志同步（兜底 = FAIL + 两个空串）；`_log_step` 的 docstring 与返回形状说明同步。验证：`python -m pytest tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 全绿（两个用例文件的 `ExecutionOutput(...)` 构造同步改为新字段）。验证结果：连同新增的 `test_ai_executor_output_contract.py` 共 27 项通过；`_role_trace` 记录的原始输出文本不受影响。
- [x] 1.2 `engines/ai/agentscope/model.py`：`VerifierRole.run` 的第二个证据参数由「执行模型说明文字」改为平台拼装的「点击前时间戳 + 点击后截图路径」文本（无点击 / 未截图时如实标注），输入文案同步；`engines/ai/agentscope/workflow.py` 的 `_verify_step` 按新契约传参、不再读 `message`。验证：`python -m pytest tests/graybox/unit -k "workflow or executor_log_check or log_evidence" -q` 全绿；`python -m ruff check engines/ai apps/ai_assistant` 通过。验证结果：`-k` 命中 84 项，83 通过；唯一失败 `test_workflow_single_path.py::test_frontend_api_layer_has_no_legacy_create_paths` 断言 `frontend` 的 workflow prototypes 路径存在，属本变更之外的存量红（本次未触碰该文件，与执行模型契约无关）。`ruff check` 通过、`ruff format --check` 50 文件已格式化。

## 2. 提示词：新契约同步到库

- [x] 2.1 新增 `apps/ai_assistant/migrations/0047_executor_output_fields.py`：对 `prompt_executor` 做四处短语级条件替换（输出字段块 / 输出格式约束末句 / 案例 JSON / 操作后截图命令行，锚点取 `0038` 快照原文），对 `prompt_verifier` 做一处（输入说明行）；每处不含锚点则跳过，reverse 按新文精确回退旧文。验证：`python manage.py makemigrations --check --dry-run` 无遗漏；新增单测用假行对象断言「旧文 → 新文」「新文 → 旧文原文」「已改写行原样跳过」三种情形全绿。验证结果：`No changes detected`；新增 `tests/graybox/unit/test_ai_executor_output_prompt_migration.py` 5 项通过（以 `0038` 平台原文快照为输入：executor 四处锚点全替换、verifier 输入行替换且验收自身输出契约不动、幂等、已改写行不动、apply→revert 回到原文）。
- [x] 2.2 对存量库应用并核对实际写入：`python manage.py migrate ai_assistant`，确认平台智能体的 `prompt_executor` 含 `click_timer` / `screenshot` 且不再含旧输出字段条目、`prompt_verifier` 输入段已改；若提示词已被用户改写导致跳过，如实记录。验证：迁移后读取该行提示词的字段清单，与迁移前对照（未改写则含新契约，已改写则保持原样）。验证结果：`Applying ai_assistant.0047_executor_output_fields... OK`；平台智能体（id=10）迁移前 `prompt_executor` 长度 1701 且含旧 `- message：操作说明，或遇到的问题。`，迁移后 2038 且四处旧锚点全部消失（输出字段三键、SOP 操作后截图行已带 `keep_local=true`、案例 JSON 只含三键），`prompt_verifier` 输入行已换新且其自身输出契约（`- action：被验证的操作。`）保持不动。提示词未被用户改写，因此本次为实际写入而非跳过。

## 3. 前端：任务详情按新契约呈现

- [x] 3.1 `frontend/src/shared/types/ai.ts` 的 `TaskRunExecutorOut` 增 `click_timer` / `screenshot`（旧 `action` / `message` 保留为可选，供存量记录）；`helpers/task-detail.ts` 的 attempt 派生同时带出新旧字段（旧记录按旧字段兜底）。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查退出码 0（新字段在 `TaskStepAttempt` 上为可选，存量旧记录与既有用例构造无需改动）。
- [x] 3.2 `components/TaskAttemptCard.vue` 执行结果段：有 `click_timer` 时显示「点击前时间」，有 `screenshot` 时显示「点击后截图」路径（有图可点开原图）、为空时如实标注无截图；旧记录仍按 `message` 呈现，不出现空壳。验证：新增/更新 `frontend/tests/ai-assistant/p0/TaskAttemptCard.spec.ts` 覆盖「新三字段可见 + 截图可点开」「screenshot 为空如实标注」「旧记录仍按 message 呈现」三条；`npx vitest run tests/ai-assistant/p0/TaskAttemptCard.spec.ts tests/ai-assistant/p0/task-detail.spec.ts` 全绿。验证结果：三文件 32 项通过（TaskAttemptCard 13 含新增 4 项 / task-detail 10 含新增 1 项 / task-log-check 9 回归）；未截图文案取新常量 `STEP_EXEC_NO_SHOT_TEXT`（「该步未截图」），与「日志检查」块的「该次点击后未截图」区分，不借用验收截图。

## 4. 文档与契约对照

- [x] 4.1 `dev_docs` 的 AI 助手接口文档里任务详情的 `log[].executor` 示例与字段说明同步为新三字段（doc 中的旧示例仍写着 `{action, result, message}`），并注明存量旧记录仍按旧字段下发。验证：按端点速查定位该段，示例与字段说明与实现一致（三边对照：文档 / 引擎输出 / 前端 DTO）。验证结果：任务详情示例的 `executor` 改为 `{result, click_timer, screenshot}`，并在该段下方补一条口径说明（三键含义、空串语义、存量旧记录仍为 `{action,result,message}` 且前端按旧字段兼容）；顺带把「模型调试」小节的成功响应字段表补上 `reply` 行（执行模型回复即该三字段 JSON，规划/验收角色各自形状一并写明）。三边对照一致：引擎 `ExecutionOutput` / 前端 `TaskRunExecutorOut` / 文档同键同名。

## 5. 收口

- [x] 5.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant engines/ai`、`python -m pytest tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_model_debug.py tests/graybox/unit/test_ai_debug_log_check.py -q`。验证：全部通过（不跑全量回归）。验证结果：`System check identified no issues (0 silenced)`；`No changes detected`；`ruff check` + `ruff format --check` 全通过（50 文件已格式化）；连同新增的两个用例文件共 56 项通过。
- [x] 5.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant src/shared/types` 无新增 error、`npx vue-tsc --noEmit` 通过。验证：命令输出与退出码。验证结果：prettier 全通过（两个 spec 先 `--write` 归一）；eslint 10 warning / 0 error，全为存量（`vue/no-mutating-props` / 未用变量 / `no-console`），退出码 0；`vue-tsc --noEmit` 退出码 0；复跑三个相关用例文件 32 项通过。
- [ ] 5.3 页面验收（用户侧，需重启后端）：到执行模型调试台选定设备，发一条会点开关的内容 —— 助手消息里的模型回复应只有 `result` / `click_timer` / `screenshot` 三个键，且时间戳与截图路径可直接读到；再到任务详情页看新任务的执行结果段，能看到执行结果、点击前时间与点击后截图（可点开）；打开一个历史任务确认旧记录照常显示。验证：用户目视确认。
