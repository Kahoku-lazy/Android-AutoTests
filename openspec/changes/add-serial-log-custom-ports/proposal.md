# Proposal: add-serial-log-custom-ports

## Why

无线串口日志的端口 / SKU / 波特率目前只能改环境配置 `DEVICE_LOG_SOURCES` 并重启后端才能新增，现场加一个端口很不方便；页面不展示本机监听 IP，用户配置串口盒时不知道填哪个地址；开启监听后端口绑定失败被前端显示成绿色成功提示，用户无法感知「监听失败」。需求方已确认方案（`temps/serial-log-custom-ports-proto.html`）并批准两条规则变更申请。

## What Changes

- 无线端口面板头部展示**本机监听 IP**（出站局域网 IP 探测，支持 `DEVICE_LOG_ADVERTISE_HOST` 覆盖），一键复制；每行给出 `IP:端口` 完整地址。
- 新增**自定义端口**能力：超管在页面新增端口（自定义端口号 / SKU / 波特率），保存即落库并**增量开启该端口监听**，不干扰其它端口；自定义端口可编辑（SKU / 波特率，端口号不可改）与删除（停监听、删登记、保留日志文件）。
- 端口登记双轨制：`sl_log_ports` 增加 `origin` 列（`config` / `custom`）；配置端口维持只读基线，自定义端口以库为真相源；`source_specs()` 合并两路，AI 日志查询自动支持自定义端口。
- **监听失败显式提示**：开启 / 新增后 `enabled && !listening` 时前端改为红色错误提示与「监听失败」状态胶囊，后端 note 区分「端口已被其它程序占用 / 端口绑定失败」；失败端口保留登记可重试。
- 新增三个超管接口：`POST /api/serial-log/ports/`、`PATCH /api/serial-log/ports/<port>/`、`DELETE /api/serial-log/ports/<port>/`；列表接口响应增加 `listen_ip` 与每行 `origin` / `address`。
- 规则变更（已获需求方批准）：`backend/apps/serial_log/AGENTS.md` 三列真相源条款改为双轨口径；`device-log-port-console`「三列只读」加 delta（custom 行例外）。
- 采集引擎 `engines/uart_log` **零改动**；新增 / 编辑 / 删除一律单端口增量生效，禁止全局 reset。

## 关联文档

无对应 PRD 编号：本变更是需求方直接提出的无线端口管理体验需求（方案原型 `temps/serial-log-custom-ports-proto.html` 已审阅确认）。`PRD-平台总需求` 仅声明串口日志证据能力，未对端口管理需求编号，不虚构编号。

## Capabilities

### New Capabilities

（无——全部落在既有能力的需求级扩展上）

### Modified Capabilities

- `device-log-port-console`: 「三列只读」改为配置行只读 / 自定义行可增删改（仅超管）；新增「自定义端口登记」「本机监听地址展示」「监听失败显式提示」三条需求；「端口管理接口契约」扩展三个写接口与列表新字段。
- `serial-log-module`: 「串口日志拥有端口监听开关状态」的三列真相源条款改为双轨制（config 行以配置为真相源，custom 行以 `sl_log_ports` 为真相源）；「串口日志接口路径与契约」由四接口扩展为七接口；「两张表的字号与状态呈现」的状态胶囊增加「监听失败红」。
- `serial-log-page`: 「页内权限与只读边界」扩展为超管可新增 / 编辑 / 删除自定义端口，非超管维持只读；日志窗口只读口径不变。

## Impact

- **后端**：`backend/apps/serial_log/`（models + 迁移、api.py、sources.py、port_service.py、views.py、urls.py、AGENTS.md 条款）；`backend/config/settings.py` 增加 `DEVICE_LOG_ADVERTISE_HOST`；本机 IP 探测落 `utils/`（不属引擎层）。
- **前端**：`frontend/src/modules/serial-log/`（api.ts、constants.ts、WifiPortPanel.vue 及其样式、useLogPorts.ts、新增端口弹窗组件与 composable、模块 AGENTS.md 端点清单同步）；复用 AppTable / DoodleBtn / el-dialog + sketch-kit / ElMessageBox，无新共享组件。
- **引擎层**：`engines/uart_log` 零改动（复用 `PortSwitch.open` 幂等增量、`PortDetector` 探测、`_await_listening`）。
- **测试**：`tests/serial_log/`（api / 单元 / 集成）新增自定义端口 CRUD、双轨合并、失败 note、上限与权限用例；前端既有 serial-log 测试随契约更新。
- **不受影响**：日志关键词只读口径、日志文件命名与轮转（device-log-file-archive）、MAX_PORTS=10 上限、AI 工具箱两源边界、其它模块页面。