## MODIFIED Requirements

### Requirement: 数据分组提供串口日志入口

系统 SHALL 在侧栏「数据」分组末尾（「页面流」之后）提供「串口日志」入口，路由 MUST 为 `/serial-log`，页面标题 MUST 为「串口日志」。直接访问或刷新该路径 MUST 直接进入该页面；未登录访问 MUST 先跳转登录。该入口 MUST NOT 放进「AI 助手」子项，也 MUST NOT 放进「AI任务」分组。

#### Scenario: 侧栏顺序

- **WHEN** 用户展开侧栏查看「数据」分组
- **THEN** 依次看到「设备管理 / 页面流 / 串口日志」，串口日志在页面流之后

#### Scenario: 直接访问

- **WHEN** 已登录用户直接打开 `/serial-log`
- **THEN** 进入串口日志页面，页面标题为「串口日志」

#### Scenario: 未登录被拦截

- **WHEN** 未登录用户打开 `/serial-log`
- **THEN** 跳转到登录页，登录成功后不进入串口日志以外的页面

#### Scenario: 不再挂在 AI 助手下

- **WHEN** 用户展开侧栏的「AI 助手」子项
- **THEN** 子项只有「平台小助手」与「AI工具箱」，不出现串口日志
