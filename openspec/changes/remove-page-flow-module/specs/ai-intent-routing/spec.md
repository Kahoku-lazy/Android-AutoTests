## MODIFIED Requirements

### Requirement: 智能体按用户输入做意图分类

系统 SHALL 在每次对话回复前，用大语言模型对用户输入做意图分类，归类为 `phone_control`（控制手机）、`test_case`（平台用例）、`other`（其它）三类之一，并给出置信度。页面流工作台已退役，MUST NOT 再保留指向它的 `workflow` 意图类别。

#### Scenario: 识别控制手机意图

- **WHEN** 用户输入"点击涂鸦"、"打开APP"或"打开APP找到H705F点击进入详情页"
- **THEN** 系统将其分类为 `phone_control`，且多步操作仍归为单个 `phone_control` 意图

#### Scenario: 识别工作流意图

<!-- 场景名沿自变更前：workflow 意图类别已随页面流模块退役，本场景改为守住「不再归入已退役类别」 -->

- **WHEN** 用户输入"新建页面流，抓取当前页面元素并保存"或"把页面跳转关系画成工作流"
- **THEN** 系统 MUST NOT 将其分类为已退役的 `workflow` 类别（归入 `other` 或先澄清）

#### Scenario: 识别平台用例意图

- **WHEN** 用户输入"测试制冰机的开关功能"、"执行H705F相关用例"或"测试打开APP功能"
- **THEN** 系统将其分类为 `test_case`（"测试/执行/查询用例"优先于操作词）

#### Scenario: 识别其它意图

- **WHEN** 用户输入普通闲聊或无法归类的内容
- **THEN** 系统将其分类为 `other`

### Requirement: 按意图路由执行模型

系统 SHALL 按分类结果选择执行模型：`phone_control` 使用视觉模型，`test_case` 与 `other` 使用文本大语言模型。

#### Scenario: 视觉类意图使用视觉模型

- **WHEN** 分类结果为 `phone_control`
- **THEN** 系统使用视觉模型执行，截图等图片输入可被模型读取

#### Scenario: 文本类意图使用文本模型

- **WHEN** 分类结果为 `test_case` 或 `other`
- **THEN** 系统使用文本大语言模型执行
