## MODIFIED Requirements

### Requirement: Assistant card uses a readable fixed width

线路卡在桌面视口 MUST 使用约 560–620px 的固定宽度，MUST NOT 被拉伸到整行。头像 MUST 为正方形，边长约为右侧文字区自然高度的 96px 级别（相对上一版约 48px 放大一倍）；名称、职责的字号与行距、身份区间距、卡片内边距、配置按钮的高度/字号/内边距 MUST 随头像同步放大，保持原有比例。窄屏下线路卡 MUST 收缩到容器宽度，MUST NOT 横向溢出。

#### Scenario: Wide viewport keeps a compact card

- **WHEN** 用户在桌面宽度打开平台小助手页
- **THEN** 线路卡宽度落在 560–620px 之间，头像边长约 96px，名称、职责与配置按钮明显大于上一版且比例协调

#### Scenario: Narrow viewport shrinks the card

- **WHEN** 视口宽度小于卡片固定宽度
- **THEN** 线路卡收缩到容器宽度，页面不出现横向滚动
