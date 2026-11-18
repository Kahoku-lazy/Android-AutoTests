# Delta: frontend-sidebar-nav

## ADDED Requirements

### Requirement: AI任务分组提供测试报告入口

侧栏「AI任务」分组 MUST 在「BUG单管理」之后提供「测试报告」入口，路径 MUST 为 `/reports`，即分组四项依次为「任务清单」「用例管理」「BUG单管理」「测试报告」。该入口 MUST 与现有导航项同样支持展开态与折叠态，折叠态 MUST 保留可识别的报告图标与可点击能力。测试报告 MUST 使用独立模块色（`--c-report`），MUST NOT 与同分组的任务清单、用例管理、BUG单管理同色。图标名 MUST 在图标运行时子集里可解析。

#### Scenario: 展开态显示测试报告

- **WHEN** 已登录用户打开带侧栏的工作台页面且侧栏展开
- **THEN** 「AI任务」分组内自上而下依次为「任务清单」「用例管理」「BUG单管理」「测试报告」
- **AND** 点击「测试报告」进入 `/reports`

#### Scenario: 折叠态保留入口

- **WHEN** 用户收起侧栏
- **THEN** 「测试报告」仍以图标项存在且可点击
- **AND** 不因折叠丢失该入口

#### Scenario: 激活态与模块色独立

- **WHEN** 用户位于 `/reports`
- **THEN** 只有「测试报告」显示激活态，高亮色取自 `--c-report`
- **AND** 与「任务清单」「用例管理」「BUG单管理」的高亮色互不相同

## MODIFIED Requirements

### Requirement: AI任务分组提供 BUG 单管理入口

侧栏「AI任务」分组 MUST 在「任务清单」「用例管理」之后提供「BUG单管理」入口，路径 MUST 为 `/bugs`，「测试报告」入口排在其后。该入口 MUST 与现有导航项同样支持展开态与折叠态，折叠态 MUST 保留可识别的 BUG 图标与可点击能力。BUG 单管理 MUST 使用独立模块色，MUST NOT 复用测试报告或任务清单的模块色。

#### Scenario: 展开态显示 BUG 单管理
- **WHEN** 已登录用户打开带侧栏的工作台页面且侧栏展开
- **THEN** 「AI任务」分组内依次出现「任务清单」「用例管理」「BUG单管理」「测试报告」
- **AND** 点击「BUG单管理」进入 `/bugs`

#### Scenario: 折叠态保留入口
- **WHEN** 用户收起侧栏
- **THEN** 「BUG单管理」仍以图标项存在且可点击
- **AND** 不因折叠丢失该入口
