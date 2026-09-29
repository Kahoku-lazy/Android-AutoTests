## 1. 配置与来源登记

- [x] 1.1 `config/settings.py` 新增日志文件与展示配置：`DEVICE_LOG_LOG_DIR`（默认 `<BASE_DIR>/logs`）、`DEVICE_LOG_FILE_MAX_BYTES`（默认 52428800）、`DEVICE_LOG_SOURCE_BAUD`（默认 921600）、`DEVICE_LOG_TAIL_LINES`（默认 2000）与行数上限。验证：`python manage.py check` 通过，且打印结果为 `logs / 52428800 / 921600 / 2000 20000`。
- [x] 1.2 `engines/device/logbus.py` 引入 `LogSourceSpec(port, sku, baud)`，`LogBusConfig` 增加 `sources: list[LogSourceSpec]`（`source_channels` 保留为兼容形态，`_specs()` 统一归一），`configured_ports()` / `channel_for_port()` 改为基于 `sources`。验证：`pytest tests/graybox/unit/test_device_log_bus.py tests/graybox/unit/test_device_log_read_tool.py -q` 全绿。
- [x] 1.3 `apps/ai_assistant/log_evidence.py::build_config()` 解析扩展后的 `DEVICE_LOG_SOURCES`：支持 `{"7005": {"sku": "...", "baud": ...}}` 与旧简写 `{"7005": "H6810"}`；未配置时按 `DEVICE_LOG_TCP_PORT` + `DEVICE_LOG_SOURCE_SKU` + `DEVICE_LOG_SOURCE_BAUD` 合成；非法 JSON 记录错误后退化。验证：`pytest tests/graybox/unit/test_ai_log_evidence_wiring.py -q` 全绿（含两种形态、缺省合成、非法 JSON 三个新用例）。

## 2. 日志文件模块（引擎层）

- [x] 2.1 新增 `engines/device/logfiles.py`：`LogFileSink` 追加写入 `{SKU}_{端口}.log`，行格式 `YYYY-MM-DD HH:MM:SS.mmm [source] 原文`，UTF-8，行末 flush，目录不存在时自动创建。验证：`pytest tests/graybox/unit/test_device_log_files.py -q`（逐行追加、历史保留、写后立即可读、目录自动创建、大小上报）。
- [x] 2.2 同模块实现 50MB 轮转：按实际字节数判断，写满前改名为 `{SKU}_{端口}_{YYYYMMDD}.log`，同日第二次起追加 `_2`/`_3`，绝不覆盖（含手工放置的同名存档用例）。验证：同文件 `-q` 全绿（存档名序列、轮转不丢行、既有存档不被覆盖、重启续写、日期取行时间戳）。
- [x] 2.3 同模块实现 `tail_lines(path, limit)`：从文件末尾按块倒读固定行数，不整文件加载，返回按文件原始顺序（旧→新）的行、剥离 CRLF；文件不存在返回空。验证：同文件用例覆盖「超过 limit 只取尾部」「不足 limit 全取」「空/不存在」「5 万行文件只读尾部」「CRLF」。
- [x] 2.4 校验引擎层边界：`logfiles.py` 不 import `django` / `apps`。验证：`python tools/gen_arch_stats.py --check-boundaries` → 零违规；`ruff check` + `ruff format --check` 对 `engines/device/` 通过。

## 3. 采集改为按端口启停并落盘

- [x] 3.1 `engines/device/logbus.py` 把采集线程改为按端口持有（`dict[port, 线程]`），新增 `start_source(port)` / `stop_source(port)` / `running_ports()` / `is_listening(port)`；每个端口独立停止事件。验证：`pytest tests/graybox/unit/test_device_log_bus.py -q` 全绿（含单端口启停、重复打开只留一个监听、未登记端口不启动、双端口隔离）。
- [x] 3.2 `stop_source` 真正关闭监听 socket 并 join（accept 0.5s 超时兜底）。验证：`test_stop_source_releases_the_port` 关闭后立即 `bind` 同端口成功。
- [x] 3.3 `LogBus.feed()` 在进缓冲后把该行写入对应端口的 `LogFileSink`；写入异常只记错误、不中断采集与缓冲。验证：`test_feed_writes_current_log_file` 与 `test_sink_failure_does_not_break_collection` 通过。
- [x] 3.4 保留既有证据链行为不变（窗口开/读、证据等级、合并倒序）。验证：`pytest tests/graybox/unit/test_device_log_bus.py tests/graybox/unit/test_device_log_evidence.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 全绿。

## 4. 开关持久化与编排

- [x] 4.1 `apps/ai_assistant/models.py` 新增 `AILogPort`（表 `ai_log_ports`：`port` 唯一、`sku`、`baud`、`enabled`、`updated_at`）+ 迁移 `0045_ailogport.py`。验证：`python manage.py makemigrations --check` 无遗漏、`python manage.py migrate` 成功建表。
- [x] 4.2 `apps/ai_assistant/api.py` 新增 `ensure_log_ports()`（按配置刷新三列、保留 `enabled`）、`get_log_port_enabled_map()`、`is_log_port_enabled()`、`set_log_port_enabled()`。验证：`pytest tests/graybox/unit/test_log_port_service.py -q`（无记录＝开启、upsert 不动开关、改开关落库）全绿。
- [x] 4.3 新增 `apps/ai_assistant/log_port_service.py`：`reconcile()` / `set_enabled()` / `list_ports()` / `read_lines()` / `clamp_tail()` / `disabled_port_note()`；开关打开→`start_source`，关闭→`stop_source`，幂等；开/关响应里的 `listening` 为等待绑定后的真实结果。验证：同文件用例覆盖 reconcile 开/关/幂等、set_enabled 启停并释放端口、双端口各自开关、列表运行时状态与提示。
- [x] 4.4 后端启动恢复监听：`AiAssistantConfig._restore_log_ports()` 在启动线程里 reconcile；`run_daphne.py` 给 autoreload 父进程打 `DJANGO_AUTORELOAD_PARENT` 标记并跳过（否则父进程会先占住端口）。验证：`test_startup_restore_starts_listening` 与 `test_startup_restore_skipped_in_autoreload_parent` 通过；真机重启验证见 8.1。

## 5. HTTP 接口

- [x] 5.1 新增 `GET /api/ai/log-ports/`：返回每端口的 `port / sku / baud / enabled / listening / log_file / size_bytes / note`（信封 `{status, data}`、snake_case）。验证：`pytest tests/graybox/unit/test_log_ports_api.py -q`（字段齐备、未登录 401）。
- [x] 5.2 新增 `POST /api/ai/log-ports/toggle/`：仅超级管理员，body `{port, enabled}`，返回生效后的状态；普通用户 403 且状态不变；未登记端口 400 + 可读中文说明。验证：同文件用例覆盖超管成功、普通用户 403、未登记端口、缺 port。
- [x] 5.3 新增 `GET /api/ai/log-ports/<int:port>/lines/?tail=N`：只接受已登记端口；`tail` 夹紧到上限；返回 `lines`（同毫秒合并、最新在上）、`line_count`、`raw_line_count`、`conclusion`；未登记端口 `port_not_configured`、关闭态 `port_disabled`，均不报 500；只读当前文件（存档不进结果）、文件名由后端拼装不受前端入参影响。验证：同文件用例覆盖四种结论、tail 夹紧、只读当前文件、传 `file=` 无效。
- [x] 5.4 `apps/ai_assistant/urls.py` 注册三条路由（尾斜杠约定）。验证：`python manage.py check` 通过，且 api 测试实际命中三条路径（`/api/ai/log-ports/`、`/toggle/`、`/<port>/lines/`）。

## 6. 前端「无线端口」区块

- [x] 6.1 `api/toolbox.ts` 增加三个调用（列表 / 切换开关 / 读取日志行）与 DTO 类型。验证：`npx vue-tsc --noEmit` 通过。
- [x] 6.2 `helpers/toolbox-assembly.ts` 增第五个来源 `{ key: "port", name: "无线端口", gateKey: "" }` 并扩展 `AssemblySourceKey`；`useToolboxAssembly` 的 `sourceMeta` / `sourceLiveCount` / `sourceCatalogTotal` 增 port 分支（不显示无意义的生效计数）。验证：`npx vitest run tests/ai-assistant/p0/toolbox-assembly-port-source.spec.ts` 通过（来源存在、无总闸、不进生效芯片、文案正确）。
- [x] 6.3 新增 `components/WifiPortPanel.vue`（179 行）＋ `WifiPortPanel.style.css`：5 列表格（端口 / SKU名称 / 波特率 / 监听开关 / 日志查看）、开关仅超管可操作、关闭前二次确认并提示验收降级、日志抽屉（读取行数可选、手动刷新、自动刷新、空日志提示、同毫秒合并展示），并在 `ToolboxPanel.vue`（358 行）按 `activeSource === "port"` 渲染。验证：`npx vue-tsc --noEmit`（0 错）、`npx eslint src/modules/ai-assistant`（0 error）、`npm run lint:styles` 四批全过、prettier 对本次新增/改动文件通过。
- [x] 6.4 前端渲染口径对齐：日志行直接消费后端顺序，不在前端二次排序。验证：`tests/ai-assistant/p0/log-port-lines.spec.ts` 断言装饰后顺序与输入一致、合并条内部换行保留。

## 7. AI 侧口径与工具

- [x] 7.1 `ensure_log_evidence()` 改为**不启动**采集：只取当前已在监听的端口；无运行中端口时返回 `None`。验证：`pytest tests/graybox/unit/test_ai_log_evidence_wiring.py tests/graybox/unit/test_ai_workflow_log_evidence.py -q` 全绿（含「没有任何端口在监听时返回 None」「有端口在监听时给出提供者」两个用例）。
- [x] 7.2 `tools.py::read_device_log` 增加关闭态口径：**只读**开关状态（不 reconcile，避免只读工具顺手打开监听），已登记但关闭 → `conclusion=port_disabled` + `note="端口 7005 已关闭监听"`，行数 0。验证：`pytest tests/graybox/unit/test_device_log_read_tool.py -q` 全绿（关闭态、默认端口关闭态、查询不启动采集、重新打开后恢复）。
- [x] 7.3 确认 AI 验收链路在「端口关闭」时按无日志证据如实呈现（不报错、不误判通过）。验证：`pytest tests/graybox/unit -k "log_evidence or verifier_log or workflow_log" -q` 全绿。

## 8. 端到端与关单

- [x] 8.1 真机验证：平台启动后不改开关即持续收到 H6810 推来的 7005 日志并落 `logs/H6810_7005.log`。验证结果：后端重启日志 `Device log ports enabled after startup: [7005]`；`netstat` 显示 `0.0.0.0:7005 LISTENING` 且 `192.168.34.73 → 7005 ESTABLISHED`；文件 8 秒内由 348 → 6429 字节，尾部可见设备原文（`gap`/`light_switch`/`ram free heap size`）。
- [x] 8.2 真机验证开关：页面关闭开关后端口释放、可被其它程序立即占用；重新打开后恢复采集。验证结果：`temps/verify_port_release.py` — 关闭后 `listening=false` 且本机 `bind 0.0.0.0:7005` 成功（真正释放）；重开后 `listening=true`，日志文件恢复增长（7299 → 7386 字节）。
- [x] 8.3 真机验证轮转：临时把单文件上限改为 1024 字节（`.env` 备份后追加，验证完原样还原）。验证结果：重启后立刻生成存档 `H6810_7005_20260928.log`（7908 字节，内容为轮转前的全部行），继续写满后生成 `H6810_7005_20260928_2.log`（935 字节），第一份存档未被覆盖；还原配置并重启后当前文件 1455 字节（>1KB）且不再轮转，即上限恢复默认 50MB。
- [x] 8.4 页面验收：AI 工具箱「无线端口」显示 5 列、开关可操作、日志窗口能看尾部日志并自动刷新、关闭态给出可读提示。验证结果：`temps/check_wifi_port_page.py`（Playwright 实操作）— 左侧来源含「无线端口 / 监听开关 · 原始日志 · 不交给助手」；表头恰为 `['端口','SKU名称','波特率','监听开关','日志查看']`；首行 `['7005','H6810','921600','监听中','日志查看']`；抽屉标题 `H6810 · 端口 7005 · H6810_7005.log`，行数摘要 `44 条（原始 48 行，同毫秒已合并）`，最新时间在最上面，合并条按发生顺序换行渲染，自动刷新开关存在。截图：`temps/wifi_port_panel.png`、`temps/wifi_port_log_drawer.png`。
- [x] 8.5 关单门禁全部通过：`python manage.py check`（0 issues）、`makemigrations --check`（No changes detected）、`ruff check`（涉及路径全过）、`ruff format --check`（涉及路径全过）、后端最小测试集 **147 passed**、`npx vitest run tests/ai-assistant`（**18 文件 / 116 passed**）、`npx vue-tsc --noEmit`（0 错）、`npx eslint src/modules/ai-assistant`（0 error）、`npm run lint:styles`（四批全过）、`openspec validate add-device-log-port-console --strict`（valid）。
