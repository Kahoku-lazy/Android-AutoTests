## Context

govee 通道现在直接建 `OpenAIChatModel`。交结论时 AgentScope 把 `tool_choice` 设成必须调用 `GenerateStructuredOutput`，Govee 网关在思考模式开启时返回 400，请求还没执行。普通截图和点击没有强制选工具，日志里都是 200。动机见 `proposal.md`。

观测中间件禁止改 `tool_choice`。AgentScope 的结构化输出降级只在专用接口里，普通推理没有。本目录不能新增自定义异常。

## Goals / Non-Goals

**Goals:**

- 只在 govee 的模型调用上，对未执行的这句 400 按请求类型重发一次。
- 交结论最终只能交出结构化结果，不能改去点设备。
- 强制设备工具和禁止调用工具的轮次，重发后语义不变。

**Non-Goals:**

- 不关全局思考，不改提示词，不改 AgentScope。
- 不重试超时、断连、其它 400。
- 不改任务状态和失败分类。第二次仍失败，继续走现有 `failed` / `provider` 收口。
- 不处理已经开始吐流之后的失败。

## Decisions

**D1 包装只放在 govee 分支。** `create_model` 在 `provider=govee` 时，用一个只覆盖 `_call_api` 的子类包住 `OpenAIChatModel`。deepseek、dashscope 仍用原类。备选是在 Agent 中间件里改请求：观测层禁止改 `tool_choice`。否决。

**D2 先看请求，再决定能不能重发。** 识别这句 400 后：

| 本次 `tool_choice` | 重发 |
| --- | --- |
| 空 / `auto` | 不重发 |
| 工具名是 `GenerateStructuredOutput` | 第一次重发：`extra_body.thinking.type=disabled`，工具名不变。若这次仍是同一句 400，第二次请求把工具列表收成只有该工具，`tool_choice` 改为 `auto` |
| 其它工具名 | 只关思考，工具名不变。不再改成 `auto` |
| `none` | 只关思考，保持 `none` |

交结论允许两次请求调整，因为第一次调整仍可能被网关拒绝。其它类型只调整一次。总请求次数有上限，避免循环。

**D3 关思考用请求参数，不改模型默认。** 重发时在当次 kwargs 里写 `extra_body.thinking.type=disabled`，不改模型实例的默认思考开关。这样只有被拒绝的那一次关掉。备选是创建模型时就关思考：会丢掉正常轮次的思考，而且网关未必认这个字段。否决。

**D4 流开始后不重发。** 只在 `_call_api` 抛出 400、还没得到流对象时重发。若调用已经返回异步生成器，后续 chunk 失败不再重发。这样不会把已经执行的设备动作再发一次。

**D5 用假网关测四段，不打真设备。** 单测注入一个按调用次数返回 400 或成功的假客户端，断言每次发出的 `tool_choice`、工具列表和 `extra_body`。不连 `test-llm.lanjingerp.com`，不调用 adb。

## 模块防火墙自检

- 改动只在 `engines/ae_harness/agents/models.py`，不碰 `backend/apps`。
- 不新增跨 App import，不写库，不新增自定义异常。
- 前端和任务收口不改。

## Risks / Trade-offs

- [网关不认 `thinking.type=disabled`] → 交结论还有第二次：只留结构化工具并改成 `auto`。设备工具和 `none` 不再降级，第二次失败就抛出。
- [交结论第二次模型仍不调用该工具] → SOP 会把这一步记为没交接。工具列表里已经没有设备工具，不会因此再点手机。
- [400 文案改写] → 只认当前这句。文案变了就不再重发，行为退回今天的失败，不会误重试。
