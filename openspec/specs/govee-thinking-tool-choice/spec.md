# openai-thinking-tool-choice Specification

## Purpose

约束 OpenAI 网关在思考模式拒绝强制选工具时只重发一次，并且重发不得改点设备、不得在收尾轮再点一次。

## Requirements

### Requirement: 只重发这一种未执行的 400

openai 通道 SHALL 只在网关返回文案含 `Thinking mode does not support this tool_choice` 时重发。其它 400、超时、连接失败 MUST NOT 重发。流已经开始返回内容后 MUST NOT 重发。同一次模型调用最多重发一次。第二次仍是这句 400 时，错误 MUST 原样抛出，由任务收口记为失败。deepseek 与 dashscope 通道 MUST NOT 套用本规则。

#### Scenario: 普通 400 不重发

- **WHEN** openai 模型收到与思考模式无关的 400
- **THEN** 请求只发出一次
- **AND** 错误原样抛出

#### Scenario: 其它通道不重发

- **WHEN** deepseek 或 dashscope 模型收到同一句 400
- **THEN** 请求只发出一次

### Requirement: 没强制工具的请求不重发

没有强制 `tool_choice` 的请求 MUST NOT 因这句 400 重发。截图、点击、滑动等已经由模型自行选择的设备动作，不得因为重发再执行一次。

#### Scenario: 普通工具调用不重发

- **WHEN** openai 模型本次请求没有强制选择工具，却收到这句 400
- **THEN** 请求只发出一次

### Requirement: 交结论时保持结构化输出

强制选择 `GenerateStructuredOutput` 时，第一次重发 MUST 关闭思考并保持强制该工具。若这次重发仍返回同一句 400，第二次重发 MUST 只保留该工具，并把选择改为由模型决定。重发后的请求 MUST NOT 再带上设备工具。

#### Scenario: 关思考后仍被拒绝

- **WHEN** 交结论请求第一次被这句 400 拒绝，关闭思考后再次被同一句拒绝
- **THEN** 下一次请求只包含 `GenerateStructuredOutput`
- **AND** 不再强制指定工具名
- **AND** 请求中没有设备工具

### Requirement: 强制设备工具不得改点

强制选择某个设备工具时，重发 MUST 只关闭思考，工具名 MUST 保持不变。系统 MUST NOT 把这次请求改成由模型自行选择工具。

#### Scenario: 强制点击不被改成自由选择

- **WHEN** 请求强制选择某个设备点击工具，并收到这句 400
- **THEN** 重发仍强制同一个工具
- **AND** 思考被关闭

### Requirement: 禁止调用工具的轮次保持禁止

`tool_choice` 为禁止调用工具时，重发 MUST 只关闭思考，并 MUST 继续禁止调用工具。系统 MUST NOT 把这次请求改成允许调用工具。

#### Scenario: 收尾轮不再点设备

- **WHEN** 请求禁止调用任何工具，并收到这句 400
- **THEN** 重发仍然禁止调用工具
- **AND** 思考被关闭

### Requirement: 关思考参数经官方扩展点声明

openai 通道 SHALL 向框架结构化输出策略阶梯声明「关闭思考」的请求参数（`extra_body.thinking.type=disabled`）。当策略阶梯进入关思考档位时，发出的请求 MUST 携带该参数。本需求不改变既有重发规则：只重发含指定文案的未执行 400、同一次调用最多重发一次、普通工具调用不重发、交结论时保持结构化输出、强制设备工具不得改点、禁止调用工具的轮次保持禁止——全部继续生效。

#### Scenario: 策略阶梯关思考档携带参数

- **WHEN** openai 模型经框架结构化输出策略阶梯进入关思考档位
- **THEN** 该档请求携带 `extra_body.thinking.type=disabled`

#### Scenario: 既有重发规则不变

- **WHEN** openai 模型收到与思考模式无关的 400
- **THEN** 请求只发出一次，错误原样抛出，不因新增扩展点而重发
