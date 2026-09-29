## Context

- 采集在引擎层：`engines/device/logbus.py` 是进程内单例，由 `apps/ai_assistant/log_evidence.py::ensure_log_evidence()` 在**首次设备任务或首次日志查询**时懒启动；配置全部来自 settings；现状只有 1 个 TCP 端口（+ 可选 1 个串口）；数据只进内存环形缓冲（600s / 20000 行），**从不落盘**。
- 引擎层约定：零 `django` / 零 `apps` 依赖，句柄不外泄，上层只调公开函数。
- 后端为**单进程** daphne（`run_daphne.py` 用 `run_with_reloader` 包装），进程内单例成立。
- 工具箱前端是装配台：左侧来源列表 `ASSEMBLY_SOURCES`（biz / skill / prompt / debug），右侧按 `activeSource` 渲染；来源的 `gateKey` 允许为空（prompt / debug 即无总闸）。
- 平台约定：写库收敛到各 App `api.py`；响应信封 `{status, data}`；字段 snake_case；`/api/` 路径以 `/` 结尾；表前缀 `ai_`；根目录 `logs/` 已在 `.gitignore`。
- 端口同一时刻只能有一个监听者；Windows 允许重复绑定，故采集前有占用探测，避免「以为在听、其实收不到」。
- 动机见 `proposal.md - Why`；行为契约见 `specs/`。

## Goals / Non-Goals

**Goals:**

- 把「日志端口来源」做成**一份登记**（端口 + SKU + 波特率），页面三列与日志文件名都由它派生，不在前端硬编码中文或数值。
- 采集启停由**开关**显式控制：状态持久化、重启自动恢复、关闭即真正释放端口。
- 采到的日志按 `{SKU}_{端口}.log` 落盘，50MB 轮转、改名存档且绝不覆盖，查看只读当前文件。
- 页面：5 列表格 + 监听开关 + 只读日志窗口（尾部行数、手动/自动刷新、同毫秒合并 + 最新在上）。

**Non-Goals:**

- 不做端口 / SKU / 波特率的页面编辑（但数据模型与采集层按「可登记多条来源」实现，避免二次改造）。
- 不启用、不删除串口直连通道（保持现状：配置驱动、不参与本开关）。
- 不改动已验收的 AI 证据链：关键词索引、环形缓冲、动作窗口与证据等级算法一律不动。
- 不把日志正文写入数据库；不改任务详情页（验收日志证据的页面渲染仍是存量遗留项）。

## Decisions

### D1 端口来源登记：settings 扩展为「端口 + SKU + 波特率」

`DEVICE_LOG_SOURCES` 由 `{端口: 通道名}` 扩展为可携带 SKU 与波特率：`{"7005": {"sku": "H6810", "baud": 921600}}`，同时保留旧简写 `{"7005": "H6810"}`（波特率回退全局值）。现场未配置该变量时，由 `DEVICE_LOG_TCP_PORT` + `DEVICE_LOG_SOURCE_SKU` + 新增 `DEVICE_LOG_SOURCE_BAUD`（默认 921600）合成一条来源。

- 引擎侧引入 `LogSourceSpec(port, sku, baud)`，`LogBusConfig.sources` 取代 `source_channels`（后者保留为兼容属性）。
- 备选「把三列存进数据库」：与「三列只读、值来自配置」相悖，且改一个数字要动后台，否。
- 备选「波特率写死在前端」：违反「中文名与展示值由后端下发、前端不硬编码」，否。

### D2 开关状态持久化：新增表 `ai_log_ports`

字段：`port`（唯一）、`sku`、`baud`、`enabled`、`updated_at`。**无记录 = 已开启**（与既有 `ai_platform_tools` 的「无记录＝启用」一致），保证升级后行为与现状（平台一直监听 7005）等价。

- 读写一律经 `apps/ai_assistant/api.py`：`list_log_ports()` / `set_log_port_enabled(port, enabled)`；视图只分发。
- 三列真相源仍是**配置**：列端口时按配置 upsert（刷新 sku / baud，保留 enabled），列表只返回配置里登记过的来源。这样页面上三列永远等于配置，开关则独立持久。
- 备选「复用 `ai_platform_tools`」：语义是工具启停，否；备选「写本地 JSON」：与「写库走 api.py」的收敛方向相悖且多进程不一致，否。

### D3 采集改为按端口启停

`LogBus` 由「一次性起全部线程 / 一次性全停」改为持有 `dict[port, 采集线程]`，新增 `start_source(port)` / `stop_source(port)` / `running_ports()`：

- 每个端口的采集线程持有**自己的**停止事件；`stop_source` 必须关闭监听 socket 并 join，确保端口被真正释放（spec 要求「其它程序可立即占用」）。
- 每个来源对应自己的 `LogFileSink`，`feed()` 时按端口写对应文件。
- 串口来源保持原样（配置驱动，不参与开关）。
- 关键词索引、环形缓冲、窗口证据逻辑不变，避免影响已验收的 AI 验收链路。

### D4 开关 → 采集的编排：新增应用层服务

新增 `apps/ai_assistant/log_port_service.py`：`reconcile()`（读开关状态 → 逐端口 ensure 总线单例 → 开/关）、`set_enabled(port, enabled)`（写库 + 只调该端口）、`list_ports()`、`read_lines(port, tail)`。

reconcile 的触发点：

1. **后端启动**：在 AppConfig 启动钩子里恢复（满足「重启后自动恢复，不需要有人打开页面」）。约束：`manage.py` 命令（migrate / check / test）与 autoreload 的父进程**不得**起采集线程——用「非 management 命令」判定 + `RUN_MAIN == "true"` 双重护栏。
2. **接口访问**：端口列表 / 开关 / 日志行三个端点每次先对该端口 reconcile（幂等且便宜），保证即使启动钩子被绕过，页面看到的监听状态也一定与库一致。
3. **AI 任务装配**：`ensure_log_evidence()` 不再隐式启动采集，只取当前已在监听的端口作为证据来源；没有运行中端口就返回 `None`（验收按「无日志证据」处理，即用户已确认的降级口径）。

幂等要求：重复打开同一端口不得产生第二个监听线程；关闭未开启的端口不报错。

### D5 日志文件模块：新增 `engines/device/logfiles.py`

- `LogFileSink(sku, port, directory, max_bytes)`：`write(line)` → 需要时创建目录 → 需要时轮转 → 追加一行 `YYYY-MM-DD HH:MM:SS.mmm [source] 原文\n`（UTF-8，行末 flush）。文件要能被记事本直接读懂，故带上时间戳与来源。
- 轮转：目标名 `{SKU}_{端口}_{YYYYMMDD}.log`；同名已存在则追加 `_2`、`_3`…；同目录 `os.replace` 改名（原子）；随后重开当前文件续写。**任何情况下不覆盖存档**，宁可留序号。
- 当前文件大小以磁盘实际大小为准（启动时 `getsize` 初始化，避免重启后计数错乱）。
- 尾部读取 `tail_lines(path, limit)`：从文件末尾按块倒读固定行数，**不把整份文件读进内存**；返回按文件原始顺序（旧→新）。
- 备选「`logging.handlers.RotatingFileHandler`」：其轮转命名是 `.1/.2` 且会滚动覆盖/删除旧文件，不满足「改名存档 + 绝不覆盖」，否。
- 合并与倒序**复用既有 `merge_lines_by_timestamp`**，保证日志窗口与 AI 查询是同一套排版口径。

### D6 落盘时机：采集线程内同步追加

在 `LogBus.feed()` 写缓冲之后同步追加到文件，不引入队列或独立写线程：日志量级为「约 3 秒一次心跳 + 事件突发」，单行 flush 让页面立刻可见，成本可接受。

- 写入失败（磁盘满 / 权限）只记录错误并继续采集、继续进内存缓冲——日志文件是加分项，不允许反过来拖垮证据链。
- 备选「内存队列 + 单写线程」：省下的那点 IO 不值得多一条异步链路与关停顺序问题，暂不做。

### D7 页面与接口

- 前端：`ASSEMBLY_SOURCES` 增第五项 `{ key: "port", name: "无线端口", gateKey: "" }`；`ToolboxPanel` 在 `activeSource === "port"` 时渲染新组件 `WifiPortPanel.vue`（＋独立 `.style.css`，避免 ToolboxPanel 越过 500 行门禁）；表格用 `el-table` + `el-switch`，日志窗口用 `el-drawer`（刷新 / 自动刷新 / 行数选择）；HTTP 全部走 `api/toolbox.ts`。
- 接口（本 App，管理面，**不走** `/api/ai/tools/` 内部网关）：
  - `GET  /api/ai/log-ports/` → 每端口：`port / sku / baud / enabled / listening / log_file / size_bytes`
  - `POST /api/ai/log-ports/toggle/`（仅超管）body `{port, enabled}` → 返回生效后的该端口状态
  - `GET  /api/ai/log-ports/<int:port>/lines/?tail=2000` → `{port, sku, log_file, line_count, raw_line_count, lines, conclusion}`，`conclusion` ∈ `ok` / `no_log` / `port_not_configured` / `port_disabled`
- 文件名由后端按登记来源拼装，前端**不传文件名**（杜绝路径穿越）；`tail` 有上下限，超限即夹紧。
- 权限：列表与日志行——已登录即可；开关——仅超级管理员（沿用 `permissions._is_superuser`）。

### D8 AI 侧口径变化（只增不减）

- `read_device_log` 工具：查询前 reconcile 一次；未登记端口 → `port_not_configured`；已登记但关闭 → `port_disabled`；两者都是**正常返回**（不抛错、不连端口、不开监听）。
- 工具网关 `POST /api/ai/tools/log/read/` 与工具箱调试入口的请求/响应形状不变，只多一个 `conclusion` 取值。

## 模块防火墙自检

- **跨 App import**：无新增。开关表 `ai_log_ports` 只由 `apps/ai_assistant` 读写；写操作全部收敛在 `apps/ai_assistant/api.py`，视图/服务只调用它。
- **跨 App service/runner import**：无。新增的 `log_port_service.py` 属本 App 内部，不被其它 App 引用。
- **引擎边界**：新增 `engines/device/logfiles.py` 保持零 `django` / 零 `apps` 依赖，只接收「目录、上限、SKU、端口」等标准库参数；上层（`apps`）只调公开函数，不持有文件句柄或 socket。
- **写库路径**：无直接 ORM 写。新增/修改/删除仅出现在 `api.py`（`list_log_ports` 的 upsert 与 `set_log_port_enabled` 也在此处）。
- **前端**：新增调用只经 `api/toolbox.ts` → `shared/api-client`，不新增裸 `fetch`/`axios`，不直连数据库。
- **通道收敛**：新增 3 个端点挂在既有 DRF 出口下，未新增 WS 生产点，未绕开 `/api` 出口。

## Risks / Trade-offs

- [关闭端口后 AI 验收失去日志证据（用户已确认的取舍）] → 关闭时页面明确提示；任务侧按「无日志证据」如实标注；开关状态持久化，避免「忘了开」被误读成能力故障。
- [单进程假定：同端口只能有一个监听者] → 启动前占用探测 + 明确错误日志（不静默）；reconcile 幂等；当前部署是单进程 daphne。若将来换多 worker，只有最先绑定者采集、其余记录错误，不会重复写文件。
- [启动钩子在 autoreload 下会跑两次] → `RUN_MAIN == "true"` + 非 management 命令双重护栏；漏跑的兜底是「打开页面/调接口即 reconcile」。
- [每行 flush 的磁盘开销与磁盘写满] → 日志量级小；写失败只记错误、不中断采集、不影响内存缓冲与证据链。
- [50MB 文件的读取性能] → 只做尾部定长倒读（默认 2000 行），不整文件加载。
- [同一天多次轮转命名冲突] → 存档名追加序号；宁可留多余文件也绝不覆盖。
- [配置与库中三列不一致] → 每次列端口以配置为准 upsert，页面上三列恒等于配置；开关值单独保留、不被 upsert 覆盖。

## Migration Plan

1. **迁移**：新增 `ai_log_ports` 表（初始为空即可；来源在首次读取时按配置 upsert）。
2. **配置新增**：`DEVICE_LOG_LOG_DIR`（默认 `<BASE_DIR>/logs`）、`DEVICE_LOG_FILE_MAX_BYTES`（默认 `52428800` = 50MB）、`DEVICE_LOG_SOURCE_BAUD`（默认 `921600`）、`DEVICE_LOG_TAIL_LINES`（默认 `2000`，及其上限）。现场来源仍为 `7005 / H6810`。
3. **行为等价**：无记录 = 已开启 → 升级后平台照旧持续监听 7005，不因本变更突然停采。
4. **回滚**：回退代码 + 删除该表迁移即可回到「只在内存采集」；已生成的日志文件保留在 `logs/`，不回滚、不删除。
5. **数据**：存量内存中的日志不迁移；日志文件从本次上线开始记录。

## Open Questions

- 存档文件是否需要页面入口（本次只保留在目录、不读取、不展示）→ 按需另立变更。
- 任务详情页展示验收阶段的日志证据（存量遗留项）→ 不在本变更范围。
