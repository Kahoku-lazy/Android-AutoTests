## 1. 依赖与单测

- [x] 1.1 在 `requirements.txt` 的 AgentScope 一段登记 `loguru>=0.7`。验证：该文件能看到这一行，且 `python -c "import loguru"` 成功。
- [x] 1.2 改写 `tests/graybox/unit/test_agent_events_show.py`：用假事件走完一轮，断言日志行含开始（模型 `deepseek-flash`、角色名）、思考合成、工具调用入参全文（320 字全部在行内）、工具返回全文（420 字全部在行内）、图片只含媒体类型与长度且不含 base64 正文、`模型token：2000000，100000，500000`、`模型费用：1.5000，0.4000，0.0100`（`deepseek-flash`、空闲时段）、结束原因、`本轮执行时间` 为三位小数加「秒」；模型调用开始之后的行改用事件上的模型名且没有第二条开始；未识别事件与步骤边界不产生行；标准输出没有这些时间线。验证：在改 `AgentEventsShow` 之前，`python -m pytest tests/graybox/unit/test_agent_events_show.py -q` 失败。

## 2. 时间线改写日志

- [x] 2.1 重写 `engines/agents/messaging/messages.py` 的 `AgentEventsShow`：去掉文件底部每次导入都 `logger.add` 的草稿；loguru 只安装一次，写入 `logs/agent_events.log`，格式为消息本身，并用 `channel=agent_events` 与排除该 channel 的 stderr 避免重复输出。`show(event, buf, models=None)` 按规格写八个动作；模型调用结束时用现有 DeepSeek 计费写「模型token」与「模型费用」两行，时刻取事件上的 `created_at`，缺失时按空闲时段；发言开始清空缓冲并记下角色模型名与 monotonic 起点；模型调用开始只更新模型名；工具名在调用开始暂存；正文块只弹出缓冲；步骤边界与未识别类型不写日志。验证：同一条 pytest 通过。
- [x] 2.2 `engines/agents/workflow/ui_auto_workflow.py` 的 `run_workflow` 用执行者与验收者的 `name` 和 `model.model` 组成映射，传给 `AgentEventsShow.show`。不改 `dump` 与 `__main__` 里的 `print`。验证：调用处能看到该映射；`dump` 仍使用 `print`。

## 3. 静态检查

- [x] 3.1 对改动文件做静态检查。验证：`ruff check engines/agents/messaging/messages.py engines/agents/workflow/ui_auto_workflow.py tests/graybox/unit/test_agent_events_show.py` 通过。不跑全量回归。

## 4. 本轮总计量与单位

- [x] 4.1 单次「模型token」用 M（6 位小数），「模型费用」用元（4 位小数）。发言结束、写完耗时后追加两行「本轮执行总计量」，分别是本轮各次调用的 token 合计与费用合计。验证：`python -m pytest tests/graybox/unit/test_agent_events_show.py -q` 通过，且 `python -m ruff check engines/agents/messaging/messages.py tests/graybox/unit/test_agent_events_show.py` 通过。

## 5. 共用事件日志

- [x] 5.1 把写 `logs/agent_events.log` 的实现抽到 `engines/agents/event_log.py` 的 `write_line`。`AgentEventsShow` 与 `AgentSOPWorkflow` 的步骤汇总、运行阶段、事件流异常都调用它，不再 `print`。验证：`python -m pytest tests/graybox/unit/test_agent_events_show.py -q` 通过，且 `python -m ruff check engines/agents/event_log.py engines/agents/messaging/messages.py engines/agents/workflow/ui_auto_workflow.py tests/graybox/unit/test_agent_events_show.py` 通过。
