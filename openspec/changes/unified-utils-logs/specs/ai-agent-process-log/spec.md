## MODIFIED Requirements

### Requirement: 过程日志的文件与自动创建

过程日志 SHALL 经进程内唯一的日志对象追加写入 `logs/agents/agent_events.log`，与智能体事件时间线共用该文件。写入 SHALL 为 UTF-8 追加，MUST NOT 覆盖既有内容。过程日志 MUST NOT 再按天切分到 `agents-YYYYMMDD.log`，也 MUST NOT 再使用 `<当前工作目录>/logs/agents.log` 作为基路径派生当天文件。文件或其所在目录不存在时 MUST 自动创建。并发写入（多角色、多任务同时执行）时每条记录 MUST 自成一行，MUST NOT 出现跨行交错。引擎 MUST NOT 依赖平台配置或框架来取得该落点，也 MUST NOT 自动删除历史文件。磁盘上已经存在的按天过程日志文件 MUST 原样保留，本能力 MUST NOT 删除、截断或移动它们。

每条过程记录 SHALL 使用 `logging` 的时间、等级与记录器名，正文 SHALL 包含角色名、模型名、任务与步骤标识、事件类型与内容。

#### Scenario: 首次运行时自动创建

- **WHEN** `logs/agents/agent_events.log` 或其目录尚不存在，且发生了第一次角色执行
- **THEN** 系统创建该目录与文件并写入记录，MUST NOT 因此报错或中断执行

#### Scenario: 跨天自动切换

- **WHEN** 一次运行跨过零点后继续产生过程记录
- **THEN** 零点之后的记录仍追加在 `logs/agents/agent_events.log`，MUST NOT 新建 `agents-YYYYMMDD.log`，也 MUST NOT 移动或覆盖零点之前的记录

#### Scenario: 落点由调用方注入

- **WHEN** 引擎写出一条过程记录
- **THEN** 该记录出现在 `logs/agents/agent_events.log`；引擎侧 MUST NOT import 平台模块来解析落点，也 MUST NOT 再接受按天基路径

#### Scenario: 并发写入不串行

- **WHEN** 两个角色同时执行并写日志
- **THEN** 每条记录仍是完整的一行，MUST NOT 出现两条记录内容交错在同一行

#### Scenario: 历史文件不被清理

- **WHEN** 已经存在前几天写下的 `agents-YYYYMMDD.log`
- **THEN** 引擎 MUST NOT 删除、截断或移动这些文件
