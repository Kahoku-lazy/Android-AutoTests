## Context

见 proposal.md 的 Why。当前落盘有四套互不相通的写法：`config/settings.py` 把根日志写到 `logs/django.log`；`engines/agents/event_log.py` 用 loguru 写 `logs/agent_events.log`；`engines/ai/process_log.py` 按天写 `agents-YYYYMMDD.log`；`apps/` 与引擎里还有直接 `FileHandler`（如 `AI-MODEL-TEST.log`）。设备采集原文由 `engines/device/logfiles.py` 按 `{SKU}_{端口}.log` 写入可配置目录（默认 `logs/`），行格式为「北京时间 [来源] 原文」，读取方依赖这个契约。

`algorithms` 是纯算法包（XPath、层级、元素分层、OCR）。`engines/device/base.py` 禁止引擎 import 该包；`test_engine_hierarchy_contract.py` 只检查 `android_device.py` 与 `android/__init__.py` 的 import 行。`AndroidConnection.__init__` 把可选回调放在 `self.log`。

## Goals / Non-Goals

**Goals:**

- 一个已实例化的日志对象拥有四组文件、统一行格式和总开关。
- 智能体事件与角色过程记录进同一个 `logs/agents/agent_events.log`。
- 串口代码日志按 SKU 与端口分文件，且不碰采集原文。

**Non-Goals:**

- 不改采集原文的目录、轮转和「北京时间 [来源] 原文」行格式。
- 不改 `run.py` 的进程标准输出捕获，不改 `boundary-check.log`。
- 不为迁移、测试、技能脚本、Django 模型新增 `__init__`。

## Decisions

### 1. 日志对象放在改名后的 `utils/logs.py`

把 `algorithms` 整包改名为 `utils`，算法模块的相对位置不变。`utils/logs.py` 用两个类分工，写法对齐 `engines/agents/role/config.py`。`LogConfig` 只保存路径和是否打到控制台。`FileLogger` 按这份配置用标准库 `logging` 写入这一个文件。`SerialLogger` 只管串口代码日志的目录。模块底部直接实例化，不再按调用方猜测文件：

- `backend_log` → `logs/backend.log`
- `agent_event_log` → `logs/agents/agent_events.log`
- `device_log` → `logs/device.log`
- `serial_log` → `logs/serial_logs/{SKU}_{端口}.log`

本文件固定在仓库 `utils/` 下，路径从上两级的仓库根拼出，不搜索 `manage.py`。控制台默认关闭。

备选是放在 `shared/` 或继续用 Django `LOGGING`。`shared/` 会被引擎碰到平台侧；Django 配置在容器里只留 stdout，也覆盖不到引擎进程里提前写出的事件。放在 `utils` 后，引擎与 `apps` 都能导入，且该模块不引用 Django。

引擎可以 `import utils.logs`。引擎仍然不得 import `utils` 里的算法模块（`xpath`、`hierarchy`、`element_layers`、`vision`）。层级契约测试改为禁止这些算法 import，并改用 `utils.hierarchy`。

### 2. 一个实例对应一个文件，用 logging 写入

每个记录器是一个 `logging.Logger`。文件用 `RotatingFileHandler`，上限 10MB，保留 3 个备份，级别 DEBUG。控制台用 `StreamHandler`，级别 WARNING。格式是 `%(asctime)s - %(name)s - %(levelname)s - %(message)s`。日志模块不把角色、模型、串口字段写进行里，也不按 SKU 或端口拆文件。

调用方选择记录器。`engines/agents` 与过程日志用 `agent_event_log`。`engines/device` 的设备代码用 `device_log`，串口代码用 `serial_log`（`logs/serial.log`）。`apps/` 用 `backend_log`。

`event_log.write_line` 改为调用 `agent_event_log`，不再 `logger.add`。`AgentProcessLog.write` 改为调用同一个 `agent_event_log`，保留角色、模型、任务与步骤、事件类型和截断规则，不再派生按天文件名。

行格式只有时间、记录器名、等级、正文。调用方要带的业务内容写在自己的 message 里。

### 3. 类里统一 `self.log = log`

四个区域内已经有 `__init__` 的运行期类，在其中写 `self.log =` 本区域对应的实例（`backend_log`、`agent_event_log`、`device_log` 或 `serial_log`）。Django 模型、迁移、测试、技能脚本不加初始化方法；这些位置若已有日志调用，改为直接使用模块级 `log`。

`AndroidConnection` 的连接回调从参数 `log` / `self.log` 改为 `trace` / `self.trace`。连接过程那句「ADB Wireless Connection」改走 `self.log`，并带上地址与串口，使其进入 `logs/serial_logs/`。

### 4. 撤掉其余代码日志文件通道

- `LOGGING` 去掉写入 `logs/django.log` 的 file handler，控制台 handler 保留。
- `event_log.py` 去掉 loguru。
- `model_test` 等自建 `FileHandler` 改为 `self.log` 或模块级 `log`。
- 旧文件留在磁盘，代码不再打开它们。

备选是用一条 `logging.Handler` 把遗留 `getLogger` 全转进 `ProjectLog`。那样类名和四组路由会靠 logger 名字猜测，和「调用点显式带字段」不一致。本次改调用点，不挂转发 Handler。

## 模块防火墙自检

- `utils/logs.py` 不 import `django` 或 `apps`。引擎只新增对 `utils.logs` 的导入，不新增对算法模块或其它 App 的导入。
- 不新增跨 App 的 service / runner 导入，不新增 ORM 写。
- 不新增 HTTP 或 WebSocket 出口，前端无改动。
- 采集归档仍由 `logfiles.LogFileSink` 写，不改到 `utils.logs`。

## Risks / Trade-offs

- [智能体文件同时接收事件时间线与过程记录，行样式比现在的「时间 | 模型 | 动作」更宽] → 事件动作文本保持原有九个动作的措辞，测试改为断言新路径和新增字段，不断言 loguru。
- [调用方漏传 `sku`/`port` 时串口日志进 `unknown_0.log`] → 串口调用点在改动时补上这三个定位字段。
- [大量类只为赋值 `self.log` 而改 `__init__`] → 只改已有 `__init__` 的运行期类；模型类用模块级 `log`。
- [`AndroidConnection` 回调改名影响传入 `log=` 的调用方] → 同步修改调用点；仓库内构造处目前没有传入该参数，默认回调改为 `self.trace`。

## Migration Plan

先落地 `utils` 改名与 `ProjectLog` 的单元测试，再改写入方，最后删旧 handler。已生成的 `logs/django.log`、`logs/agent_events.log`、`agents-YYYYMMDD.log` 不删除。回滚时恢复这些写入路径即可，新文件可以留着。
