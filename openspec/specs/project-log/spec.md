# project-log Specification

## Purpose
把后端、智能体、串口与设备四组运行日志收成一个进程内日志对象，按固定字段追加到约定文件，使同一次执行可以按先后顺序对照排障。

## Requirements

### Requirement: 按模块实例化的日志对象与总开关

系统 SHALL 在 `utils/logs.py` 用标准库 `logging` 建好四个记录器：`backend_log` 写入 `logs/backend.log`，`agent_event_log` 写入 `logs/agents/agent_events.log`，`device_log` 写入 `logs/device.log`，`serial_log` 写入 `logs/serial.log`。每个文件 MUST 使用 `RotatingFileHandler`，单文件上限 10MB，保留 3 个备份。文件级别为 DEBUG，控制台级别为 WARNING。后端业务代码、`engines/agents`、`engines/device` 以及串口相关模块中，已经定义初始化方法的运行期类 SHALL 在初始化时把本区域对应的记录器赋给实例属性 `log`。迁移文件、测试、技能脚本与 Django 模型类 MUST NOT 为了挂上该属性而新增初始化方法。日志模块 MUST NOT 根据角色、模型、SKU 或端口改写正文或改选文件。

#### Scenario: 同一区域的两个类共用对应实例

- **WHEN** 两个后端类先后完成初始化
- **THEN** 两者的 `log` 都是 `backend_log`，并且不是 `device_log` 或 `agent_event_log`

#### Scenario: DEBUG 只进文件，WARNING 同时打到控制台

- **WHEN** 同一个记录器先写一条 DEBUG，再写一条 WARNING
- **THEN** 文件里两条都有，控制台只有 WARNING

### Requirement: 四组日志按调用方落入固定路径

调用方 SHALL 把一条运行日志交给对应实例，由该实例追加写入且只写入下面一组路径，编码为 UTF-8，目录不存在时 MUST 自动创建：

- 后端代码调用 `backend_log`，写入 `logs/backend.log`
- `engines/agents` 的代码日志与事件时间线调用 `agent_event_log`，写入 `logs/agents/agent_events.log`
- 串口代码日志调用 `serial_log`，写入 `logs/serial.log`
- `engines/device` 中不带串口定位字段的代码日志调用 `device_log`，写入 `logs/device.log`

同一条日志 MUST NOT 同时出现在两组文件中。`engines/agents` 的事件时间线 MUST NOT 再写入 `logs/agent_events.log`，也 MUST NOT 再通过独立的 loguru 通道落盘。

#### Scenario: 智能体事件写入新路径

- **WHEN** 一轮智能体发言写出「开始」动作
- **THEN** 该行出现在 `logs/agents/agent_events.log`，`logs/agent_events.log` 不因此被创建或追加

#### Scenario: 设备代码与串口代码分开

- **WHEN** 设备引擎写出一条没有串口定位字段的日志，同时串口模块为 SKU `H6810`、端口 `7005` 写出一条日志
- **THEN** 前者只在 `logs/device.log`，后者只在 `logs/serial.log`

### Requirement: 每行只有时间、记录器名、等级与正文

每一行 SHALL 使用格式 `%(asctime)s - %(name)s - %(levelname)s - %(message)s`。日志模块 MUST NOT 另加文件路径、类名、角色、模型或串口字段。写入 MUST 为追加，MUST NOT 覆盖已有内容。单文件达到 10MB 时 MUST 轮转，并最多保留 3 个备份。

#### Scenario: 普通后端行

- **WHEN** 后端日志以 INFO 写出正文 `设备已释放`
- **THEN** `logs/backend.log` 增加一行，其中包含记录器名 `backend`、等级 `INFO` 与正文 `设备已释放`

### Requirement: 串口代码日志不改写采集原文

串口代码日志 SHALL 写入 `logs/serial.log`。这些代码日志 MUST NOT 写入设备采集原文所使用的 `{SKU}_{端口}.log`（该文件仍由采集归档按原契约维护）。

#### Scenario: 采集原文文件不被代码日志改写

- **WHEN** 串口代码日志写入完成，且采集归档目录里已有 `H6810_7005.log`
- **THEN** 采集归档目录中的该文件内容不因这条代码日志而改变

### Requirement: 按调用顺序落盘且失败不打断业务

多条日志 SHALL 按调用发生的先后顺序写入。并发调用时每条记录 MUST 自成一行，MUST NOT 出现两条记录交错在同一行。写文件失败（目录不可创建、磁盘满、权限不足）时，日志对象 MUST NOT 把异常抛给业务调用方。

#### Scenario: 先后两条保持顺序

- **WHEN** 同一线程先写出正文 `第一步`，再写出正文 `第二步`
- **THEN** 对应文件中 `第一步` 位于 `第二步` 之前

#### Scenario: 写失败不中断调用方

- **WHEN** 目标日志目录无法创建，调用方仍写出一条日志
- **THEN** 调用方收到正常返回，业务流程继续
