## MODIFIED Requirements

### Requirement: Assistant card uses a readable fixed width

线路卡在桌面视口 MUST 使用约 300–320px 的固定宽度，MUST NOT 被拉伸到整行。卡片 MUST 采用「左侧头像 + 右侧三行」布局：头像 MUST 为约 120px 的正方形；右侧列 MUST 约 140–150px 宽、约 120px 高，自上而下 MUST 依次为名称、职责、配置按钮，三行 MUST 纵向均匀分布。名称/职责字号 MUST 收敛到能完整放进右列（约 18px / 15px），配置按钮 MUST 与名称/职责同列、不得再占用卡片底部整行。窄屏下右列与字号 MUST 降档到 120px / 15px / 13px，卡片 MUST 收缩到容器宽度，MUST NOT 横向溢出。

#### Scenario: Wide viewport keeps a compact card

- **WHEN** 用户在桌面宽度打开平台小助手页
- **THEN** 线路卡宽度落在 300–320px 之间，头像约 120px，右侧自上而下为名称、职责、配置三行

#### Scenario: Narrow viewport shrinks the card

- **WHEN** 视口宽度小于 720px
- **THEN** 线路卡收缩到容器宽度，右列保持约 120px，页面不出现横向滚动
