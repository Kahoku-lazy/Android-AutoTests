# serial-log-module Specification

## Purpose
把串口日志从 AI 助手里独立出来，形成一个自有边界的后端模块：端口来源登记、监听开关持久化、启停编排、当前日志文件只读、关键词对照表与启动恢复都由它承接，其它模块只能经它的接口读写。

## Requirements

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
- **THEN** 返回关键词 → 功能点条目、关键词数、功能点数、取值来源与最近一次写入时间

### Requirement: 关键词对照表由串口日志模块从数据库组装

串口日志模块 SHALL 以只读方式从其自有的关键词表组装「串口日志关键词 → 功能模块 / 功能点」对照表：条目 MUST 取自数据库，组装路径 MUST NOT 写库、MUST NOT 写文件、MUST NOT 启停任何端口，也 MUST NOT 依赖采集是否运行。关键词顺序 MUST 与表内登记顺序一致。表为空或不可用时 MUST 返回空列表与可读说明，MUST NOT 抛错。

#### Scenario: 条目取自数据库

- **WHEN** 已登录用户请求关键词对照表
- **THEN** 条目来自串口日志模块的关键词表，取值来源标为数据库，并给出表内最近一次写入时间

#### Scenario: 顺序与登记顺序一致

- **WHEN** 关键词表内登记了多个关键词与多个功能点
- **THEN** 组装结果按表内登记顺序逐行给出，同一关键词的功能点按登记先后排列

#### Scenario: 表为空给可读空态

- **WHEN** 关键词表没有任何条目或不可用
- **THEN** 返回空条目与可读原因，不返回 500

#### Scenario: 组装不产生写入

- **WHEN** 对照表被反复读取
- **THEN** 关键词表的条目与时间戳不发生变化，也不产生任何文件写入或端口启停

### Requirement: 串口日志拥有关键词对照表数据

系统 SHALL 由串口日志模块独占持久化「关键词 → 功能模块 / 功能点」对照表，落表 `sl_log_keywords`，一行 MUST 为一个「关键词 × 功能点 × 范围」。每行 MUST 含关键词原文、功能点编号、功能模块名、功能点名与范围；同一关键词同一功能点在同一范围内 MUST NOT 重复登记。范围 MUST 区分「通用」与「SKU 专用」：通用条目 MUST 对所有型号生效；SKU 专用条目 MUST 只对该 SKU 生效；某型号可用关键词 MUST 为通用条目与该型号专用条目的**并集**，专用条目 MUST NOT 覆盖或使通用条目失效。该表的全部写入 MUST 经串口日志模块的 api；其它模块 MUST NOT 直接写表，需要按型号取词时 MUST 经串口日志模块的 api 按并集口径读取。

#### Scenario: 通用条目对所有型号生效

- **WHEN** 按任一型号读取可用关键词
- **THEN** 结果包含全部通用条目

#### Scenario: 专用条目是增量

- **WHEN** 表内登记了 H6601 专用条目
- **THEN** H6601 的可用关键词为通用条目与 H6601 专用条目的并集
- **AND** 其它型号的可用关键词不包含 H6601 专用条目

#### Scenario: 同一关键词挂多个功能点

- **WHEN** 同一关键词在同一范围内登记了两个功能点
- **THEN** 表内存在两行，各带自己的功能点编号与名称，组装时该关键词占两行

#### Scenario: 重复登记不产生第二行

- **WHEN** 再次写入相同关键词、相同功能点编号、相同范围的条目
- **THEN** 不产生第二行（按更新或拒绝处理），唯一性口径不被破坏

#### Scenario: 其它模块不直接写表

- **WHEN** 其它模块需要变更关键词条目
- **THEN** 变更经串口日志模块的 api 发生，不出现绕过 api 的直接写表

### Requirement: 迁移保留存量关键词条目

升级时系统 SHALL 把现行关键词数据文件的存量条目一次性迁入 `sl_log_keywords`：范围 MUST 全部为通用，功能点编号与名称 MUST 与原表一致，行序 MUST 保持原表内顺序。迁移 MUST 以冻结快照方式进行，MUST NOT 依赖部署时读取数据文件。全新安装 MUST 得到同样的全量条目。迁移后数据文件 MUST 退役为种子档案，平台的展示与取词 MUST NOT 再依赖该文件。

#### Scenario: 升级后存量条目不丢

- **WHEN** 升级完成
- **THEN** 关键词数与功能点数与原数据文件一致，逐条的关键词、功能点编号、模块与名称与原表一致

#### Scenario: 存量全部为通用

- **WHEN** 查看迁移后的条目
- **THEN** 所有条目的范围均为通用

#### Scenario: 行序保持

- **WHEN** 迁移后组装对照表
- **THEN** 行序与原数据文件内的先后顺序逐行一致

#### Scenario: 全新安装不依赖旧数据

- **WHEN** 在从未有过关键词数据的数据库上执行迁移
- **THEN** 迁移成功并得到同样的全量条目，不依赖数据文件在场

#### Scenario: 回退不丢数据文件

- **WHEN** 回退本次迁移
- **THEN** 关键词表被移除，原数据文件仍在，旧版平台仍可按文件读取

### Requirement: 关键词维护接口（仅超管）

平台 SHALL 在 `/api/serial-log/keywords/` 下提供关键词维护接口，且 MUST 仅限超级管理员：`POST /api/serial-log/keywords/`（新建）、`PATCH /api/serial-log/keywords/<int:row_id>/`（部分更新）、`DELETE /api/serial-log/keywords/<int:row_id>/`（删除）。路径 MUST 以 `/` 结尾；响应 MUST 遵循平台信封 `{status, data}` 与 snake_case。`GET /api/serial-log/keywords/` 的功能点条目 MUST 带 `row_id`（条目主键）。全部写入 MUST 经串口日志模块的 api；非超管请求 MUST 返回 403 且不产生写入。业务错误（重复新建、编辑撞车、条目不存在）MUST 返回可读 400；删除 MUST NOT 影响日志文件与采集。

#### Scenario: 超管新建关键词

- **WHEN** 超级管理员 `POST /api/serial-log/keywords/`，body 为 `{"keyword": "h6601_boot", "module": "设备开关", "feature": "H6601开机完成", "scope": "H6601"}`
- **THEN** 返回 201，条目落库且范围为 H6601，功能点编号按全表续编

#### Scenario: 新建缺省通用与续编

- **WHEN** 超级管理员新建时不带 scope 与 feature_id
- **THEN** 条目范围为通用（`*`），功能点编号为全表 max+1，行序追加表尾

#### Scenario: 重复新建被拒

- **WHEN** 超级管理员 POST 已存在的「关键词 + 功能点编号 + 范围」组合
- **THEN** 返回可读 400，表内不产生第二行

#### Scenario: 非超管被拒

- **WHEN** 普通登录用户请求 POST / PATCH / DELETE 关键词接口
- **THEN** 返回 403，关键词表不发生任何变化

#### Scenario: 编辑部分更新

- **WHEN** 超级管理员 `PATCH /api/serial-log/keywords/<row_id>/`，body 为 `{"feature": "打开设备成功（改）"}`
- **THEN** 返回 200，仅该字段更新，其余字段与行序不变

#### Scenario: 编辑撞车被拒

- **WHEN** 超级管理员 PATCH 把条目改成另一行已有的「关键词 + 功能点编号 + 范围」
- **THEN** 返回可读 400，两行均保持原样

#### Scenario: 编辑或删除不存在条目

- **WHEN** 超级管理员 PATCH 或 DELETE 一个不存在的 row_id
- **THEN** 返回可读 400，不返回服务端错误

#### Scenario: 删除单条不影响采集

- **WHEN** 超级管理员 `DELETE /api/serial-log/keywords/<row_id>/`
- **THEN** 返回 200，该条目移除，日志文件与端口监听状态不变

#### Scenario: 目录带 row_id

- **WHEN** 已登录用户 `GET /api/serial-log/keywords/`
- **THEN** 每个功能点条目带 `row_id`，与表内主键一致

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

### Requirement: 关键词表按功能模块区分色相

关键词表的「关键词」与「功能模块」两列 MUST 按功能模块着色：同一功能模块 MUST 得到同一色相；不同模块 MUST 在色池容量内互不撞色。分配 MUST 按模块在表中**首次出现的顺序**依次取色池（色池用完才循环），且 MUST 基于全量行而非过滤后的行，保证切换搜索词时已有配色不漂移。色相 MUST 取 `tokens.css` 的模块令牌，SHALL NOT 写字面色值；正文色 MUST 由该令牌与墨色混合得到，保证浅底可读。

#### Scenario: 同一模块同色、不同模块不撞色

- **WHEN** 表格中出现 6 个不同的功能模块（少于色池容量）
- **THEN** 6 个模块各得一个不同色相
- **AND** 同一行内关键词与模块名的计算颜色相同

#### Scenario: 搜索过滤不改变配色

- **WHEN** 输入搜索词把行数收窄或清空
- **THEN** 剩余行的模块仍保持原来的色相
- **AND** 清空搜索后颜色与过滤前一致
