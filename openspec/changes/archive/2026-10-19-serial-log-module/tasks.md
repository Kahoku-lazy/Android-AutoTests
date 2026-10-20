## 1. 后端模块骨架

- [x] 1.1 新建 `apps/serial_log/`（`__init__.py`、`apps.py` 的 `SerialLogConfig`：`name="apps.serial_log"`、`verbose_name="串口日志"`、`ready()` 内起后台线程等 `apps.ready_event` 后调 `port_service.reconcile()`，保留「仅 ASGI 服务进程」与「autoreload 父进程跳过」两道守卫），并把 `apps.serial_log` 加进 `config/settings.py` 的 `INSTALLED_APPS`（同步把「11 个」注释改成 12 个）。验证：`python manage.py check` 通过且 `python -c "from apps.serial_log.apps import SerialLogConfig; print(SerialLogConfig.name)"` 输出 `apps.serial_log`。
- [x] 1.2 写 `apps/serial_log/models.py` 的 `LogPort`（port 唯一、sku、baud、enabled 默认 True、updated_at；`db_table="sl_log_ports"`）与 `apps/serial_log/api.py` 四个写读函数（`ensure_log_ports` / `get_log_port_enabled_map` / `is_log_port_enabled` / `set_log_port_enabled`），语义与旧 `apps/ai_assistant/api.py:356-395` 一致。验证：`python manage.py makemigrations serial_log` 生成 `0001_initial`，临时 SQLite `migrate` 后 `sl_log_ports` 存在。
- [x] 1.3 把端口来源登记搬为 `apps/serial_log/sources.py`（原 `apps/ai_assistant/log_evidence.py` 的 `source_specs`/`_specs_from_mapping` 原样迁入，仅改模块 docstring）。验证：`python -c` 在 `config.settings` 下调用 `sources.source_specs()`，返回现场端口 7005 / H6810 / 921600。
- [x] 1.4 搬 `apps/serial_log/port_service.py`（原 `apps/ai_assistant/log_port_service.py`）：`reconcile` / `set_enabled` / `list_ports` / `read_lines` / `disabled_port_note` / `LogPortUnknown`，内部改成 `from . import api, sources`。验证：`python -c "from apps.serial_log import port_service; print(port_service.list_ports())"` 在测试配置下不报错。
- [x] 1.5 搬 `apps/serial_log/keywords.py`（原 `apps/ai_assistant/log_keywords.py`），逻辑与 `collect_keywords()` 返回值不变。验证：`python -c "from apps.serial_log import keywords; d=keywords.collect_keywords(); print(d['keyword_count'])"` 输出与旧接口一致的关键词数。
- [x] 1.6 写 `apps/serial_log/views.py` + `urls.py`：四个端点（`ports/`、`ports/toggle/`、`ports/<int:port>/lines/`、`keywords/`，尾斜杠、信封、snake_case），超管判定用 `shared.users.is_superuser`，保留「reconcile 失败不拖垮列表/读行」的 try/except 与 `@extend_schema`。验证：`python manage.py check` 通过，`python -c "from django.urls import resolve; print(resolve('/api/serial-log/ports/').url_name)"` 命中新路由。

## 2. 数据迁移与旧模块清理

- [x] 2.1 写 `apps/serial_log/migrations/0002_copy_port_state.py`：旧表 `ai_log_ports` 存在时复制 `port/sku/baud/enabled/updated_at` 到 `sl_log_ports`（逐行 `update_or_create`，按 port 幂等），不存在时直接返回。验证：临时 SQLite 先建旧表并插入一行 `enabled=False`，跑 `migrate` 后 `sl_log_ports` 里该端口仍为 `False`。
- [x] 2.2 写 `apps/ai_assistant/migrations/0054_remove_ailogport.py`：`SeparateDatabaseAndState`（`state_operations=[DeleteModel("AILogPort")]`、`database_operations=[RunSQL("DROP TABLE IF EXISTS ai_log_ports")]`），依赖 `("ai_assistant", "0053_retire_ai_chat_surface")` 与 `("serial_log", "0002_copy_port_state")`。验证：`python manage.py makemigrations --check` 无待生成迁移，临时库 `migrate` 后 `ai_log_ports` 不存在且 `sl_log_ports` 数据仍在。
- [x] 2.3 `shared/users.py` 新增 `is_superuser(user_id)`；`apps/ai_assistant/permissions._is_superuser` 改为委托它。验证：`python manage.py check` 通过，`python -c "from shared.users import is_superuser; print(is_superuser(''))"` 输出 `False`。
- [x] 2.4 删除 `apps/ai_assistant` 的端口/关键词实现：`log_port_service.py`、`log_keywords.py`、`log_evidence.py`、`views_log_ports_drf.py`、`views_log_keywords_drf.py`，并移除 `api.py` 的 `AILogPort` 导入 / 四个函数 / `__all__` 条目、`models.py` 的 `AILogPort`、`urls.py` 的四条路由与 import、`apps.py` 的 `_restore_log_ports` 调用与实现。验证：`grep -rn "log_port_service\|log_keywords\|AILogPort\|log_evidence" apps/ai_assistant` 无输出，`python manage.py check` 通过。
- [x] 2.5 改 `config/urls.py` 增加 `path("api/serial-log/", include("apps.serial_log.urls"))`，并在 `SPECTACULAR_SETTINGS.TAGS` 增加 `{"name": "serial_log", "description": "串口日志：端口监听开关、当前日志查看与关键词对照表"}`。验证：`python manage.py spectacular --validate` 报 Errors 0、Warnings 不新增，`/api/schema/` 中出现 `serial_log` 分组。

## 3. 后端验证

- [x] 3.1 新增 `tests/api/test_serial_log_api.py`：未登录 401；普通登录 200 可读列表 / 关键词；普通用户 toggle 403；超管 toggle 200 且值落库；未登记端口 400 + 可读中文；旧路径 `/api/ai/log-ports/`、`/api/ai/log-keywords/` 返回 404。验证：`python -m pytest tests/api/test_serial_log_api.py -q` 全绿。
- [x] 3.2 临时库演练迁移往返：在 `temps/` 写一次性脚本，建空 SQLite → `migrate` → 断言 `sl_log_ports` 存在、`ai_log_ports` 不存在；再模拟旧库（建 `ai_log_ports` 插两条，一条 `enabled=False`）→ `migrate` → 断言状态保留、旧表被删。验证：脚本输出 `PASS` 且临时库文件不留在仓库根（放 `temps/`）。
- [x] 3.3 跑后端门禁：`python manage.py check`、`python manage.py makemigrations --check --dry-run`、`ruff check apps/serial_log apps/ai_assistant shared`、`python tools/gen_arch_stats.py --check-boundaries`。验证：四条命令退出码均为 0。

## 4. 前端模块骨架

- [x] 4.1 新建 `frontend/src/modules/serial-log/`：`routes.ts`（`/serial-log`，`meta.title="串口日志"`）、`index.vue` 壳（`doc-page doc-page--fixed wb-shell` + `WorkbenchHeader` title「串口日志」+ `AppTabs` 两 Tab 占位）、`constants.ts`、`api.ts`（四个 fetcher 指向 `/serial-log/ports/`、`/serial-log/ports/toggle/`、`/serial-log/ports/${port}/lines/`、`/serial-log/keywords/`）。验证：`cd frontend; npx vue-tsc --noEmit` 通过。
- [x] 4.2 接线：`src/router.ts` 汇总 `serial-log/routes`；`shared/components/sidebarNavConfig.ts` 数据组末尾加 `{ path: "/serial-log", icon: "terminal", label: "串口日志" }` 与 `MOD_COLORS` 的 `--c-device` 映射；`shared/icons/lucide-registry.ts` 注册 `Terminal`。验证：`npx vite build` 通过，侧栏配置数组顺序为 设备管理→设备检查器→元素定位→页面流→串口日志。
- [x] 4.3 迁移两个面板与数据层：`components/WifiPortPanel.vue`、`LogKeywordPanel.vue`、`composables/useLogPorts.ts`、`useLogKeywords.ts`、`helpers/log-port-lines.ts`、`log-keyword-rows.ts` 从 `modules/ai-assistant` 挪到 `modules/serial-log`；import 全部改新路径；`api` 引用改 `../api`。验证：`grep -rn "log-port-lines\|log-keyword-rows\|useLogPorts\|useLogKeywords\|WifiPortPanel\|LogKeywordPanel" frontend/src/modules/ai-assistant` 无输出，`npx vue-tsc --noEmit` 通过。
- [x] 4.4 面板样式自带：把两个面板模板里的 `tb-cat-head` / `tb-cat-title` / `tb-cat-sub` / `tb-cat-actions` / `tb-cat-body` / `tb-btn` 改为 `sl-*`，并在各自 style 文件里补齐等价规则（`WifiPortPanel` 已有镜像块可直接改名，`LogKeywordPanel` 新补一份）；页面只提供 Tab 条与容器布局。验证：`npx vite build` 通过，浏览器/组件快照中两个 Tab 的区块头有边框与背景，不依赖 `ToolboxPanel.style.css`。
- [x] 4.5 页面行为接完：`index.vue` 用 `AppTabs`（默认 `ports`），`can-manage` 由 `useAuthUser().isSuperuser` 传给端口面板；两个 Tab 内容分别渲染 `WifiPortPanel` / `LogKeywordPanel`；切 Tab 不发写请求。验证：新增组件用例断言默认 Tab、切换后关键词表出现、非超管时开关 `disabled`。

## 5. AI 工具箱收缩

- [x] 5.1 `helpers/toolbox-assembly.ts`：`ASSEMBLY_SOURCES` 只留 `biz` 与 `skill`，`AssemblySourceKey` 收为 `"biz" | "skill"`；`useToolboxAssembly` 中无总闸分支保持可用（无来源时不再显示 meta）。验证：`grep -n "port\|keywords" frontend/src/modules/ai-assistant/helpers/toolbox-assembly.ts` 无来源定义，`npx vue-tsc --noEmit` 通过。
- [x] 5.2 `components/ToolboxPanel.vue` 删除 `WifiPortPanel` / `LogKeywordPanel` 的 import 与两个 `v-if` 分支；`api/toolbox.ts` 删除 `LogPort*` / `LogKeyword*` 类型与四个 fetcher；`constants.ts` 删除 `LOG_KEYWORD_*` 常量。验证：`grep -rn "LogKeyword\|LogPort\|log-port\|log-keyword" frontend/src/modules/ai-assistant` 无输出，`npx vite build` 通过。
- [x] 5.3 更新 `frontend/src/modules/ai-assistant/AGENTS.md`：工具来源由「四源」改为「两源」（平台业务 / 自定义 Skill），删掉无线端口与日志关键词的长段描述，改为一句「串口日志见 serial-log 模块」。验证：文档内不再出现 `WifiPortPanel` / `LogKeywordPanel` / 「四源」。

## 6. 前端测试与门禁

- [x] 6.1 迁移用例：`frontend/tests/ai-assistant/p0/log-port-lines.spec.ts`、`log-keyword-rows.spec.ts`、`LogKeywordPanel.spec.ts` 挪到 `frontend/tests/serial-log/p0/` 并改 import 为 `@/modules/serial-log/...`。验证：`cd frontend; npx vitest run tests/serial-log` 全绿。
- [x] 6.2 改写工具箱用例：`toolbox-assembly-port-source.spec.ts` 改为断言「来源只有 biz/skill、不存在 port/keywords、无总闸来源集合为空」；`ToolboxPanel-keyword-source.spec.ts` 改为断言「工具箱不渲染日志关键词来源与面板」。验证：`npx vitest run tests/ai-assistant` 全绿。
- [x] 6.3 新增 `frontend/tests/serial-log/p0/SerialLogPage.spec.ts`：默认选中无线端口、点击关键词 Tab 后渲染表格、非超管开关禁用、切 Tab 不触发 toggle 调用。验证：同命令通过。
- [x] 6.4 跑前端门禁：`cd frontend; npx vitest run tests/serial-log tests/ai-assistant; npm run lint; npx vue-tsc --noEmit; npx vite build`。验证：本次触及范围全绿（6 文件 33 用例、lint、build、style-gates）；`useTaskPublish.spec.ts` 3 例与 `TaskInputPanel.spec.ts` 1 例为并行变更（未提交的 `useTaskPublish.ts` / `TaskInputPanel.vue`）遗留，`vue-tsc` 仅报该文件，与本变更无关。

## 7. 模块文档

- [x] 7.1 新增 `frontend/src/modules/serial-log/AGENTS.md`：入口 `/serial-log`、两 Tab、数据来源、超管权限、只读边界、`sl-*` 私有样式、禁止把这两个面板挪回工具箱。验证：文件存在且内容与 `ASSEMBLY_SOURCES` 现状一致。
- [x] 7.2 新增 `apps/serial_log/AGENTS.md`：模块职责、表 `sl_log_ports` 唯一写点、四端点、启动恢复、禁止反向 import `apps.ai_assistant`。验证：文件存在且与 `urls.py` 四路由逐条对应。

## 8. 收尾与验收

- [x] 8.1 全仓残留检查：`grep -rn "api/ai/log-ports\|api/ai/log-keywords\|ai_log_ports\|AILogPort\|log_port_service" --include=*.py --include=*.ts --include=*.vue .`（排除 `openspec/changes/archive` 与迁移 0045）无业务代码命中。验证：输出只剩历史迁移与归档文档。
- [x] 8.2 运行时验证：`python run.py start` → 打开 `/serial-log` 两 Tab 均正常、开关状态与升级前一致；AI 工具箱只剩两源；`python run.py stop`。验证：页面与接口实测通过，日志 `logs/serial_logs/` 继续追加。
- [x] 8.3 归档：`openspec validate serial-log-module --strict` 通过后执行 `openspec archive serial-log-module`，确认 `openspec/specs/` 新增 `serial-log-module`、`serial-log-page`，两份旧规格入口口径已更新。验证：`openspec list --specs` 出现新能力，`git status` 只有预期文件。
