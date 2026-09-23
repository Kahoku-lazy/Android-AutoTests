## Purpose

约定智能体看板线路卡的身份信息架构：左侧头像、右侧三行（名称、职责、助手状态），底部保留校验与配置操作。职责与连通探测协议无关，只约束卡片可见结构与文案位置。

## ADDED Requirements

### Requirement: Route card identity is avatar plus three lines

智能体看板的线路卡片 SHALL 按「左头像、右三行」展示身份，MUST NOT 再使用独立的功能标题带（例如卡片顶部单独一行「控制设备」）。

右侧三行 MUST 依次为：

1. 助手名称（线路配置名，缺省回落智能体名；再缺省为「未命名助手」）
2. 职责行，控制设备线路固定文案「职责：UI自动化」
3. 助手状态行，文案 MUST 与 `ai-route-connectivity` 的三态及过程态一致（`ready` / `unusable` / `offline` / 校验中）

头像 MUST 为正方形，其边长 MUST 等于右侧三行文字块的自然总高度（三行数据与头像宽度一致）。状态行过长时 MUST 在身份区内换行或截断，MUST NOT 撑破卡片水平边界。

#### Scenario: Device-control card shows name duty and status

- **WHEN** 用户打开 `/ai-assistant/agents` 且存在控制设备线路配置（名称为「测试助手」、连通为 `ready`）
- **THEN** 卡片左侧显示头像，右侧第一行为「测试助手」，第二行为「职责：UI自动化」，第三行为「已连通，可执行任务」，且卡片内不出现独立功能标题「控制设备」

#### Scenario: Avatar height matches three-line block

- **WHEN** 线路卡完成渲染
- **THEN** 头像为正方形，其宽度与右侧三行文字块的总高度相同（允许 1px 级布局舍入）

### Requirement: Route card keeps inspect and configure actions at the bottom

线路卡片底部 SHALL 保留「校验」与「配置」两个按键（仅具备管理权限时可见）。点击行为 MUST 与现网一致：校验触发该线路连通探测，配置打开该线路配置界面。MUST NOT 把这两个按键移入头像右侧三行区内。

#### Scenario: Admin sees inspect and configure under identity

- **WHEN** 超级管理员查看智能体看板线路卡
- **THEN** 「校验」与「配置」出现在身份区（头像+三行）下方，不出现在头像右侧

#### Scenario: Non-admin does not see manage actions

- **WHEN** 非超级管理员查看智能体看板线路卡
- **THEN** 卡片仍展示头像与三行身份信息，MUST NOT 展示「校验」或「配置」
