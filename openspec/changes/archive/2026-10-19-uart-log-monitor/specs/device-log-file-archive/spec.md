## MODIFIED Requirements

### Requirement: 日志按 SKU 与端口落本地文件

平台 SHALL 把每一条由端口来源抓到的日志行追加写入本地日志文件。文件名 MUST 为 `{SKU}_{端口}.log`（如 `H6810_7005.log`），所在目录 MUST 为 `logs/serial_logs/`。每行 MUST 使用格式 `时间 - 记录器名 - 等级 - 消息`，消息 MUST 只含抓到的原文，编码 MUST 为 UTF-8。日志正文 MUST NOT 写入数据库。

#### Scenario: 逐行追加且保留历史

- **WHEN** 采集层前后收到多行日志
- **THEN** 每行按到达顺序追加到 `logs/serial_logs/H6810_7005.log` 末尾，文件中此前写入的行仍完整保留

#### Scenario: 写入即可被读取

- **WHEN** 一行日志刚被抓到
- **THEN** 不必等待进程退出，读取该文件即可看到该行

#### Scenario: 日志不写数据库

- **WHEN** 采集持续一段时间后检查数据库
- **THEN** 任何数据表中都不存在这些日志正文记录

#### Scenario: 多个来源各自成文件

- **WHEN** 平台登记了多个端口来源
- **THEN** 每个来源写入以自身 SKU 与端口命名的文件，MUST NOT 混写进同一个文件

### Requirement: 只读取当前文件，存档文件仅归档

平台的日志查看 SHALL 只读取当前文件 `logs/serial_logs/{SKU}_{端口}.log`。轮转产生的备份文件 MUST NOT 被平台读取，也 MUST NOT 被平台删除。

#### Scenario: 查看只读当前文件

- **WHEN** 用户查看某端口的日志
- **THEN** 返回内容全部来自该端口的当前文件，MUST NOT 混入轮转备份中的行

#### Scenario: 存档文件保留可外部打开

- **WHEN** 一次轮转之后
- **THEN** 轮转备份仍留在 `logs/serial_logs/` 中，平台既不读取也不删除它

### Requirement: 日志目录与文件上限可配置

抓取日志的目录 MUST 固定为 `logs/serial_logs/`。单文件上限与备份个数 MUST 与 `utils/logs.py` 的现有规则相同（10MB、3 个备份），MUST NOT 再另设一套采集专用的目录或 50MB 上限。目录不存在时，平台 SHALL 在首次写入前自动创建。

#### Scenario: 目录不存在时自动创建

- **WHEN** `logs/serial_logs/` 尚未创建
- **THEN** 平台在首次写入前创建该目录并正常写入日志文件

#### Scenario: 上限可配置生效

- **WHEN** 当前文件达到 `utils/logs.py` 规定的单文件上限
- **THEN** 按该模块的 10MB 与 3 个备份轮转，而不是按另一套 50MB 或按日期改名

## REMOVED Requirements

### Requirement: 单文件到达上限即轮转且绝不覆盖

**Reason**: 轮转改走 `utils/logs.py` 已有的 10MB 与 3 个备份，不再把当前文件改名为 `{SKU}_{端口}_{日期}.log`。
**Migration**: 当前文件仍是 `{SKU}_{端口}.log`。历史内容留在该文件的轮转备份中，平台查看不读取这些备份。

## ADDED Requirements

### Requirement: 按 10MB 轮转并保留 3 个备份

当前文件达到 10MB 时，系统 SHALL 按 `utils/logs.py` 的轮转规则继续写入，并最多保留 3 个备份。轮转 MUST NOT 清空当前正在写入的这一行之前已经落盘的内容。进程重启后 MUST 从当前文件末尾续写。

#### Scenario: 重启后从当前文件末尾续写

- **WHEN** 平台重启并继续采集同一端口
- **THEN** 新行追加到当前文件末尾，MUST NOT 覆盖或清空已有内容

#### Scenario: 备份个数有上限

- **WHEN** 同一文件的轮转备份已经有 3 个，文件再次达到 10MB
- **THEN** 系统继续轮转，备份个数不超过 3 个
