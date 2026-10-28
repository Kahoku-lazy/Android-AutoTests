## ADDED Requirements

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
