## 1. 引擎契约：验收模型只回五字段

- [x] 1.1 `engines/ai/agentscope/workflow.py`：`VerificationOutput` 换成 `result`（Literal PASS/FAIL）、`click_timer`、`log_assertion_timer`（alias `logAssertionTimer`）、`screenshot`、`actual` 五字段，去掉 `action` / `assert`；`_verify_step` 的兜底对象、日志与 docstring 同步（兜底 = FAIL + 三个空串 + 可读 actual）。验证：新增 `tests/graybox/unit/test_ai_verifier_output_contract.py` 断言「五键且按别名下发」「缺 result / 非 PASS-FAIL 不成立」「空值默认」全绿。验证结果：该文件 10 项通过，其中 `test_contract_has_exactly_five_fields_with_alias` 断言 `model_dump(by_alias=True)` 恰好等于五键契约（键名含 camelCase 的 `logAssertionTimer`），`test_invalid_output_is_rejected` 覆盖缺 result / 旧布尔 result / 非 PASS-FAIL / 非 JSON 对象四种无效输出。
- [x] 1.2 `engines/ai/agentscope/workflow.py` 的两处通过判定由 `verdict.result is True` 改为 `== "PASS"`（`_run_step` 与 `run`）；失败原因回灌（`retry_hint = verdict.actual`）与失败步骤记录的 `actual` 保持；`engines/ai/agentscope/model.py` 的 `VerifierRole` 输入文案给出来源标注（点击前时间戳来自平台证据、日志关键词时间戳取日志证据命中那一次）。验证：`python -m pytest tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_executor_log_check.py -q` 全绿（含把桩结果从布尔改为 `PASS`）；`python -m ruff check engines/ai` 通过。验证结果：新增的三条判定用例通过 —— `FAIL` 时第二次执行拿到的 retry_hint 等于 `actual`（`["", "灯没亮"]`）、`PASS` 时不重试（`hints == [""]`）、`run()` 的失败记录 `failed[0].actual == "灯没亮"`；两个既有用例文件的桩已改为新契约，`ruff check` 通过。

## 2. 提示词：新契约同步到库

- [x] 2.1 新增 `apps/ai_assistant/migrations/0048_verifier_output_fields.py`（依赖 `0047`）：对 `prompt_verifier` 做六处短语级条件替换（照抄截图路径那条 / 日志证据段 `判 true/false` 措辞 / 验收段 actual-result-偏离三条 / 输出字段块 / 输出格式约束 / 案例 JSON），锚点取当前库中原文；每处不含锚点则跳过，reverse 按新文精确回退。验证：`python manage.py makemigrations --check --dry-run` 无遗漏；新增单测（输入为 0038 快照经 0044、0047 纯函数处理后的当前原文）断言「旧文 → 新文」「幂等」「已改写行不动」「apply→revert 回到当前原文」全绿。验证结果：`No changes detected`；新增 `tests/graybox/unit/test_ai_verifier_output_prompt_migration.py` 8 项通过（输出字段五键、`screenshot` 照抄路径那条取代原「不要抄写路径」、日志证据段与验收段措辞全改 PASS/FAIL、案例 JSON 含 `logAssertionTimer`、幂等、已改写行不动、回滚回到当前原文）。
- [x] 2.2 对存量库应用并核对实际写入：`python manage.py migrate ai_assistant`，确认平台智能体的 `prompt_verifier` 含五字段说明与 `logAssertionTimer`、不再含旧输出字段条目、且日志证据段措辞已改；若提示词已被用户改写导致跳过，如实记录。验证：迁移前后读取该行提示词的关键锚点与长度并对照。验证结果：`Applying ai_assistant.0048_verifier_output_fields... OK`；平台智能体（id=10）`prompt_verifier` 长度 1245 → 1689，五字段条目与「五个键」约束均在，旧 `- action：被验证的操作。` / `- assert：断言。` / `true 表示操作成功` / `判 true|false` / `不要编造或抄写文件路径` / 案例里的 `"result": true` 全部消失（残留检查 `leftovers = []`）。提示词未被用户改写，因此为实际写入而非跳过。

## 3. 前端：任务详情按新契约呈现验收

- [x] 3.1 `frontend/src/shared/types/ai.ts` 的 `TaskRunVerifierOut` 增 `click_timer` / `logAssertionTimer` / `screenshot`（旧 `action` / `assert` / `actual` / 布尔 `result` 保留为可选，供存量记录）；`helpers/task-detail.ts` 的 attempt 派生带出 `verifierLogTimer` / `verifierScreenshotPath`（旧记录为空串）。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查退出码 0（新字段在 `TaskStepAttempt` 上为可选，既有用例构造无需改动）。
- [x] 3.2 `components/TaskAttemptCard.vue`：验收段在 `logAssertionTimer` 非空时显示「日志断言时间」行（为空不渲染、不顶替）；验证截图块补模型回报的路径文本（图片仍取平台验收截图）；旧记录仍按 `actual` + 布尔结果呈现。验证：更新 `frontend/tests/ai-assistant/p0/TaskAttemptCard.spec.ts` 覆盖「日志断言时间可见 / 为空不渲染」「验证截图路径文本可见」「旧记录兼容」三条，`frontend/tests/ai-assistant/p0/task-detail.spec.ts` 覆盖新键映射与 `PASS` 归一化；`npx vitest run tests/ai-assistant/p0/TaskAttemptCard.spec.ts tests/ai-assistant/p0/task-detail.spec.ts` 全绿。验证结果：四个用例文件 67 项通过（TaskAttemptCard 17 含新增 4 项 / task-detail 11 含新增 1 项 / task-log-check 9 / useModelDebug 30 回归）；只有模型回报路径、没有落盘图时仍显示路径文本且不渲染图片；存量旧记录的两行新坐标均不出现。

## 4. 文档与契约对照

- [x] 4.1 `dev_docs` 的 AI 助手接口文档同步：任务详情 `log[].verifier` 的新五字段与存量旧记录口径；模型调试小节的 `reply` 行把验收模型的回复形状改为该五字段。验证：三边对照（引擎 `VerificationOutput` / 前端 `TaskRunVerifierOut` / 文档）键名一致。验证结果：任务详情示例的 `verifier` 改为 `{result, click_timer, logAssertionTimer, screenshot, actual}`，并补一条口径说明（五键含义、空值语义、`actual` 是失败重试回灌的原因、存量旧记录仍为 `{action,assert,actual}` + 布尔 result）；「模型调试」小节 `reply` 行列出验收模型的五键回复形状。三边键名一致：`result` / `click_timer` / `logAssertionTimer` / `screenshot` / `actual`。

## 5. 收口

- [x] 5.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant engines/ai`、`python -m pytest tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_executor_log_check.py tests/graybox/unit/test_ai_model_debug.py tests/graybox/unit/test_ai_debug_log_check.py tests/graybox/unit/test_ai_verifier_output_contract.py tests/graybox/unit/test_ai_verifier_output_prompt_migration.py -q`。验证：全部通过（不跑全量回归）。验证结果：`System check identified no issues (0 silenced)`；`No changes detected`；`ruff check` + `ruff format --check` 全通过（124 文件已格式化）；连同上一变更的两个契约/迁移用例共 74 项通过。
- [x] 5.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant src/shared/types` 无新增 error、`npx vue-tsc --noEmit` 通过。验证：命令输出与退出码。验证结果：prettier 全通过；eslint 10 warning / 0 error，全为存量，退出码 0；`vue-tsc --noEmit` 退出码 0；四个相关用例文件 67 项通过。
- [ ] 5.3 页面验收（用户侧，需重启后端）：到验收模型调试台选定设备，发一条会验收的内容 —— 助手消息里的模型回复应只有 `result` / `click_timer` / `logAssertionTimer` / `screenshot` / `actual` 五个键；再到新跑出的任务详情页看验收段，应能看到验收结果、实际结果、日志断言时间（有日志时）与验证截图路径（可点开）；打开历史任务确认旧记录照常显示。验证：用户目视确认。

## 6. 修订（2026-09-29，需求方澄清：加 `logAssertionInfo`，且「日志检测到 + 截图确认」两条件才 PASS）

- [x] 6.1 `VerificationOutput` 增第六个字段 `log_assertion_info`（alias `logAssertionInfo`）；`workflow._fill_log_assertion` 按本轮对 `check_device_log` 的**实际调用**自动填关键词（按调用顺序去重、「、」连接），并在模型把 `logAssertionTimer` 留空而工具**确实检测到**时用最早命中时间戳补上（不覆盖模型已写值、不编造）。验证：`tests/graybox/unit/test_ai_verifier_output_contract.py` 14 项通过（六键契约、别名下发、无效输出、自动填关键词、仅在留空时补时间戳、未检测到保持空串、不改判）。
- [x] 6.2 判定口径「日志检测到 + 截图确认两个条件都满足才可判 PASS，未检测到该关键词必须判 FAIL」写进两处：平台拼的验收输入（`workflow._verify_step` → `VerifierRole.run`，与调试台 `model_debug._keyword_catalog_input`）与库中提示词（迁移 `0050_verifier_log_check_contract`）；平台仍不改判模型给出的 result。验证：`test_ai_debug_log_check.py::test_verifier_chat_input_carries_keyword_catalog_and_rule` 与 `test_ai_verifier_log_check_prompt.py` 通过。
- [x] 6.3 前端呈现新字段：`TaskRunVerifierOut` 增 `logAssertionInfo`、attempt 派生 `verifierLogInfo`、详情页验收段新增「日志断言」行（为空不渲染）；调试台响应新增 `log_assertion_info` 并在日志证据块内显示「本轮检查的日志关键词」。验证：`frontend/tests/ai-assistant/p0/` 四个文件 70 项通过（TaskAttemptCard 新增 2 项、task-detail 映射断言、model-debug-log-check 新增 2 项）。
- [x] 6.4 文档同步：接口文档的 `log[].verifier` 六字段说明与「两条件」口径、模型调试小节的 `reply` 与新增 `log_assertion_info` 键。验证：三边一致（引擎 `VerificationOutput` / 前端 DTO / 文档）。
