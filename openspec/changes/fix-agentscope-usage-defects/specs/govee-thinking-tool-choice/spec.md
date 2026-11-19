## ADDED Requirements

### Requirement: 关思考参数经官方扩展点声明

govee 通道 SHALL 向框架结构化输出策略阶梯声明「关闭思考」的请求参数（`extra_body.thinking.type=disabled`）。当策略阶梯进入关思考档位时，发出的请求 MUST 携带该参数。本需求不改变既有重发规则：只重发含指定文案的未执行 400、同一次调用最多重发一次、普通工具调用不重发、交结论时保持结构化输出、强制设备工具不得改点、禁止调用工具的轮次保持禁止——全部继续生效。

#### Scenario: 策略阶梯关思考档携带参数

- **WHEN** govee 模型经框架结构化输出策略阶梯进入关思考档位
- **THEN** 该档请求携带 `extra_body.thinking.type=disabled`

#### Scenario: 既有重发规则不变

- **WHEN** govee 模型收到与思考模式无关的 400
- **THEN** 请求只发出一次，错误原样抛出，不因新增扩展点而重发