## MODIFIED Requirements

### Requirement: 只重发这一种未执行的 400

openai 与 deepseek 通道 SHALL 只在接口返回文案含 `Thinking mode does not support this tool_choice` 时重发。其它 400、超时、连接失败 MUST NOT 重发。流已经开始返回内容后 MUST NOT 重发。同一次模型调用最多重发一次。第二次仍是这句 400 时，错误 MUST 原样抛出，由任务收口记为失败。dashscope 通道 MUST NOT 套用本规则。

#### Scenario: 普通 400 不重发

- **WHEN** openai 或 deepseek 模型收到与思考模式无关的 400
- **THEN** 请求只发出一次
- **AND** 错误原样抛出

#### Scenario: 其它通道不重发

- **WHEN** dashscope 模型收到同一句 400
- **THEN** 请求只发出一次

#### Scenario: deepseek 通道交卷轮被拒后重发一次

- **WHEN** deepseek 模型在强制选择 `GenerateStructuredOutput` 的请求上收到这句 400
- **THEN** 第一次重发关闭思考，仍强制同一个工具，工具清单不变
- **AND** 若这次重发仍是同一句 400，第二次重发只保留该工具并把选择改为由模型决定，且请求中没有设备工具

### Requirement: 关思考参数经官方扩展点声明

openai 与 deepseek 通道 SHALL 向框架结构化输出策略阶梯声明「关闭思考」的请求参数（`extra_body.thinking.type=disabled`）。当策略阶梯进入关思考档位时，发出的请求 MUST 携带该参数。本需求不改变既有重发规则：只重发含指定文案的未执行 400、同一次调用最多重发一次、普通工具调用不重发、交结论时保持结构化输出、强制设备工具不得改点、禁止调用工具的轮次保持禁止——全部继续生效。

#### Scenario: 策略阶梯关思考档携带参数

- **WHEN** openai 或 deepseek 模型经框架结构化输出策略阶梯进入关思考档位
- **THEN** 该档请求携带 `extra_body.thinking.type=disabled`

#### Scenario: 既有重发规则不变

- **WHEN** openai 或 deepseek 模型收到与思考模式无关的 400
- **THEN** 请求只发出一次，错误原样抛出，不因新增扩展点而重发
