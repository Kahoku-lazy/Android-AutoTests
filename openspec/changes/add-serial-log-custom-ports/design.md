# Design: add-serial-log-custom-ports

## Context

动机见 proposal.md - Why。当前实现的关键事实（均已从代码核实）：

- 端口登记真相源是 `sources.source_specs()` 解析 `DEVICE_LOG_SOURCES` 配置；`sl_log_ports` 已有 port/sku/baud 三列但只持久化开关，`api.ensure_log_ports(specs)` 按配置同步三列。
- `engines/uart_log` 的 `PortSwitch.open()` 按端口幂等（活着的接收线程直接返回成功），每端口独立线程与 socket；`PortReceiver.run()` 先 `PortDetector.available()` 两步探测（客户端连接探测 + 试绑定）再真实 bind，失败线程退出、`listening=False`。
- `port_service.set_enabled()` 已是「写库 → 单端口 open/close → `_await_listening(1s)` 拿真实结果」的增量路径；`reconcile()` 由 GET 10 秒节流触发，对活着端口无副作用。
- 前端 `useLogPorts.setEnabled` 把 `enabled && !listening` 用 `ElMessage.success` 提示——失败感知缺口在此。
- 约束：engines 零 Django、写库只经 `api.py`、View 只分发、MAX_PORTS=10、开关仅超管。两条规则变更（App AGENTS 真相源条款、spec 三列只读）已获需求方批准。

## Goals / Non-Goals

**Goals:**

- 自定义端口 CRUD 与配置端口基线共存，来源可辨、互不覆盖。
- 新增/编辑/删除一律单端口增量生效，其它端口连接零中断。
- 本机监听 IP 可见可复制；监听失败可见可重试。
- 引擎层零改动；回退后自定义行休眠、配置链路无损。

**Non-Goals:**

- 不做多网卡 IP 候选列表（P2）；不做保存前预探测（P2）；不做设备在线/心跳检测。
- 不改「只看监听中」筛选语义（仍按 `enabled` 过滤）、分页、日志抽屉交互。
- 不做全量库化（配置仍是配置端口的真相源）；不动关键词表与日志文件轮转。

## Decisions

### D1 数据模型：`sl_log_ports` 加 `origin` 列，不建新表

`origin` 取值 `config`（默认）/ `custom`。迁移只加列带默认值，存量行全部视为 config，无数据搬迁。`ensure_log_ports` 改为**只 upsert config 行**（按 port 匹配且 origin=config），不创建、不改写、不删除 custom 行。`source_specs()` = 配置解析结果 + `api.list_custom_port_specs()`（经 api 读库），按端口排序去重。

- 备选：独立新表 `sl_custom_ports` —— 否决：开关语义、reconcile、读行路径全要双表合并，改动面翻倍。
- 备选：全量库化 —— 否决：破坏运维改配置即生效的口径（见方案 B 对比）。
- **配置后加同号端口**：若配置后来登记了已被 custom 占用的端口，config 同步跳过该端口并记 warning，该行仍按 custom 管理（spec：配置同步不碰自定义行）。

### D2 生效方式：单端口增量，禁止全局 reset

新增 = 校验 → `api.create_custom_port` → `switch.open(新端口)` → `_await_listening` → 返回真实结果；编辑 = `switch.close(该端口)` → 更新 → 按开关 `open`；删除 = `switch.close` → 删行。复用 `set_enabled` 同款路径与上限检查（`reserved_count() >= MAX_PORTS` 时新增直接可读拒绝，不动现有端口）。`reconcile()` 保留为兜底校正；`reset_port_switch()` 仍只用于测试与总开关关闭。

- 备选：新增后全量重启监听 —— 否决：掐断其它端口正在推流的设备连接，造成日志空窗（需求方已确认增量口径）。

### D3 本机 IP：UDP 出站探测 + 配置覆盖，落 `utils/`

新增 `utils/netinfo.py`（纯 socket，无 Django）：`local_lan_ip()` 用 UDP `connect` 外网地址后读 `getsockname()`（不发包），失败回退 `gethostbyname(hostname)`，再失败返回空串。`port_service.list_ports` 组装响应时优先取 `settings.DEVICE_LOG_ADVERTISE_HOST`，否则取探测值；探测失败给空态说明，不抛错。绑定地址仍 `0.0.0.0`。

- 备选：遍历网卡枚举 —— 否决：多网卡时无法判断哪个是设备可达的出口，出站探测法天然选对路由网卡；人工覆盖兜底。

### D4 失败语义与提示

后端：`set_enabled` / 新增 / 重试在 `_await_listening` 超时后，用 `PortDetector` 再探一次细化 note——连接探测命中 → 「端口已被其它程序占用」；否则 → 「端口绑定失败」。前端：`enabled && !listening` 统一 `ElMessage.error("端口 X 监听失败：…")`，状态胶囊新增 `is-fail` 红态（令牌取既有状态红，不新增色板）；失败行提供「重试」= 再次 `toggle {enabled:true}`（死线程已被 `_drop_dead` 清理，open 会重建接收线程）。`no_log` 与失败严格区分。

### D5 接口与校验

`POST /ports/`（新增）、`PATCH /ports/<port>/`（编辑 sku/baud）、`DELETE /ports/<port>/`（删除），均仅超管（`shared.users.is_superuser`），View 只分发、写库经 api。校验：端口 1–65535 整数、与 config+custom 全量不重号、SKU 必填 ≤100 字符、波特率正整数；编辑/删除只接受 custom 行，config 行给可读拒绝（400）。删除保留日志文件。响应沿用 `{status, data}` 信封与 snake_case；列表加 `listen_ip`，行加 `origin` / `address`。

### D6 前端结构

模块私有新增 `PortFormDialog.vue`（el-dialog 全局皮肤 + `.sketch-kit` 表单，新增/编辑复用）与 `useCustomPorts.ts`（CRUD 编排 + 校验）；`useLogPorts.ts` 改失败提示与重试；`WifiPortPanel.vue` 加 IP 条、新增按钮、来源徽标、行内编辑/删除/重试；`api.ts` / `constants.ts` 同步契约与文案（波特率常用值 9600/115200/921600 + 自定义）。删除确认用 ElMessageBox，文案含「AI 验收将不再有该端口日志证据」。组件超 500 行先拆样式层再拆逻辑层。

### D7 规则与文档同步（已获批）

实现时同步改 `backend/apps/serial_log/AGENTS.md` 真相源条款为双轨口径；`frontend/src/modules/serial-log/AGENTS.md` 端点清单补三个写接口。spec 变更以本 change 的 delta 为准，归档时合入主 spec。

## 模块防火墙自检

- 跨 App import：无新增。serial_log 仍不 import ai_assistant；其它模块读开关仍经 serial_log api。
- 写库收敛：`sl_log_ports` 的全部 INSERT/UPDATE/DELETE 仍只在 `backend/apps/serial_log/api.py`（新增 create/update/delete 三个写函数）；View / port_service 不碰 ORM。
- engines 边界：`engines/uart_log` 零改动，不引入 Django；`utils/netinfo.py` 纯标准库，不反向依赖 apps。
- 前端不直连数据库；HTTP 唯一出口仍是模块 `api.ts`；无仪表盘写操作。
- 新增跨模块依赖：无。

## Risks / Trade-offs

- [多网卡探测选错 IP] → `DEVICE_LOG_ADVERTISE_HOST` 人工覆盖；页面提示「设备侧需与本机同局域网」。
- [探测与真实 bind 之间的竞态] → 既有双层兜底不变（detect + run 内 bind 捕获），失败统一走 D4 提示。
- [SKU 改名后旧通道文件成为孤儿] → 文件保留（证据不删），编辑弹窗文案明示「将更换日志文件通道名」。
- [上限语义混淆（登记数 vs 监听数）] → 新增在监听满 10 时直接拒绝；开关超限沿用既有「保留开关值但不监听 + 可读 note」。
- [回退后 custom 行残留] → 旧代码只按配置 reconcile，custom 行休眠不被监听、不上列表；重新部署即恢复，无数据丢失。
- [1 秒等待预算] → 占用探测 connect 超时 0.5s，细化 note 的二次探测最坏再 0.5s，仍在响应预算内；超时不阻塞返回。

## Migration Plan

1. 部署：`makemigrations`（加 origin 列，default=config）→ `migrate` → 新代码上线；存量开关值与配置端口行为不变。
2. 验证：全新安装 + 旧库升级两条路径演练（App 关单附加项）；配置端口监听不中断。
3. 回退：还原代码即可（custom 行休眠）；如需彻底清理再反向迁移删列——删列会丢失自定义登记，须先导出备份，默认不执行。

## Open Questions

（无——多网卡候选与保存前预探测已明确列为 P2 非目标，不影响本次 spec 与任务拆分。）