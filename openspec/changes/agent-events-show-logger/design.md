## Context

`AgentEventsShow.show(event, buf)` 按事件类名分派，各阶段用 `print` 打控制台。文件底部已有未完成的 loguru 草稿：`logger.add("logs/agent_events.log")` 写在 import 之后，每次导入都会再挂一个 sink，默认格式还带级别和代码位置。`logs/` 已被忽略。`loguru` 本机已安装，但 `requirements.txt` 未登记。

模型名不在发言开始事件上。`ModelCallStartEvent.model_name` 才是这次调用的名字，且它晚于发言开始。`ToolCallEndEvent` 没有工具名，名称只在 `ToolCallStartEvent.tool_call_name`。工作流在 `run_workflow` 里持有执行者与验收者两个 `Agent`，模型名在 `agent.model.model`。

动机见 proposal.md 的 Why。行内容见 `specs/agent-events-show/spec.md`。

## Goals / Non-Goals

**Goals:**

- 时间线只通过 loguru 写入 `logs/agent_events.log`，行内时间由代码按上海时区格式化。
- 调用点传入「角色名 → 模型名」，供「开始」行使用；模型调用开始后改记事件上的模型名。
- 定向单测改为断言日志行，并确认这些行不进标准输出。

**Non-Goals:**

- 不改 `dump`、异常提示、用例标题这些仍用 `print` 的汇总。
- 不改对话稿与平台过程日志的文件和字段。
- 不把 `messages` 去 import 角色模块。

## Decisions

**D1：用 loguru，并把依赖写进 `requirements.txt`。**

确认过的草稿就是 loguru。标准库 `logging` 也能打出同样三列，但会推翻已确认的写法。登记 `loguru>=0.7`，避免测试环境未安装时导入失败。

sink 只安装一次。格式用 `{message}`，因为 loguru 的 `{time}` 取本地时区，不能保证是上海。整行（含时间）由展示代码拼好再写入。用 `channel=agent_events` 过滤，避免和其它 sink 混写。

默认的 stderr sink 没有这层过滤，同一条还会再打一遍且格式不对。首次安装时卸下 0 号 sink，再装回一个排除该 channel 的 stderr。0 号已被拆掉时跳过，不因此失败。

**D2：`show(event, buf, models=None)`。**

`models` 是角色名到模型名的映射，由 `run_workflow` 用两个 Agent 的 `name` 与 `model.model` 现拼现传。展示模块不 import `role.agents`，以免单测带上工具包和密钥。缺映射或缺少模型名时写 `-`。

**D3：轮次状态放在调用方持有的 `buf` 里。**

发言开始时先 `clear`，再写入本轮模型名与 `time.monotonic()` 起点。模型调用开始只更新模型名，不另记「开始」。工具名在调用开始时按 `tool_call_id` 暂存，入参结束时取出。图片在数据增量里只记媒体类型和 base64 长度，返回结束时附到同一条「工具返回」。正文块仍把碎片弹出以免缓冲膨胀，但不写日志。步骤边界与未识别类型直接返回，不再打印类型名。

**D4：耗时用 monotonic，不用墙钟相减。**

「本轮执行时间」是起点到发言结束的秒数，格式 `x.xxx秒`。没有起点时明细为 `-`。墙钟回拨不会把耗时打成负数。

**D5：模型调用结束写两行，费用复用 `DeepSeekBilling`。**

`ModelCallEndEvent` 用 `ReplyStreamParser.tokens` 取输入、输出、缓存命中。同一事件再调 `DeepSeekBilling.cost`，模型名用本轮已记下的名字，时刻用事件的 `created_at`（解析失败或缺字段时传 `None`，按空闲时段，不用「现在」，避免单测随钟点变化）。两行动作分别是 `模型token：输入，输出，缓存` 与 `模型费用：输入费用，输出费用，缓存费用`。token 写成百万并带 `M`（6 位小数），费用带 `元`（4 位小数）。同一次发言里的各次调用累加在 `buf`，发言结束、写完耗时后另写两行「本轮执行总计量」。未登记模型的三项费用为 `0.0000元`，token 行仍按 M 写实际用量。

**D6：单测用额外 sink 截获同一 channel 的消息。**

不读日志文件做断言，避免和历史追加内容缠在一起。同时用 `capsys` 确认时间线没有再 `print`。

## 模块防火墙自检

- 不涉及 `apps/`，没有跨 App import，没有 ORM 写，没有前端。
- 改动停在 `engines/agents/messaging/messages.py`、`engines/agents/workflow/ui_auto_workflow.py`、对应单测和 `requirements.txt`。
- 展示模块不依赖角色模块；模型名由工作流在调用时传入。

## Risks / Trade-offs

- [卸下 loguru 默认 stderr sink 会影响同进程里其它 loguru 调用] → 仓库里只有这一处使用 loguru；安装只做一次，并把 stderr 装回，仅排除本 channel。
- [思考、入参、返回都全文写入，单行可能很长] → 按确认的口径不截断文本；图片 base64 仍只记媒体类型与长度。
- [「开始」的模型名来自 Agent 配置，可能和稍后事件上的名字不同] → 开始行用配置名，调用开始之后的行改用事件名，两段都如实记录。
