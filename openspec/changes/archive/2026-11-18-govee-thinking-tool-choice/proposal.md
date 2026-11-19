## Why

17:30 之后的任务在手机上已经截图、点击成功，交结构化结论时 Govee 网关返回 `Thinking mode does not support this tool_choice`。这个 400 发生在请求执行前，却把整单标成失败。一律改成 `auto` 重发会让模型改点设备，或在收尾轮再点一次。

## What Changes

- 只在 `govee` 通道上，对这一句 400 重发一次。其它 400、超时、断连不重发。
- 没强制工具的请求不重发。
- 强制交结论（`GenerateStructuredOutput`）时，先关思考并保持强制；仍是这句 400，就把工具列表收成只有这一个工具，再改成 `auto`。
- 强制某个设备工具时，只关思考，工具名不变，不改成 `auto`。
- `tool_choice=none` 时只关思考，保持禁止调用工具，不改成 `auto`。
- 流已经开始吐出内容后不重发。DeepSeek 官方客户端和 DashScope 不加这层。
- 第二次仍是这句 400 时，按现有收口记为 `failed` / `provider`，不再循环。

## 关联文档

无关联 PRD 编号。口径来自 2026-11-17 对任务 225、226、227、228、229 的日志排查，以及随后确认的四段重发规则。

## Capabilities

### New Capabilities

- `govee-thinking-tool-choice`: Govee 网关在思考模式拒绝强制选工具时，按请求类型只重发一次。

### Modified Capabilities

## Impact

- `engines/ae_harness/agents/models.py`：只包 `govee` 的 `OpenAIChatModel`。
- 测试：`tests/engines/ae_harness/unit/` 覆盖四段重发，以及非 govee 通道不变。
- 不改任务状态口径，不改提示词，不改 AgentScope，不自动重试设备动作。
