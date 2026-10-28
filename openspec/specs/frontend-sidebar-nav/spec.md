## Purpose

定义侧栏导航入口的分组顺序与分组标题可见性：仪表盘之后紧跟「AI 功能」分组（AI 助手 / 知识库助手），且不出现重复或伪分组标题。

## Requirements

### Requirement: Duplicate AI assistant group label is absent
系统 MUST NOT 在同一侧栏中重复渲染「AI 功能」分组标题，MUST NOT 渲染仅含「AI 助手」或「知识库助手」文案的伪分组标题。两个入口 MUST 只作为「AI 功能」分组的子项出现，父项文案 MUST 保留为「AI 助手」与「知识库助手」。

#### Scenario: No group heading AI助手

- **WHEN** 用户查看展开态侧栏
- **THEN** 「AI 功能」文案只作为该分组的标题出现一次
- **AND** 不存在第二个仅含「AI 助手」或「知识库助手」文案的分组标题节点

### Requirement: AI 功能分组紧随仪表盘

侧栏 SHALL 在「仪表盘」之后、「数据」之前渲染「AI 功能」分组，分组标题文案 MUST 为「AI 功能」。该分组 MUST 恰含两项，顺序 MUST 为「AI 助手」在前、「知识库助手」在后；两项路径分别 MUST 为 `/ai-assistant` 与 `/knowledge-assistant`。系统 MUST NOT 在「仪表盘」与「AI 功能」分组之间插入其它导航项。

#### Scenario: 展开态侧栏顺序

- **WHEN** 已登录用户打开带侧栏的工作台页面且侧栏展开
- **THEN** 「仪表盘」之后是分组标题「AI 功能」
- **AND** 该分组内先出现「AI 助手」，再出现「知识库助手」
- **AND** 「AI 功能」分组之后才是「数据」分组

#### Scenario: 知识库助手可直达语音页

- **WHEN** 用户点击侧栏「知识库助手」
- **THEN** 路由进入 `/knowledge-assistant`
- **AND** 页面出现语音按键与对话记录区

#### Scenario: 折叠态仍可识别两个入口

- **WHEN** 侧栏折叠后用户查看「AI 功能」分组
- **THEN** 「AI 助手」与「知识库助手」仍以图标项存在并可点击
- **AND** 不因折叠而丢失任一项

### Requirement: AI任务分组提供 BUG 单管理入口

侧栏「AI任务」分组 MUST 在「任务清单」「用例管理」「测试报告」之后提供「BUG单管理」入口，路径 MUST 为 `/bugs`。该入口 MUST 与现有导航项同样支持展开态与折叠态，折叠态 MUST 保留可识别的 BUG 图标与可点击能力。BUG 单管理 MUST 使用独立模块色，MUST NOT 复用测试报告或任务清单的模块色。

#### Scenario: 展开态显示 BUG 单管理
- **WHEN** 已登录用户打开带侧栏的工作台页面且侧栏展开
- **THEN** 「AI任务」分组内依次出现「任务清单」「用例管理」「测试报告」「BUG单管理」
- **AND** 点击「BUG单管理」进入 `/bugs`

#### Scenario: 折叠态保留入口
- **WHEN** 用户收起侧栏
- **THEN** 「BUG单管理」仍以图标项存在且可点击
- **AND** 不因折叠丢失该入口

#### Scenario: BUG 单管理有独立模块色
- **WHEN** 用户位于 `/bugs` 页面
- **THEN** 侧栏高亮色取自 BUG 单管理专属模块色
- **AND** 与 `/tasks`、`/reports` 的高亮色不同
