## Context

现状见 proposal.md - Why。方案必须满足的既有约束：

- 后端 App 边界（`apps/AGENTS.md`）：View 只分发、写库走 `api.py`、跨 App 只能 import Model（只读）或对方 `api.py`，禁止跨 App import service/runner 等内部实现；
- 响应信封 `{status, data}`、HTTP 字段 snake_case、`/api/` 路径尾斜杠（`api-path-convention`）；
- 采集与文件格式不动：`engines/uart_log`、`engines/device/logbus`、`utils/logs`、`logs/serial_logs/{SKU}_{端口}.log`；
- 前端：每模块 `api.ts` 是唯一 HTTP 出口（走 `shared/api-client`），页面 L2–L5，跨模块组件放 `shared/`；
- 本次不动 `dev_docs`。

## Goals / Non-Goals

**Goals:**

- 后端有一个独占端口开关状态的 `apps/serial_log`，四个端点、启动恢复、关键词组装都在它内部闭环；
- 升级不丢监听开关状态，旧表与旧代码干净移除；
- 前端「数据」分组末尾有一个「串口日志」页面，两个 Tab 承载原有两个面板，权限口径不变；
- AI 工具箱只剩「平台业务 / 自定义 Skill」，且不再有这两个来源的任何装配语义。

**Non-Goals:**

- 不新增串口日志业务能力（导出、服务端检索、多端口批量操作等都不做）；
- 不改采集引擎、日志行格式、轮转规则、关键词表文件格式；
- 不搬 `engines/agents/tools/tool_serial.py`（它是智能体工具，不是本模块 HTTP 面）；
- 不改 `DEVICE_LOG_*` 配置键与运维方式；
- 不保留旧 URL 别名，不提供兼容层。

## Decisions

### D1 后端独立 App：`apps/serial_log`

- 名称与前端 `serial-log` 对齐；`verbose_name = "串口日志"`。
- 备选：① 继续留在 `apps/ai_assistant`（模块归属与入口都错，否决）；② 叫 `apps/device_log`（与前端命名不一致，且 OpenSpec 里 `device-log-*` 描述的是行为能力而非模块，否决）。
- 依赖方向：`serial_log` → `shared` / `engines` / `utils` / Django；**不 import `apps.ai_assistant` 任何东西**，`ai_assistant` 也不再引用端口服务。

### D2 端点路径 `/api/serial-log/ports|keywords/`

- 端点：`GET /ports/`、`POST /ports/toggle/`、`GET /ports/<int:port>/lines/`、`GET /keywords/`；尾斜杠、信封、snake_case 不变。
- 备选：沿用 `/api/serial-log/log-ports/`（重复词，且旧文档里已有 `log-ports` 心智，否决）；保留 `/api/ai/…` 旧路径（等于没拆模块，否决）。
- Swagger：`SPECTACULAR_SETTINGS.TAGS` 增加中文 `serial_log` 分组说明，否则违反「每个 tag 有中文说明」。

### D3 表与迁移：`sl_log_ports`，三步迁移

- 模型 `LogPort`（port 唯一 / sku / baud / enabled 默认 True / updated_at），`db_table = "sl_log_ports"`；无记录＝开启的语义保持。
- 迁移顺序：
  1. `serial_log/0001_initial`：建 `sl_log_ports`；
  2. `serial_log/0002_copy_port_state`：`RunPython` 在旧表存在时复制 `port/sku/baud/enabled/updated_at`，缺失则跳过（全新安装）；只依赖旧表建表迁移 `ai_assistant.0045_ailogport`，不与 AI 助手的其它在途迁移互相锁死；
  3. `ai_assistant/0054_remove_ailogport`：`SeparateDatabaseAndState`，状态层 `DeleteModel`、数据库层 `DROP TABLE IF EXISTS ai_log_ports`，依赖 `serial_log.0002` 与 `ai_assistant.0053`。
- 备选：① 直接 `AlterModelTable` 把表改名（跨 App 迁移图无法干净表达状态归属，否决）；② 保留 `ai_log_ports` 表名只换 App（前缀规范 `ai_` 会误导，否决）；③ 不迁移状态（用户会莫名多出监听端口，否决）。

### D4 超管判定上移 `shared/users.py`

- 新增 `is_superuser(user_id)`；`apps/ai_assistant/permissions._is_superuser` 改为委托它；`serial_log` 视图直接用 shared 版本。
- 备选：在 `serial_log` 里复制一份查询（两份权限逻辑，后续容易漂移，否决）。

### D5 启动恢复钩子随模块迁移

- `SerialLogConfig.ready()` 里起后台线程：等 `apps.ready_event` → `port_service.reconcile()`；保留「仅 ASGI 服务进程执行」与「autoreload 父进程跳过」两道守卫；`DEVICE_LOG_ENABLED` 关闭时不打开端口（沿用 `reconcile` 内既有判断）。
- `AiAssistantConfig` 只保留任务孤儿恢复，删除 `_restore_log_ports`。
- 备选：放 `gateway` 启动钩子（跨层依赖，否决）；留在 `ai_assistant` 但 import 新模块（依赖倒挂，否决）。

### D6 前端：新模块 + 两个 Tab + 面板自带样式

- `frontend/src/modules/serial-log/`：`index.vue`（WorkbenchHeader「串口日志」+ `AppTabs` 两 Tab）、`routes.ts`（`/serial-log`）、`api.ts`、`constants.ts`、`components/WifiPortPanel.vue|LogKeywordPanel.vue`（迁移）、`composables/`、`helpers/`、`AGENTS.md`。
- 侧栏：`sidebarNavConfig.ts` 数据组末尾追加；`MOD_COLORS` 映射 `--c-device`；`lucide-registry.ts` 增加 `Terminal`。
- **样式**：两个面板迁出后不再依赖 `ToolboxPanel.style.css`；各自 `scoped` 样式自带区块头 / 按钮（`WifiPortPanel` 已有镜像写法，`LogKeywordPanel` 补一份），类名从 `tb-*` 改为 `sl-*`，避免「tb = toolbox」的误导。
- 备选：抽一份全局 `sl-*` 样式文件（跨组件共享但污染全局，且两面板头部规格可能分叉，否决）；保留 `tb-*` 类名（语义错位，否决）。

### D7 测试与验证策略

- 前端：`log-port-lines`、`log-keyword-rows`、`LogKeywordPanel` 三个用例迁到 `frontend/tests/serial-log/p0/`；`toolbox-assembly-port-source`、`ToolboxPanel-keyword-source` 改写为「工具箱不再有这两个来源」；新增 `SerialLogPage` 冒烟用例（默认 Tab、切换、非超管开关禁用）。
- 后端：新增 `tests/api/test_serial_log_api.py`（未登录 401、登录可读、非超管 403、超管可切、未登记端口 400、旧路径 404）；迁移用临时 SQLite 跑 `migrate` 全链路。
- 只跑定向：`vitest` 指定文件 + `npm run lint` + `vue-tsc` + `vite build`；后端 `manage.py check` + `makemigrations --check` + `spectacular --validate` + 定向 pytest。**不跑全量回归**。

## 模块防火墙自检

- **跨 App import**：`serial_log` 不 import 任何 `apps.*`（只 import `shared` / `engines` / `utils`）；`ai_assistant` 不再 import `serial_log`。无跨 App Model 读写。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及；`port_service` 为本 App 内部编排层，只被本 App 的 View 与 `apps.py` 调用。
- **写库收敛**：`views.py` → `port_service.py` → `api.py` → ORM；`apps/serial_log/api.py` 是 `sl_log_ports` 的唯一写点；迁移文件属 schema 变更，不在此限。
- **前端不直连数据库**：页面只经 `modules/serial-log/api.ts` → `shared/api-client` 调 HTTP；无 WS / SSE 新增。
- **仪表盘不做写操作**：不涉及。
- **新跨模块依赖**：仅 `shared/users.py` 的 `is_superuser`（shared 层，允许）；另无。

## Risks / Trade-offs

- [迁移顺序写错会丢开关状态] → 三步固定顺序；`0002` 复制前后行数比对；临时 SQLite 上演练 `migrate` 全链路；生产升级前备份数据库。
- [删旧表后仍有代码引用 `AILogPort`/`log_port_service`] → 删除后全仓 grep + `manage.py check` + `makemigrations --check`；`tests/arch` 静态检查兜底。
- [旧 URL 直接 404] → 前端与后端同批上线；不设别名，避免「同一资源两种写法」。
- [`LogKeywordPanel` 迁出后掉样式] → 自带 `sl-*` 样式；浏览器逐 Tab 核对区块头 / 表格 / 空态。
- [启动恢复钩子迁移后不再恢复] → 重启实测：先关一个端口、重启、确认仍关闭；再开一个、重启、确认自动监听。
- [pytest 用 `--nomigrations`，迁移不被测试覆盖] → 单独用临时 SQLite 跑 `manage.py migrate` 验证，不依赖测试套件。
- [AI 工具箱测试仍假设四源] → 同步改写两个用例，并加「只有两源」断言，防止回归。

## Migration Plan

1. 建 `apps/serial_log`：`apps.py` / `models.py` / `api.py` / `sources.py` / `port_service.py` / `keywords.py` / `views.py` / `urls.py` / `migrations/0001`；
2. 写 `0002` 数据复制，再写 `ai_assistant/0053` 状态删除 + 删旧表；
3. 切后端代码：`config/urls.py` 挂 `/api/serial-log/`；`ai_assistant` 删模型 / 服务 / 视图 / 路由 / 启动钩子 / api 函数；`shared/users.is_superuser`；`INSTALLED_APPS` 与 Swagger tag；
4. 切前端：新模块 + 侧栏 + 路由 + 图标；AI 工具箱删两源；迁移组件 / composable / helper / API；
5. 迁移测试与文档（AGENTS）；
6. 验证顺序：后端 `check` → `makemigrations --check` → 临时库 `migrate` → `spectacular --validate` → 定向 pytest；前端 `vitest` 定向 → `lint` → `vue-tsc` → `vite build`；最后手工核对页面两 Tab 与 AI 工具箱两源。
7. 回滚：代码层 `git revert`；数据层若已执行 `0053`，需先用备份恢复 `ai_log_ports`（或从 `sl_log_ports` 反向复制），再回退迁移记录。

## Open Questions

- 无。升级窗口内采集会短暂中断（进程重启的既有行为），不属于本次改动引入的问题。
