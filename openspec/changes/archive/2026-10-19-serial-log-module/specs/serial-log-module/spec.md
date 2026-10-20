## Purpose

把串口日志从 AI 助手里独立出来，形成一个自有边界的后端模块：端口来源登记、监听开关持久化、启停编排、当前日志文件只读、关键词对照表与启动恢复都由它承接，其它模块只能经它的接口读写。

## ADDED Requirements

### Requirement: 串口日志拥有端口监听开关状态

系统 SHALL 由串口日志模块独占持久化「端口是否持续监听」这一状态，落表 `sl_log_ports`。端口 / SKU名称 / 波特率三列的真相源 MUST 仍是平台配置（`DEVICE_LOG_SOURCES` 等 `DEVICE_LOG_*` 配置），表内 MUST 只保存开关与最近一次写入时间。其它模块 MUST NOT 直接读写该表；需要开关状态时 MUST 经串口日志模块的 api 读取。串口日志模块 MUST NOT import AI 助手模块的内部实现。

#### Scenario: 开关状态只由串口日志模块写入

- **WHEN** 超级管理员通过串口日志接口打开或关闭某端口
- **THEN** 只有串口日志模块写入 `sl_log_ports`，其它模块的数据表不出现该端口的开关记录

#### Scenario: 无记录视为开启

- **WHEN** 某端口在 `sl_log_ports` 中没有记录
- **THEN** 该端口按开启处理，平台持续监听它

#### Scenario: 配置变更不改开关

- **WHEN** 平台配置里某端口的 SKU 或波特率发生变化
- **THEN** 串口日志模块只刷新表内的 SKU 与波特率，MUST NOT 改写该端口的开关值

### Requirement: 迁移保留既有监听开关状态

升级时系统 SHALL 把旧表 `ai_log_ports` 的每一行复制到 `sl_log_ports`，再移除旧表与旧模块。升级后 MUST 保持每个端口原来的开关值：升级前关闭的端口 MUST 仍为关闭，MUST NOT 因为升级而开始监听。全新安装（不存在旧表）时 MUST 直接使用新表，MUST NOT 因缺少旧表而失败。

#### Scenario: 已关闭端口升级后仍关闭

- **WHEN** 升级前端口 7005 的开关为关闭
- **THEN** 升级完成并重启后，该端口仍为关闭，不写入新日志

#### Scenario: 已开启端口升级后继续监听

- **WHEN** 升级前端口 7005 的开关为开启
- **THEN** 升级完成并重启后，该端口自动恢复监听

#### Scenario: 全新安装不依赖旧表

- **WHEN** 数据库里从来没有 `ai_log_ports` 表
- **THEN** 迁移全部成功，`sl_log_ports` 可用，平台按配置登记端口

#### Scenario: 旧表与旧代码不再留存

- **WHEN** 迁移全部完成
- **THEN** `ai_log_ports` 表已被删除，AI 助手模块不再包含端口开关模型与端口管理服务

### Requirement: 启动恢复监听由串口日志模块负责

平台启动后 SHALL 按 `sl_log_ports` 里持久化的开关状态恢复监听，MUST NOT 需要用户先打开页面。同时监听的端口 MUST NOT 超过 10 个；超出上限的端口 MUST NOT 被打开，并 MUST 留下可读记录。autoreload 的父进程 MUST NOT 抢占日志端口；`DEVICE_LOG_ENABLED` 关闭时 MUST NOT 打开任何端口。

#### Scenario: 重启后自动恢复

- **WHEN** 后端重启完成，且开启监听的端口不超过 10 个
- **THEN** 这些端口自动恢复监听，无需任何人打开页面或再次点击开关

#### Scenario: 超过上限的端口不恢复

- **WHEN** 持久化状态里开启监听的端口有 11 个
- **THEN** 只恢复 10 个，第 11 个保持开关不变但不监听，并留下可读记录

#### Scenario: autoreload 父进程不抢端口

- **WHEN** 开发态以 autoreload 启动，父进程只做文件监控
- **THEN** 父进程不打开任何日志端口，端口由真正服务的子进程监听

#### Scenario: 采集总开关关闭

- **WHEN** `DEVICE_LOG_ENABLED` 为关闭
- **THEN** 启动时任何端口都不被打开

### Requirement: 串口日志接口路径与契约

平台 SHALL 在 `/api/serial-log/` 下提供四个接口，路径 MUST 以 `/` 结尾：`GET /api/serial-log/ports/`、`POST /api/serial-log/ports/toggle/`、`GET /api/serial-log/ports/<int:port>/lines/`、`GET /api/serial-log/keywords/`。响应 MUST 遵循平台信封 `{status, data}` 与 snake_case 字段约定。端口列表、日志行与关键词目录 MUST 登录可读；切换开关 MUST 仅限超级管理员。旧路径 `/api/ai/log-ports/…` 与 `/api/ai/log-keywords/` MUST NOT 继续提供，也 MUST NOT 以重定向保留别名。

#### Scenario: 读取端口列表

- **WHEN** 已登录用户请求 `GET /api/serial-log/ports/`
- **THEN** 返回每个登记端口的端口、SKU名称、波特率、是否开启监听、当前是否真的在监听与日志文件名

#### Scenario: 切换开关

- **WHEN** 超级管理员请求 `POST /api/serial-log/ports/toggle/`，body 为 `{"port": 7005, "enabled": false}`
- **THEN** 开关落库并立即生效，返回生效后的该端口状态

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

### Requirement: 关键词对照表由串口日志模块组装

串口日志模块 SHALL 以只读方式组装「串口日志关键词 → 功能模块 / 功能点」对照表：采集正在运行时 MUST 取运行中的关键词索引，否则 MUST 直读 `DEVICE_LOG_KEYWORD_FILE` 指向的文件；两者都取不到时 MUST 返回空列表与可读说明，MUST NOT 抛错、MUST NOT 写文件或写库。关键词顺序 MUST 与对照表内顺序一致。

#### Scenario: 采集运行时取运行中索引

- **WHEN** 采集正在运行
- **THEN** 目录的取值来源标为运行中的采集索引，条目与判定实际使用的那张表一致

#### Scenario: 采集未运行直读文件

- **WHEN** 采集未启动但关键词表文件存在
- **THEN** 目录从文件读取并标为关键词表文件，同时给出文件更新时间

#### Scenario: 表不可用给可读空态

- **WHEN** 关键词表文件缺失或无法解析
- **THEN** 返回空条目与可读原因，不返回 500
