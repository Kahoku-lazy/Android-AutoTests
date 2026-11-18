# serial-log-module Delta

## MODIFIED Requirements

### Requirement: 串口日志拥有端口监听开关状态

系统 SHALL 由串口日志模块独占持久化「端口是否持续监听」这一状态，落表 `sl_log_ports`。端口登记 SHALL 实行双轨制：**配置端口**的端口 / SKU名称 / 波特率三列真相源 MUST 仍是平台配置（`DEVICE_LOG_SOURCES` 等 `DEVICE_LOG_*` 配置），配置同步 MUST 只刷新配置行；**自定义端口**的三列真相源 MUST 是 `sl_log_ports` 本身（来源标记为 custom），配置同步 MUST NOT 创建、改写或删除自定义行。表内 MUST 保存开关、来源标记与最近一次写入时间。其它模块 MUST NOT 直接读写该表；需要开关状态时 MUST 经串口日志模块的 api 读取。串口日志模块 MUST NOT import AI 助手模块的内部实现。

#### Scenario: 开关状态只由串口日志模块写入

- **WHEN** 超级管理员通过串口日志接口打开或关闭某端口
- **THEN** 只有串口日志模块写入 `sl_log_ports`，其它模块的数据表不出现该端口的开关记录

#### Scenario: 无记录视为开启

- **WHEN** 某配置端口在 `sl_log_ports` 中没有记录
- **THEN** 该端口按开启处理，平台持续监听它

#### Scenario: 配置变更不改开关

- **WHEN** 平台配置里某端口的 SKU 或波特率发生变化
- **THEN** 串口日志模块只刷新表内配置行的 SKU 与波特率，MUST NOT 改写该端口的开关值

#### Scenario: 配置同步不碰自定义行

- **WHEN** 平台配置发生变化且表内存在自定义端口行
- **THEN** 自定义行的三列与开关值保持不变，配置同步只作用于配置行

### Requirement: 串口日志接口路径与契约

平台 SHALL 在 `/api/serial-log/` 下提供七个接口，路径 MUST 以 `/` 结尾：`GET /api/serial-log/ports/`、`POST /api/serial-log/ports/`、`POST /api/serial-log/ports/toggle/`、`PATCH /api/serial-log/ports/<int:port>/`、`DELETE /api/serial-log/ports/<int:port>/`、`GET /api/serial-log/ports/<int:port>/lines/`、`GET /api/serial-log/keywords/`。响应 MUST 遵循平台信封 `{status, data}` 与 snake_case 字段约定。端口列表、日志行与关键词目录 MUST 登录可读；切换开关、新增端口、编辑端口、删除端口 MUST 仅限超级管理员。旧路径 `/api/ai/log-ports/…` 与 `/api/ai/log-keywords/` MUST NOT 继续提供，也 MUST NOT 以重定向保留别名。

#### Scenario: 读取端口列表

- **WHEN** 已登录用户请求 `GET /api/serial-log/ports/`
- **THEN** 返回本机监听 IP，以及每个登记端口的端口、SKU名称、波特率、来源、完整监听地址、是否开启监听、当前是否真的在监听与日志文件名

#### Scenario: 切换开关

- **WHEN** 超级管理员请求 `POST /api/serial-log/ports/toggle/`，body 为 `{"port": 7005, "enabled": false}`
- **THEN** 开关落库并立即生效，返回生效后的该端口状态

#### Scenario: 新增端口

- **WHEN** 超级管理员请求 `POST /api/serial-log/ports/`，body 为 `{"port": 7008, "sku": "H717D", "baud": 115200}`
- **THEN** 自定义端口落库并立即开始监听，返回生效后的该端口状态（含真实监听结果）

#### Scenario: 编辑与删除自定义端口

- **WHEN** 超级管理员请求 `PATCH` 或 `DELETE /api/serial-log/ports/7008/`
- **THEN** 编辑只更新该自定义端口并按开关恢复其监听；删除停止其监听并移除登记，历史日志文件保留

#### Scenario: 非管理员切换被拒

- **WHEN** 普通登录用户请求切换开关
- **THEN** 返回 403 且开关状态保持不变

#### Scenario: 未登记端口给可读结论

- **WHEN** 请求读取未登记端口（如 7004）的日志行
- **THEN** 返回可读结论「端口 7004 未配置为日志来源」，MUST NOT 返回服务端错误

#### Scenario: 旧接口下线

- **WHEN** 请求 `/api/ai/log-ports/` 或 `/api/ai/log-keywords/`
- **THEN** 返回 404，不返回端口或关键词数据，也不发生 3xx 跳转

#### Scenario: 读取关键词目录

- **WHEN** 已登录用户请求 `GET /api/serial-log/keywords/`
- **THEN** 返回关键词 → 功能点条目、关键词数、功能点数、取值来源与表文件更新时间

### Requirement: 串口日志两张表的字号与状态呈现

端口表与关键词表的列头 MUST 为 **16px** 且带图标；表体正文 MUST 为 **14px**；数据单元格上下内边距 MUST 不小于 12px。首列 MUST 是「图标圆 + 主行」身份单元（端口 🔌 / 关键词 🔑）。监听状态 MUST 以**状态色 20%→5% 渐变胶囊**呈现（监听中绿 / 未监听天蓝 / 已停止灰 / **监听失败红**），开关本体 MUST 保留且权限不变。「监听失败」胶囊 MUST 仅在开关开启但实际未监听时出现，并 MUST 伴随可读失败原因。操作键 MUST 采用 `.sketch-kit` 的描边态，SHALL NOT 在模块样式里自写虚线。关键词搜索 MUST 使用 `.sketch-kit` 的输入框，SHALL NOT 使用无皮肤的原生 `input`。

#### Scenario: 表格字号与首列

- **WHEN** 量测端口表与关键词表
- **THEN** 表头 16px、表体 14px、单元格内边距 ≥12px
- **AND** 两张表首列都是图标圆 + 主行

#### Scenario: 状态胶囊与开关并存

- **WHEN** 查看任一端口行的监听状态
- **THEN** 出现渐变状态胶囊，同时保留可操作的开关
- **AND** 非超管看到的开关仍为禁用态

#### Scenario: 监听失败红色胶囊

- **WHEN** 某端口开关开启但实际未监听
- **THEN** 该行状态胶囊为红色「监听失败」，并展示可读失败原因

#### Scenario: 关键词搜索是手稿输入框

- **WHEN** 查看关键词 Tab 的搜索框
- **THEN** 该输入框为虚线描边、无影（来自 `.sketch-kit`）
- **AND** 模块样式里没有自写 `dashed` 的输入框规则