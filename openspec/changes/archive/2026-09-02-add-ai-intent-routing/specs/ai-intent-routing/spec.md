## Purpose

让 AI 智能体在对话中自动识别用户输入属于「控制手机 / 工作流工作台 / 平台用例 / 其它」四类意图之一，并据此选择视觉模型或文本模型、以及对应的工具集执行。

## ADDED Requirements

### Requirement: 智能体按用户输入做意图分类

系统 SHALL 在每次对话回复前，用大语言模型对用户输入做意图分类，归类为 `phone_control`（控制手机）、`workflow`（工作流工作台）、`test_case`（平台用例）、`other`（其它）四类之一，并给出置信度。

#### Scenario: 识别控制手机意图

- **WHEN** 用户输入"点击涂鸦"、"打开APP"或"打开APP找到H705F点击进入详情页"
- **THEN** 系统将其分类为 `phone_control`，且多步操作仍归为单个 `phone_control` 意图

#### Scenario: 识别工作流意图

- **WHEN** 用户输入"新建页面流，抓取当前页面元素并保存"或"把页面跳转关系画成工作流"
- **THEN** 系统将其分类为 `workflow`

#### Scenario: 识别平台用例意图

- **WHEN** 用户输入"测试制冰机的开关功能"、"执行H705F相关用例"或"测试打开APP功能"
- **THEN** 系统将其分类为 `test_case`（"测试/执行/查询用例"优先于操作词）

#### Scenario: 识别其它意图

- **WHEN** 用户输入普通闲聊或无法归类的内容
- **THEN** 系统将其分类为 `other`

### Requirement: 按意图路由执行模型

系统 SHALL 按分类结果选择执行模型：`phone_control` 与 `workflow` 使用视觉模型，`test_case` 与 `other` 使用文本大语言模型。

#### Scenario: 视觉类意图使用视觉模型

- **WHEN** 分类结果为 `phone_control` 或 `workflow`
- **THEN** 系统使用视觉模型执行，截图等图片输入可被模型读取

#### Scenario: 文本类意图使用文本模型

- **WHEN** 分类结果为 `test_case` 或 `other`
- **THEN** 系统使用文本大语言模型执行

### Requirement: 按意图裁剪工具集

系统 SHALL 按分类结果只装配该意图相关的工具子集，且 `other` 意图不装配任何业务工具。

#### Scenario: 其它意图不挂工具

- **WHEN** 分类结果为 `other`
- **THEN** 系统以纯对话方式回复，不调用任何平台业务工具

#### Scenario: 控制手机意图只挂设备工具

- **WHEN** 分类结果为 `phone_control`
- **THEN** 系统仅装配设备控制与截图相关工具，不装配用例/工作流工具

### Requirement: 低置信度时澄清而非执行

系统 SHALL 在分类置信度低于阈值时反问用户澄清意图，不直接路由执行。

#### Scenario: 模糊输入触发澄清

- **WHEN** 分类结果置信度低于配置阈值
- **THEN** 系统向用户追问意图，等待用户确认后再执行

### Requirement: 视觉模型可配置且可降级

系统 SHALL 支持为智能体配置视觉模型；当智能体未配置视觉模型时，视觉类意图回退为文本模型执行且不报错。

#### Scenario: 未配置视觉模型时降级

- **WHEN** 分类为视觉类意图但智能体未配置视觉模型
- **THEN** 系统回退使用文本模型执行，对话不中断、不报错
