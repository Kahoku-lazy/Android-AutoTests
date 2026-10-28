## REMOVED Requirements

### Requirement: AI assistant sits under dashboard
**Reason**: 侧栏新增「AI 功能」分组，把「AI 助手」与「知识库助手」放在同一组；「AI 助手」不再紧贴「仪表盘」。
**Migration**: 由本变更新增的「AI 功能分组紧随仪表盘」需求承接：分组整体位于「仪表盘」之后，「数据」之前。

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Duplicate AI assistant group label is absent
系统 MUST NOT 在同一侧栏中重复渲染「AI 功能」分组标题，MUST NOT 渲染仅含「AI 助手」或「知识库助手」文案的伪分组标题。两个入口 MUST 只作为「AI 功能」分组的子项出现，父项文案 MUST 保留为「AI 助手」与「知识库助手」。

#### Scenario: No group heading AI助手

- **WHEN** 用户查看展开态侧栏
- **THEN** 「AI 功能」文案只作为该分组的标题出现一次
- **AND** 不存在第二个仅含「AI 助手」或「知识库助手」文案的分组标题节点
