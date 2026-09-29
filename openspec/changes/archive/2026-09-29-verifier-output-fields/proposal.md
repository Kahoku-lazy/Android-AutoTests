## Why

验收模型（含验收模型调试台）目前返回 `{action, assert, actual, result}`：`result` 是 true/false 布尔，且完全不带「这一验是拿哪一次点击、哪一条日志来判断的」证据坐标 —— 排查时只能读模型作文，机器读不了。需求方要求验收模型输出固定字段：`result`（PASS/FAIL）、`click_timer`（点击前时间戳）、`logAssertionTimer`（检测到日志关键词的时间戳，未检测到为空）、`screenshot`（验证截图路径），并保留 `actual`（截图里实际看到什么）作为达标/不达标的原因说明。

## What Changes

- 验收模型输出契约改为五字段：`result`（`PASS`/`FAIL`，**BREAKING**：不再是布尔）、`click_timer`（取输入里执行侧给出的点击前时间戳；本步无点击为空串）、`logAssertionTimer`（取输入日志证据里命中关键词那一次的日志时间戳，多次命中取最早一次；未采集日志 / 未命中 / 无日志证据块时为空串）、`screenshot`（取本人 `screenshot_page(keep_local=true)` 返回的 `screenshot_path`）、`actual`（截图里的实际结果）；**BREAKING**：不再输出 `action` 与 `assert`。
- 验收模型系统提示词同步改写：输出字段 / 输出格式约束 / 案例、日志证据段里 `判 true/false` 的措辞改为 `判 PASS/FAIL`、以及原先「你的最终 JSON 不要编造或抄写文件路径」与新契约（要照抄 `screenshot_path`）冲突的那一条；存量库提示词由可逆迁移按锚点同步。
- 工作流以 `result == "PASS"` 判通过；失败时仍把 `actual` 回灌给执行模型重试（**保留原因回灌**，这是本次选择保留 `actual` 的理由）。
- 任务详情页「验收」段新增「日志断言时间」行，验证截图块补上模型回报的路径文本（图片仍取平台落盘的验收截图）；存量旧记录（`action/assert/actual` + 布尔 `result`）继续如实呈现、不报错。
- 非目标：不改验收模型的工具子集（仍仅为截图工具，不给它加日志查询工具）、不改平台的「日志检查」点击证据块与 5 秒取证窗口径、不改执行模型的输出契约（上一变更已定）。

## 关联文档

- PRD-08（AI 助手 · 设备操控 · 工具箱）。
- 依赖既有能力：`ai-executor-output`（上一变更：执行模型的三字段契约 —— 验收侧 `click_timer` 的来源就是它给出的执行证据）、`device-log-evidence`（日志证据块的命中与时间戳口径，本次不改，只从中取时间戳）。
- 与未归档变更 `2026-09-28-debug-console-log-check` 的关系：那份定义的是**平台装配**的点击证据块，本次改的是**验收模型自己**的输出字段，两者并存。

## Capabilities

### New Capabilities

- `ai-verifier-output`: 验收模型的输出契约（五字段与各自取值来源、空值口径）、验收模型提示词对该契约的声明与存量库同步、以及该契约的消费方（工作流的通过判定与失败原因回灌、任务过程记录、任务详情页呈现、验收模型调试对话同契约）。

### Modified Capabilities

（无）

## Impact

- 引擎：`engines/ai/agentscope/workflow.py`（`VerificationOutput`、兜底对象、两处通过判定）、`engines/ai/agentscope/model.py`（`VerifierRole.run` 的输入文案中给出来源标注）。
- 后端数据：新增一份可逆迁移，同步 `ai_agents.prompt_verifier`（输出字段 / 输出格式约束 / 案例 / 照抄路径那条 / 日志证据段措辞）。
- 前端：`shared/types/ai.ts`（`TaskRunVerifierOut`）、`helpers/task-detail.ts`（attempt 派生）、`components/TaskAttemptCard.vue`（验收段与验证截图块）。
- 测试：`tests/graybox/unit/`（契约、提示词迁移、工作流通过判定与失败回灌）、`frontend/tests/ai-assistant/p0/`（页面呈现与旧记录兼容）。
- 兼容性：存量任务的过程记录里 `verifier` 仍是旧四字段且 `result` 为布尔，前端按旧字段如实呈现；新任务只有新五字段。
