## Why

`AgentEventsShow` 把智能体事件流用 `print` 打到控制台，跑 SOP 时和流程汇总混在一起，也留不下可回看的文件。调试时需要一条固定的「时间 | 模型 | 动作」日志，能按开始、思考、工具调用、工具返回、结束、模型 token、模型费用和本轮耗时把一轮执行读完。

## What Changes

- `AgentEventsShow` 不再 `print`。命中的阶段改由 loguru 追加写入 `logs/agent_events.log`。
- 每一行的形状为：上海时区毫秒时间、模型名、动作，动作后面带上明细（角色名、思考文本、工具名与完整入参或返回、token、结束原因、耗时）。入参与返回全文写入，不按字数截断。
- 动作使用：开始、思考、工具调用、工具返回、结束、模型token、模型费用、本轮执行时间、本轮执行总计量。模型调用结束时写两行：token 用 M（百万，6 位小数），费用用元（4 位小数）。发言结束时再写本轮合计，把各次调用的三项 token 与三项费用分别相加。
- 正文块、步骤边界 `CustomEvent`、未识别事件不再输出。图片不写 base64，只在「工具返回」里附媒体类型与长度。
- 「开始」发生在模型调用之前，模型名由调用方按角色名传入；模型调用开始后，后续行改用事件上的真实模型名。
- 更新定向单测，改为断言日志行。`dump` 与流程结束时的控制台汇总保持 `print`。

## 关联文档

无关联需求编号。这是 `engines/agents` 调试时间线的输出方式调整，不改变平台对外接口或页面。

## Capabilities

### New Capabilities

- `agent-events-show`: 把智能体事件流写成「时间 | 模型 | 动作」日志，覆盖一轮发言的八个动作、模型名来源、入参与返回全文、模型 token 与三项费用，以及图片不落正文。

### Modified Capabilities

无。对话稿（`agent-dialogue-log`）与平台过程日志（`ai-agent-process-log`）的文件、字段和按天切分都不改。

## Impact

- 代码：`engines/agents/messaging/messages.py` 的 `AgentEventsShow`；`engines/agents/workflow/ui_auto_workflow.py` 在调用时传入角色名到模型名的映射。
- 测试：`tests/graybox/unit/test_agent_events_show.py`。只跑这一条，不跑全量回归，不连设备。
- 依赖：`requirements.txt` 声明 `loguru`（当前文件已引用，但依赖清单未登记）。
- 不改前端、接口、数据库，也不改 `engines/ai/**` 与 `dump`。
