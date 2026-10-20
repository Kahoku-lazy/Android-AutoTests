## Why

`BaseRole` 是角色基类，只应负责用 AgentScope 配置并跑完一轮智能体。现在流式入口调用了 `messaging.render_reply_stream`，把上屏和「取出最终消息」绑在一起，基类承担了解析层的职责。调试时需要的是：等任务结束后拿到结果，或只在控制台看到过程。

## What Changes

- `user_reply` 保持同步：内部 `asyncio.run(agent.reply(...))`，返回框架最终消息。基类不打印、不解析用量或正文。
- `user_reply_stream` 改为只上屏：用 AgentScope 的 `ConsoleRenderer` 消费 `agent.reply_stream`，方法返回 `None`。**BREAKING**：不再返回最终消息，也不再调用 `render_reply_stream`。
- 基类不再 import `engines.agents.messaging`。
- `if __name__ == "__main__":` 代码块一字不改。

## 关联文档

无关联需求编号。这是角色基类运行入口的职责拆分，不改产品行为。

## Capabilities

### New Capabilities

- `agent-role-run`: 角色基类的两条同步运行入口——返回最终消息，或只把本轮事件打到控制台且不返回结果。

### Modified Capabilities

## Impact

- `engines/agents/role/base.py`：去掉对 `render_reply_stream` 的依赖，改写 `user_reply_stream`。
- 调用方：仓库内只有该文件 `__main__` 调用 `user_reply`（保持可用）；`user_reply_stream` 仅出现在被注释的行，本次不改那些行。
- `messaging.render_reply_stream` 与用量解析保持原样，仍由其它模块负责。
- 不改前端、接口或数据库。
