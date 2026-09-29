## 1. 引擎：标记与点击证据组装

- [x] 1.1 `engines/ai/agentscope/workflow.py`：`Step` 增 `log_check: bool = Field(default=False, ...)`（说明「本步断言是否需靠设备日志核对」）。验证：`pytest tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 仍全绿，且新增一条解析用例证明缺该键时默认 False、给 `true` 时为 True。验证结果：13 项用例通过；另加 `mode="before"` 宽松校验（字符串 / 数字 / 空值归一为布尔），保证该标记不会把整步建模拖垮（`_coerce` 校验失败会让整个规划作废）。
- [x] 1.2 新增纯函数 `_build_executor_log_check(result, skip_results, log_evidence, need_log) -> dict`：取 `result.tool_usage[skip_results:]`，按行序把「有 `action_time` 的结果行」记成点击，并为每次点击配对其后第一张带 `screenshot_path` 的行（已配对的不重复分配，无则空串）；`need_log` 为真时把 `log_evidence` 放进 `log` 键，否则 `log` 为 `None`。验证：新增用例覆盖「一步一次点击」「一步多次点击各自配对」「点击后未截图标空」「只读步骤无条目」「`skip_results` 吃掉本步全部返回时 `clicks` 为空」。验证结果：上述五种情形全部有用例覆盖并通过，另补「点击之前的截图不得复用」「一张截图只服务第一次点击」两条。
- [x] 1.3 `_log_step` 增 `executor_log_check` 参数并在 `need_log`/有内容时写入过程记录键 `executor_log_check`；`_run_step` 用**同一次** `seen_results` 快照组装并传入（与 `_step_action_times` 同源切片）。验证：用例断言过程记录键形状为 `{"clicks": [...], "log": ...|None}`，且未标记步骤 `log` 为 `None`；`pytest tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_log_evidence_wiring.py -q` 全绿。验证结果：新增两条工作流级用例证明「标记步骤的 `log` 与验收证据是同一份 dict」「未标记步骤只有 clicks、验收证据照旧并存」。

## 2. 规划提示词指引（可逆迁移）

- [x] 2.1 新增 `apps/ai_assistant/migrations/0046_add_planner_log_check_guidance.py`：forward 仅当 `prompt_planner` 含锚点 `- assert：该操作的断言，即操作后屏幕上可观察到的期望结果（供验证模型比对）。` 且不含标记 `log_check` 时插入指引块（判定口径 + 输出字段说明）；reverse 按插入块精确文本删除。验证：`python manage.py makemigrations --check --dry-run` 无遗漏。验证结果：`No changes detected`；`python manage.py migrate ai_assistant` 已应用（0045 → 0046），平台智能体（id=10）的 `prompt_planner` 长度 1205 → 1337 且含 `log_check` 指引；迁移前已核对该字段仍含平台原文锚点，因此实际写入成功（未被用户改写挡下）。
- [x] 2.2 新增 `tests/graybox/unit/test_ai_planner_log_check_guidance.py`：新装库（跑完迁移链后）规划提示词含该指引；存量原文库被补写且其余内容不变；管理员已改写的提示词不被改动；reverse 后回到原样。验证：`pytest tests/graybox/unit/test_ai_planner_log_check_guidance.py -q` 全绿。验证结果：4 项通过（插入位置在 assert 条目之后、幂等、不覆盖改写、回滚可逆）。

## 3. 前端：任务详情执行模型段呈现

- [x] 3.1 `frontend/src/shared/types/ai.ts` 增 `TaskLogCheck`（`clicks[{action_time, screenshot_path}]` + `log?`）并挂到任务过程记录 DTO；`helpers/task-detail.ts` 的 `toAttempt` 增 `logCheck` 透传。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查无输出、退出码 0。
- [x] 3.2 新增 `components/StepLogCheck.vue` + `StepLogCheck.style.css`：逐条渲染点击前时间点与截图路径（路径以文本呈现、有图时缩略图可点开），`log` 非空时内嵌既有 `StepLogEvidence`；`clicks` 与 `log` 均空时不渲染。`components/TaskAttemptCard.vue` 在执行结果段之后渲染该块。验证：`npx vitest run tests/ai-assistant/p0/task-log-check.spec.ts` 通过。验证结果：9 项通过；「不渲染」由 `helpers/task-detail.ts` 的纯函数 `hasLogCheck` 判定（父组件 `v-if`），组件本身不含判空分支之外的逻辑。
- [x] 3.3 新增 `frontend/tests/ai-assistant/p0/task-log-check.spec.ts`：标记步骤渲染三件内容；未标记步骤不出现日志内容；无点击且无日志时不渲染该块；既有任务（无该键）不报错；执行段与「设备日志证据」块并存。验证：`npx vitest run tests/ai-assistant/p0` 全绿。验证结果：本变更相关 4 个用例文件共 29 项通过（task-log-check 9 / TaskAttemptCard 9 / task-detail 9 / useTaskDetail 2）。

## 4. 收口

- [x] 4.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`ruff check apps/ai_assistant engines/ai`（相关路径）、`pytest tests/graybox/unit/test_ai_workflow_log_evidence.py tests/graybox/unit/test_ai_log_evidence_wiring.py tests/graybox/unit/test_ai_planner_log_check_guidance.py -q`。验证：全部通过。验证结果：`manage.py check` 无问题、`No changes detected`、`ruff check` + `ruff format --check` 全通过；相关后端用例 41 项通过（含 work_evidence 10 / wiring 12 / progress 2 / executor_log_check 13 / planner 指引 4）。
- [x] 4.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant src/shared/types` 无新增 error、`npx vue-tsc --noEmit`。验证：全部通过。验证结果：prettier 全通过；eslint 10 warning / 0 error（全为存量）；`vue-tsc` 退出码 0。
- [ ] 4.3 页面验收（用户侧）：跑一条断言涉及开关日志的任务 —— 执行模型段应显示「点击前时间点 + 点击后截图路径 + 该时间点后 5 秒内日志（原始日志与命中标注）」；再跑一条纯页面断言的步骤，确认只显示时间点与截图。验证：用户目视确认。
