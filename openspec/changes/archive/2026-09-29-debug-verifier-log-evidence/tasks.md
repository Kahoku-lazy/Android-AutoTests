## 1. 引擎：日志证据渲染收敛到共享模块

- [x] 1.1 把 `engines/ai/agentscope/workflow.py` 的 `_render_log_evidence` 与等级标签移到 `engines/ai/agentscope/logcheck.py`（公开名 `render_log_evidence` / `GRADE_LABEL`），`workflow.py` 改为导入（私有别名保持既有调用与测试不变）。验证：`python -m pytest tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 全绿；`python -m ruff check engines/ai` 通过。验证结果：迁移后 `test_ai_workflow_log_evidence.py` 10 项 + `test_ai_executor_log_check.py` 13 项全绿（既有 `_render_log_evidence` 调用点与测试未动）；`ruff check` + `ruff format` 通过。

## 2. 后端：按基准时刻从日志文件取证据

- [x] 2.1 新增 `apps/ai_assistant/log_history.py`：`extract_basis_time(text)`（取第一个北京时间毫秒时间戳，找不到返回空串）与 `history_evidence(basis_time, *, window_seconds, baseline_seconds, tail_lines)`（按来源登记定位 `logs/{SKU}_{端口}.log`，尾部读后按时刻过滤，交给 `build_evidence` 出证据块；文件缺失/不可读/窗口内无日志时如实返回空证据并给出原因）。验证：新增 `tests/graybox/unit/test_ai_debug_log_history.py`，用临时日志文件断言「按基准切窗取到命中与时间戳」「时刻早于所读范围时如实为空」「文件缺失不抛错」「时刻识别取第一个、非法文本返回空串」全绿。验证结果：7 项通过（含监听开关关着时 `NOTE_NO_LISTEN`、无端口来源时 `NOTE_NO_SOURCE`、没给基准时退回最近窗且 `from_message=False`）；实现上把候选行先按「基准 − 基线 ~ 基准 + 2×阈值」过滤，避免窗口后的尾行把「窗口内无日志」判成「未命中」。
- [x] 2.2 `apps/ai_assistant/model_debug.py` 的 `run_role_chat`：对验收角色在 `ask()` 之前算出证据块并渲染进模型输入，响应新增 `log_evidence` 与 `log_basis`（`basis_time` / `from_message` / `files` / `note`）；规划与执行角色的输入与响应 MUST NOT 变化。验证：扩展 `tests/graybox/unit/test_ai_debug_log_check.py` 断言「验收对话的模型输入含证据文本与 logAssertionTimer 取值指引」「响应带 log_evidence 与 log_basis」「消息无时刻时 from_message=False」「无端口监听时不取证据、不开端口」「执行角色输入不含证据块」全绿。验证结果：该文件 9 项通过（既有 5 项点击证据用例未回归）；输入里同时给出「来源：消息里的时刻 / 最近一个取证窗」与「调试回溯，不是生产取证窗」的口径说明。

## 3. 前端：调试台呈现证据与基准

- [x] 3.1 `api/toolbox.ts` 的 `ModelDebugReply` 与 `composables/useModelDebug.ts` 的消息 DTO 增 `log_evidence`（复用 `shared/types/ai.ts` 的 `TaskLogEvidence`）与 `log_basis`（基准时刻 / 来源 / 文件），并透传。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查退出码 0；`log_basis` 形状落在共享类型 `ModelDebugLogBasis`。
- [x] 3.2 `ModelDebugPage.vue`：在助手消息内按「有基准说明」渲染基准行、按「有证据块」渲染既有 `StepLogEvidence`；无证据时给可读原因，不留空壳。验证：扩展 `frontend/tests/ai-assistant/p0/model-debug-log-check.spec.ts` 断言「带证据时块可见且含命中关键词与基准来源」「无证据时给原因说明」「块内无按钮与输入控件」；`npx vitest run tests/ai-assistant/p0/model-debug-log-check.spec.ts tests/ai-assistant/p0/useModelDebug.spec.ts` 全绿。验证结果：该文件 9 项通过（新增 4 项，含 composable 透传全链路）；文案集中在 `constants.ts` 的 `MODEL_DEBUG_LOG_BASIS_LABEL` 与 `modelDebugLogBasisText`，页面只渲染。

## 4. 文档与契约对照

- [x] 4.1 `dev_docs` 的 AI 助手接口文档「模型调试」小节补上调试响应新增的两个键、取证基准的识别口径（消息里第一个毫秒时间戳 → 否则最近窗）与「从日志文件回溯、不是生产 5 秒取证窗」的说明。验证：文档字段表与实现一致，且与前端 DTO 同键名。验证结果：字段表新增 `log_evidence` 与 `log_basis` 两行（含 `basis_time` / `from_message` / `files` / `note` 的语义、取证窗 5 秒与「端口关着不取证据也不开端口」的口径）；键名与实现、前端 DTO 三边一致。

## 5. 收口

- [x] 5.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant engines/ai`、`python -m pytest tests/graybox/unit/test_ai_debug_log_history.py tests/graybox/unit/test_ai_debug_log_check.py tests/graybox/unit/test_ai_model_debug.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q`。验证：全部通过（不跑全量回归）。验证结果：`System check identified no issues (0 silenced)`；`No changes detected`；`ruff check` + `ruff format --check` 全通过（126 文件已格式化）；五个相关用例文件共 58 项通过。
- [x] 5.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant src/shared/types` 无新增 error、`npx vue-tsc --noEmit` 通过。验证：命令输出与退出码。验证结果：prettier 全通过；eslint 10 warning / 0 error（全为存量），退出码 0；`vue-tsc --noEmit` 退出码 0；四个相关用例文件 67 项通过。
- [ ] 5.3 页面验收（用户侧，需重启后端）：到验收模型调试台，把执行模型的回复（含点击时刻）贴进去发一条 —— 助手消息里应出现日志证据块与基准说明，模型回复的 `logAssertionTimer` 应有值；再发一条不带时刻的确认退回最近窗并标明来源。验证：用户目视确认。
