## Why

执行模型（含执行模型调试台）目前返回 `{action, result, message}`：`message` 是模型自由发挥的说明文字，把「点击前时间戳」和「截图路径」混在自然语言里，机器读不了、页面上也拆不出来。需求方要求执行模型输出固定三字段：`result`（执行结果）、`click_timer`（点击前的时间戳）、`screenshot`（截图路径），使排查与断言都能直接读字段，而不是读模型作文。

## What Changes

- 执行模型输出契约改为三字段：`result`（PASS/FAIL）、`click_timer`（点击前时间戳，取点击类工具返回的 `action_time`）、`screenshot`（点击后截图路径，取 `screenshot_page(keep_local=true)` 返回的 `screenshot_path`）；**BREAKING**：不再输出 `action` 与 `message`。
- 执行模型系统提示词的「输出字段 / 输出格式约束 / 案例」段与操作后截图口径同步改写；存量库提示词由可逆迁移按锚点同步（已被用户改写、不含锚点的提示词保持原样）。
- 验收模型的输入说明同步：改为「result + 点击前时间戳 + 点击后截图路径 + 操作结果截图」，不再有 `message`；平台按新契约拼验收输入，MUST NOT 依赖模型自述说明。
- 任务过程记录的 `executor` 段落新字段；任务详情页「执行结果」段新增「点击前时间」与「点击后截图」（有路径可点开原图），存量旧记录继续按 `action`/`message` 如实呈现、不报错。
- 非目标：不改动平台装配的「日志检查」点击证据块（`executor_log_check` / `log_check`）——它照旧由平台按工具轨迹装配，与模型自报的两字段相互独立，模型抄错不影响该块。
- 非目标：不改验收模型的输出契约（仍为 `action/assert/actual/result`）、不改 5 秒取证窗与日志证据口径、不改工具侧的 `action_time` 打点与截图落盘行为。

## 关联文档

- PRD-08（AI 助手 · 设备操控 · 工具箱）。
- 依赖既有能力：`ai-device-action`（动作发出时刻随工具结果回传）、`device-log-evidence`（日志证据口径，本次不动）。
- 与未归档变更 `2026-09-28-executor-step-log-check` / `2026-09-28-debug-console-log-check` 的关系：那两份定义的是**平台装配**的点击证据块（不依赖模型自觉），本次改的是**模型自己**的输出字段；两者并存、互不替代。

## Capabilities

### New Capabilities

- `ai-executor-output`: 执行模型的输出契约（三字段与取值来源）、执行模型提示词对该契约的声明与存量库同步、以及该契约的消费方（任务过程记录 / 任务详情呈现 / 验收模型输入 / 执行模型调试对话同契约）。

### Modified Capabilities

（无）

## Impact

- 引擎：`engines/ai/agentscope/workflow.py`（`ExecutionOutput` 与执行/验收两处调用）、`engines/ai/agentscope/model.py`（`VerifierRole.run` 输入参数与文案）、`apps/ai_assistant/model_debug.py`（调试装配同契约，代码预计不变）。
- 后端数据：新增一份可逆迁移，同步 `ai_agents.prompt_executor`（输出字段 / 输出格式约束 / 案例 / 操作后截图口径）与 `prompt_verifier`（输入说明）。
- 前端：`shared/types/ai.ts`（`TaskRunExecutorOut`）、`helpers/task-detail.ts`（attempt 派生）、`components/TaskAttemptCard.vue`（执行结果段呈现）。
- 测试：`tests/graybox/unit/`（执行/验收输出契约与过程记录）、`frontend/tests/ai-assistant/p0/`（详情页呈现与旧记录兼容）。
- 兼容性：存量任务的过程记录仍是旧三字段，前端按旧字段如实呈现；新任务的记录只有新三字段。
