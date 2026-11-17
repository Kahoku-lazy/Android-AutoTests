## Purpose

让超级管理员与运营在仪表盘平台概览直接看到用户、Agent 配置和模型配置的数量，同时保证普通用户既看不到卡片，也拿不到这些计数。

## ADDED Requirements

### Requirement: Operator overview counts three configuration sets

系统 SHALL 在仪表盘统计响应中向超级管理员与运营返回 `ops`。`ops.users` MUST 为账号总数，含已停用账号。`ops.agents` MUST 为 Agent 配置总数。`ops.models` MUST 为模型配置总数。三项均为 0 时 MUST 仍返回该对象，MUST NOT 省略字段。响应 MUST NOT 包含密码、密钥、系统提示词或其它凭据。

#### Scenario: 运营拿到三项计数

- **WHEN** 超级管理员或运营请求仪表盘统计接口，且平台有 4 个账号、2 条 Agent 配置、3 条模型配置
- **THEN** 响应含 `ops.users = 4`、`ops.agents = 2`、`ops.models = 3`

#### Scenario: 停用账号仍计入用户数

- **WHEN** 账号中有已停用账号，运营请求仪表盘统计接口
- **THEN** `ops.users` 等于全部账号数，不只计启用账号

#### Scenario: 全零仍返回对象

- **WHEN** 运营请求统计接口且三项都是 0
- **THEN** 响应仍含 `ops`，三项均为 0

### Requirement: Ordinary users do not receive operator counts

普通用户请求仪表盘统计接口时，响应 MUST NOT 含 `ops` 或其任一计数字段。权限判定 MUST 在服务端完成，MUST NOT 只依赖前端隐藏卡片。未登录请求 MUST 保持既有 401，MUST NOT 为了隐藏计数而改成返回空统计。

#### Scenario: 普通用户响应没有运营字段

- **WHEN** 普通用户请求仪表盘统计接口
- **THEN** HTTP 200 的统计响应中不存在 `ops`
- **AND** 不存在用户数、Agent 配置数或模型配置数

#### Scenario: 未登录仍被拒绝

- **WHEN** 未登录请求仪表盘统计接口
- **THEN** HTTP 401
- **AND** 响应不含运营计数

### Requirement: Operator overview renders three entry cards

超级管理员与运营查看「平台概览」时，系统 SHALL 在「运营配置」子区按顺序展示用户管理、Agent配置、模型配置三张 KPI 卡。主数值 MUST 分别取 `ops.users`、`ops.agents`、`ops.models`。三张卡 MUST 整卡分别进入 `/ops/users`、`/ops/agents`、`/ops/model-configs`，MUST NOT 渲染独立「进入」按钮。普通用户 MUST NOT 看到这三张卡。

#### Scenario: 运营看到三张入口卡

- **WHEN** 运营打开仪表盘且统计已加载
- **THEN** 「运营配置」子区按顺序出现「用户管理」「Agent配置」「模型配置」
- **AND** 点击整卡分别进入对应运营页

#### Scenario: 三张卡没有独立进入按钮

- **WHEN** 运营查看这三张卡
- **THEN** 卡内不存在「进入」按钮（`.kpi-card__enter`）

#### Scenario: 普通用户看不到三张卡

- **WHEN** 普通用户打开仪表盘
- **THEN** 页面不出现「用户管理」「Agent配置」「模型配置」这三张概览卡
