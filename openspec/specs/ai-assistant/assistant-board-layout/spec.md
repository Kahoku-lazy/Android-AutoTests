# ai-assistant/assistant-board-layout Specification

## Purpose
约定平台小助手页的看板不套章节白底外框：线路卡直接置于页面背景，页面层级只由页头与卡片自身表达，并以固定的可读宽度展示。

## Requirements

### Requirement: Assistant card sits directly on the page

平台小助手页 SHALL 把助手线路卡直接放在页面背景上，MUST NOT 使用 `.doc-section` 的白色底、描边、阴影外框，MUST NOT 再渲染「平台小助手 / Assistant / N 个助手」区块标题行。页面页头「平台小助手」MUST 保留。

#### Scenario: Page shows the card without a section frame

- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 线路卡直接显示在页面背景上，卡片外不存在白色区块外框
- **AND** 页面不出现重复的「平台小助手」区块标题行或「N 个助手」计数

### Requirement: Assistant card uses a readable fixed width

线路卡在桌面视口 MUST 使用约 300–320px 的固定宽度，MUST NOT 被拉伸到整行。卡片 MUST 采用「左侧头像 + 右侧三行」布局：头像 MUST 为约 120px 的正方形；右侧列 MUST 约 140–150px 宽、约 120px 高，自上而下 MUST 依次为名称、职责、配置按钮，三行 MUST 纵向均匀分布。名称/职责字号 MUST 收敛到能完整放进右列（约 18px / 15px），配置按钮 MUST 与名称/职责同列、不得再占用卡片底部整行。窄屏下右列与字号 MUST 降档到 120px / 15px / 13px，卡片 MUST 收缩到容器宽度，MUST NOT 横向溢出。

#### Scenario: Wide viewport keeps a compact card

- **WHEN** 用户在桌面宽度打开平台小助手页
- **THEN** 线路卡宽度落在 300–320px 之间，头像约 120px，右侧自上而下为名称、职责、配置三行

#### Scenario: Narrow viewport shrinks the card

- **WHEN** 视口宽度小于 720px
- **THEN** 线路卡收缩到容器宽度，右列保持约 120px，页面不出现横向滚动
