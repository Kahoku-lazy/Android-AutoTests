## Context

见 proposal.md 的 Why。当前 `BaseRole.user_reply` 已经是 `asyncio.run(self.agent.reply(...))`，返回最终消息。`user_reply_stream` 现为调用 `messaging.render_reply_stream`，该函数既用 `ConsoleRenderer(verbosity="debug")` 上屏，又返回最后一条消息。`if __name__ == "__main__":` 实际执行的是 `print(role.user_reply(...))`；`user_reply_stream` 只出现在被注释的两行。

调用方要的是「等模型做完再拿结果」，不是自己写 `async`。AgentScope 的 `Agent.reply` / `reply_stream` 是协程，同步入口把事件循环藏在方法内部即可。

## Goals / Non-Goals

**Goals:**

- 返回结果与上屏拆成两个同步方法，基类不解析消息。
- 上屏使用 AgentScope 自带的 `ConsoleRenderer`，不再经过 `messaging`。
- 保持 `user_reply` 的现有调用方式，使未改动的 `__main__` 仍能 `print` 到最终消息。

**Non-Goals:**

- 不把 `reply_stream` 的事件流作为返回值暴露给调用方。
- 不修改、不删除 `render_reply_stream` 及其用量解析。
- 不改 `if __name__ == "__main__":` 的任何字符，包括被注释的 `user_reply_stream` 调用。
- 不恢复已删除的 `interrupt`，不清理与本变更无关的未使用导入或字段。
- 不把入口改成 `async def`。

## Decisions

### D1：两条入口都保持同步，内部使用 `asyncio.run`

返回结果对应「等任务完成再输出」。`Agent.reply` 是协程，用 `asyncio.run` 包住后，调用方仍是普通函数调用。已在运行的事件循环里再调用会由 `asyncio.run` 抛出 `RuntimeError`，两个公开方法的 `Raises` 都要写明这一点。

备选：把两个方法改成 `async def` 直转。调用方必须自备事件循环，和「跑完再拿结果」的调试与业务调用不符，不采用。

### D2：方法名保持 `user_reply` 与 `user_reply_stream`

`user_reply(content) -> Msg`：`return asyncio.run(self.agent.reply(self._user_msg(content)))`。

`user_reply_stream(content) -> Msg`：在 `asyncio.run` 里调用 `self.agent.reply_stream(..., yield_final_msg=True)`。流里的 `Msg` 是最终消息，不打印、不写入对话稿，留到结束时返回。其余事件逐条 `ConsoleRenderer.render`，并写入一份 `DialogueLog`（`logs/agent_logs`）。`ReplyStartEvent` 只调用 `begin_reply`，其余事件交给 `consume`。结束后 `finish`。基类不自己计算用量三元组，费用不传入对话稿。

保留 `user_reply_stream` 这个名字，是因为 `__main__` 里被注释的调用仍然使用它，而该代码块禁止改动。取消注释后 `print` 会打印最终消息。

备选：新名 `user_reply_console` 并删除 `user_reply_stream`。未改动的注释行一旦打开就会 `NameError`，不采用。

### D3：上屏详细程度用框架默认值

`ConsoleRenderer()` 使用其默认 `verbosity="default"`（正文、思考、工具调用与结果）。旧的 `render_reply_stream` 使用 `"debug"`（额外生命周期行）。基类跟随框架默认，不把 debug 行当成基类契约。

备选：继续 `"debug"`，以便和旧调试输出逐行一致。那是 messaging 层的选择，不是框架默认，不采用。

### D4：基类不依赖 messaging

删除 `from ..messaging.messages import render_reply_stream`。上屏只依赖 `agentscope.console.ConsoleRenderer`。用量与正文解析留在 `messaging`，由拿到 `user_reply` 返回值的调用方自己做。

## 模块防火墙自检

- 本变更只改 `engines/agents/role/base.py`，不触碰 `apps/`，没有跨 App import。
- 没有 ORM 写操作，不涉及 `api.py`。
- 前端不参与，没有新的 HTTP 或 WebSocket 出口。
- 新依赖是 AgentScope 已有的 `ConsoleRenderer`，不是项目内跨模块 service。

## Risks / Trade-offs

- [取消注释的 `print(role.user_reply_stream(...))` 会打印 `None`] → 方法契约就是不返回结果；`__main__` 按用户要求不改。需要拿消息时继续用已经在执行的 `user_reply`。
- [上屏从 debug 降到 default，少了「model call / reply end」这类行] → 正文、思考和工具仍会打印。需要 debug 行时由调用方自建 `ConsoleRenderer(verbosity="debug")`，不放进基类。
- [在已有事件循环内调用会 `RuntimeError`] → 文档写进 `Raises`。当前调试脚本与同步业务调用不在该环境里。
