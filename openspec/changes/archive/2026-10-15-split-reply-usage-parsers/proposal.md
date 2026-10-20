## Why

`reply` 的最终消息把用量放在 `usage` 对象里，`reply_stream` 的 `ModelCallEndEvent` 把同样三项铺在事件字段上。`messages.py`、`SopRunner`、`DialogueLog` 各取一次，字段对齐但入口不统一，费用计算无法共用同一份解析结果。

## What Changes

- 在 `engines/agents/messaging/messages.py` 增加两个解析类：`ReplyParser` 解析 `agent.reply()` 返回的最终消息；`ReplyStreamParser` 解析 `reply_stream` 的单条事件。
- 两个类的 `tokens()` 都返回 `(输入 token, 输出 token, 缓存命中 token)`。取不到用量时返回 `(0, 0, 0)`。该三元组可直接传给 `DeepSeekBilling.cost`。
- 流式解析只从单条 `ModelCallEndEvent` 取用量。其它事件不构成一次可计费调用。调用方按该次事件的时刻分别计费，再把费用相加。
- `reply_usage` 与 `reply_cost` 改为经 `ReplyParser` 取值。`print_result`、`render_reply_stream`，以及截图路径、工具文本清洗函数保持为函数。
- **BREAKING** 将 `engines/agents/billing.py` 移到 `engines/agents/messaging/billing.py`。原路径不再保留再导出。`SopRunner` 与 `DialogueLog` 改为使用 `ReplyStreamParser.tokens()`，再调用搬迁后的 `DeepSeekBilling`。
- 更新 `engines/agents/AGNETS.md` 中计费模块的位置说明。
- 不改 `engines/ai` 的平行实现。不改价目、高峰规则、对话稿字段和 SOP 汇总口径。

## 关联文档

无关联需求编号。本次是脚手架内部的消息用量解析重构：SOP 逐次计费结果、对话稿助手块字段、平台用量统计均保持现有规格。不进入 PRD / ARCH 编号体系。

## Capabilities

### New Capabilities

- `agent-reply-usage`: 从最终回复与流式模型调用结束事件解析出同一 token 三元组，供 DeepSeek 计费使用。

### Modified Capabilities

无。`agent-role-billing` 的价目与取位、`agent-sop-runner` 的逐次计费后求和、`agent-dialogue-log` 的助手块字段均不改变。

## Impact

- 代码：`engines/agents/messaging/messages.py`、`engines/agents/messaging/__init__.py`、`engines/agents/messaging/dialogue.py`、`engines/agents/workflow/runner.py`、`engines/agents/AGNETS.md`；删除 `engines/agents/billing.py`，新增 `engines/agents/messaging/billing.py`。
- 导入：`from engines.agents.billing import DeepSeekBilling` 与 `from ..billing import DeepSeekBilling` 失效，改为 messaging 包内导入。
- 测试：覆盖两个解析类的三元组，以及「流式按单次事件计费」与现有 `DeepSeekBilling.cost` 逐项相等。不跑全量回归。
- 范围外：`engines/ai/**`、工具文本清洗、上屏渲染、角色 `reply` / `reply_stream` 的运行入口。
