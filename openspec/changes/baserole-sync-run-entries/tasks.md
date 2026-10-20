## 1. 同步入口

- [x] 1.1 在 `engines/agents/role/base.py` 去掉 `messaging` 导入。`user_reply` 保持 `asyncio.run(self.agent.reply(...))` 并返回最终消息，方法内不打印、不解析。`user_reply_stream` 改为 `asyncio.run` 里用默认 `ConsoleRenderer` 消费 `self.agent.reply_stream(...)`，不读取 `last_msg`，返回 `None`。两个方法的 docstring 写明返回值，并在 `Raises` 中写明：已在运行的事件循环内调用时 `asyncio.run` 抛出 `RuntimeError`。验证：`rg "render_reply_stream|messaging" engines/agents/role/base.py` 无匹配，且 `ruff check engines/agents/role/base.py` 通过。

## 2. 调试块与测试

- [x] 2.1 新增 `tests/graybox/unit/test_agent_role_run.py`。用替身替换已构造角色上的 `agent`：`user_reply` 返回该最终消息，且标准输出没有这条正文；`user_reply_stream` 返回 `None`，并把 `reply_stream` 的事件交给渲染器。验证：`python -m pytest tests/graybox/unit/test_agent_role_run.py -q` 通过。
- [x] 2.2 不修改 `engines/agents/role/base.py` 里 `if __name__ == "__main__":` 及其后的任何字符。验证：实施前后这一段文本一致（diff 在该行之后没有改动）。

## 3. 上屏同时落对话稿并返回消息

- [x] 3.1 `user_reply_stream` 用 `reply_stream(..., yield_final_msg=True)`。事件打印到控制台并写入 `DialogueLog`；流末尾的 `Msg` 不打印、不落稿，作为返回值。验证：`python -m pytest tests/graybox/unit/test_agent_role_run.py -q` 通过，且 `__main__` 块仍未改动。
