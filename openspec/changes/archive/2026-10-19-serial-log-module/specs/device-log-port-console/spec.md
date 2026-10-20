## RENAMED Requirements

- FROM: `### Requirement: 工具箱展示日志端口列表（五列）`
- TO: `### Requirement: 串口日志页展示日志端口列表（五列）`

## MODIFIED Requirements

### Requirement: 串口日志页展示日志端口列表（五列）

串口日志页的「无线端口」Tab SHALL 以表格展示平台登记的日志端口，列 MUST 恰为 5 列：端口、SKU名称、波特率、监听开关、日志查看。端口 / SKU名称 / 波特率三列 MUST 为只读展示，取值来自平台配置登记的日志来源；波特率 MUST 表述为该端口无线串口盒的串口参数，MUST NOT 影响采集行为。每行 MUST 同时呈现该端口当前是否正在监听。

#### Scenario: 五列齐备

- **WHEN** 用户打开串口日志页的「无线端口」Tab
- **THEN** 表格包含端口、SKU名称、波特率、监听开关、日志查看五列

#### Scenario: 三列只读

- **WHEN** 用户查看端口 / SKU名称 / 波特率三列
- **THEN** 三列仅作展示，页面上没有修改它们的入口

#### Scenario: 展示现场登记值

- **WHEN** 平台登记了现场来源 7005 / H6810 / 921600
- **THEN** 表格对应行显示端口 7005、SKU名称 H6810、波特率 921600

#### Scenario: 监听状态如实呈现

- **WHEN** 某端口开关处于关闭状态
- **THEN** 该行状态呈现为未监听，与开关实际状态一致

### Requirement: 端口管理接口契约

平台 SHALL 提供读取端口列表、切换监听开关、读取日志行三个接口，全部位于 `/api/serial-log/ports/` 之下：`GET /api/serial-log/ports/`、`POST /api/serial-log/ports/toggle/`、`GET /api/serial-log/ports/<int:port>/lines/`。响应 MUST 遵循平台信封（`{status, data}`）与 snake_case 字段约定；切换开关 MUST 校验超级管理员身份；读取日志行 MUST 只接受平台已登记的端口，未登记端口 MUST 返回可读结论而非报错。旧路径 `/api/ai/log-ports/…` MUST NOT 继续提供，MUST NOT 以重定向保留别名。

#### Scenario: 读取端口列表

- **WHEN** 已登录用户请求 `GET /api/serial-log/ports/`
- **THEN** 返回每个来源的端口、SKU名称、波特率、是否正在监听与当前日志文件名

#### Scenario: 切换开关立即生效

- **WHEN** 超级管理员请求打开或关闭某端口
- **THEN** 开关状态落库并立即生效，返回生效后的状态

#### Scenario: 非管理员切换被拒

- **WHEN** 普通登录用户请求切换开关
- **THEN** 请求被拒绝（403）且开关状态保持不变

#### Scenario: 未登记端口返回可读结论

- **WHEN** 请求读取一个平台未登记的端口（如 7004）的日志行
- **THEN** 返回可读结论「端口 7004 未配置为日志来源」，MUST NOT 返回服务端错误

#### Scenario: 旧端口接口下线

- **WHEN** 请求 `/api/ai/log-ports/`
- **THEN** 返回 404，不返回端口数据，也不发生 3xx 跳转
