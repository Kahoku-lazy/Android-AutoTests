## REMOVED Requirements

### Requirement: Route card identity is avatar plus three lines

**Reason**: 第三行是连通状态，随校验功能下线；卡片身份区收为两行。
**Migration**: 由新增的「Route card identity is avatar plus two lines」承接。

### Requirement: Route card keeps inspect and configure actions at the bottom

**Reason**: 「校验」按钮已删除，底部只剩「配置」。
**Migration**: 由新增的「Route card keeps configure action at the bottom」承接。

## ADDED Requirements

### Requirement: Route card identity is avatar plus two lines

智能体看板的线路卡片 SHALL 按「左头像、右两行」展示身份，MUST NOT 再使用独立的功能标题带（例如卡片顶部单独一行「控制设备」），也 MUST NOT 展示连通状态徽标。

右侧两行 MUST 依次为：

1. 助手名称（线路配置名，缺省回落智能体名；再缺省为「未命名助手」）
2. 职责行，控制设备线路固定文案「职责：UI自动化」

头像 MUST 为正方形，其边长 MUST 等于右侧两行文字块的自然总高度。

#### Scenario: Device-control card shows name and duty

- **WHEN** 用户打开 `/ai-assistant/agents` 且存在控制设备线路配置（名称为「测试助手」）
- **THEN** 卡片左侧显示头像，右侧第一行为「测试助手」，第二行为「职责：UI自动化」，且卡片内不出现独立功能标题「控制设备」
- **AND** 卡片内不出现任何连通状态文案

#### Scenario: Avatar height matches two-line block

- **WHEN** 线路卡完成渲染
- **THEN** 头像为正方形，其宽度与右侧两行文字块的总高度相同（允许 1px 级布局舍入）

### Requirement: Route card keeps configure action at the bottom

线路卡片底部 SHALL 保留「配置」按键（仅具备管理权限时可见），点击打开该线路配置界面。MUST NOT 提供「校验」按键，MUST NOT 把「配置」移入头像右侧身份区内。

#### Scenario: Admin sees configure under identity

- **WHEN** 超级管理员查看智能体看板线路卡
- **THEN** 「配置」出现在身份区（头像+两行）下方，不出现在头像右侧
- **AND** 卡片上没有「校验」按键

#### Scenario: Non-admin does not see manage actions

- **WHEN** 非超级管理员查看智能体看板线路卡
- **THEN** 卡片仍展示头像与两行身份信息，MUST NOT 展示「配置」
