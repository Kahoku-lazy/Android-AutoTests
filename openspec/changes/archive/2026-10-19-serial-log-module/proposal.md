## Why

「无线端口」与「日志关键词」现在寄生在 AI 工具箱里，代码也散落在 `apps/ai_assistant`（`log_port_service.py`、`log_keywords.py`、`views_log_*_drf.py`、`AILogPort` 模型、启动恢复钩子）。串口日志是数据面能力，与 AI 助手没有归属关系：入口放错位置让人找不到，后端也没有独立模块承接采集配置、端口开关与关键词表。现在把前后端各收成一个独立模块，为后续串口日志能力（导出、检索、多来源）留出边界。

## What Changes

- **后端新建 `apps/serial_log`**：承接端口登记、监听开关持久化（`sl_log_ports`）、启停编排、当前日志文件只读、关键词对照表组装与启动恢复；路由 `/api/serial-log/`，四个端点：
  - `GET /api/serial-log/ports/`
  - `POST /api/serial-log/ports/toggle/`（仅超管）
  - `GET /api/serial-log/ports/<int:port>/lines/`
  - `GET /api/serial-log/keywords/`
  - **BREAKING**：旧路径 `/api/ai/log-ports/…`、`/api/ai/log-keywords/` 下线，不设别名（同一资源不得两种写法）。
- **监听开关状态迁移**：`ai_log_ports` 的行复制到 `sl_log_ports` 后删旧表，已关闭的端口升级后仍保持关闭。
- **AI 工具注册结构收缩**：`AILogPort` 模型、`log_port_service.py`、`log_keywords.py`、`log_evidence.py`（迁后只剩空壳）与四个端点从 `apps/ai_assistant` 移除；启动恢复钩子从 `AiAssistantConfig` 移到 `SerialLogConfig`。
- **超管判定上移**：`shared/users.py` 新增 `is_superuser()`，`ai_assistant` 与 `serial_log` 共用，不再各写一份。
- **前端新建 `modules/serial-log`**：侧栏「数据」分组末尾新增「串口日志」，页内两个 Tab（无线端口 / 日志关键词），把原 `WifiPortPanel`、`LogKeywordPanel` 及其 composable / helper / API 封装整体迁入。
- **AI 工具箱收缩为两源**：`ASSEMBLY_SOURCES` 只保留「平台业务」「自定义 Skill」，两个无总闸来源及其面板从工具箱移除。
- 本次不动 `dev_docs` 文档，不改关键词表文件与采集引擎（`engines/uart_log`、`utils/logs`、`logs/serial_logs/` 的行格式与轮转规则）。

## 关联文档

无关联需求编号：本次是模块归属与入口迁移 + 后端代码搬迁，不新增业务规则，`dev_docs`（PRD / 接口文档）本次不动；验收口径以本变更的 specs 为准。

## Capabilities

### New Capabilities

- `serial-log-module`: 后端 `apps/serial_log` 的模块归属与边界——端口登记、监听开关持久化（`sl_log_ports`）、启停编排、当前日志文件只读、关键词对照表、启动恢复、四个端点契约与旧表迁移口径。
- `serial-log-page`: 前端入口与页面——侧栏「数据」分组末尾的「串口日志」、两个 Tab（无线端口 / 日志关键词）、超管可写 / 普通用户只读、页内不持有 AI 装配语义。

### Modified Capabilities

- `device-log-port-console`: 入口由「AI 工具箱的无线端口区块」改为「串口日志页的无线端口 Tab」；端口管理接口路径改为 `/api/serial-log/ports/…`；五列表格、开关语义、日志窗口与权限口径不变。
- `device-log-keyword-catalog`: 入口由「AI 工具箱的工具来源」改为「串口日志页的日志关键词 Tab」；目录接口路径改为 `/api/serial-log/keywords/`；三列、只读、搜索与计数口径不变。

## Impact

- 后端：新增 `apps/serial_log/`（apps/models/api/port_service/keywords/sources/views/urls/migrations/AGENTS）；修改 `apps/ai_assistant/{apps,api,models,urls}.py` 并删除 `log_port_service.py`、`log_keywords.py`、`log_evidence.py`、`views_log_ports_drf.py`、`views_log_keywords_drf.py`；修改 `config/settings.py`（INSTALLED_APPS、中文 Swagger tag、App 数量注释）、`config/urls.py`、`shared/users.py`。
- 数据：新增表 `sl_log_ports`，迁移后删除 `ai_log_ports`；迁移顺序：建表 → 复制 → 状态删除 + 删旧表。
- 前端：新增 `frontend/src/modules/serial-log/`（routes/api/constants/components/composables/helpers/index/AGENTS）；修改 `ai-assistant`（工具箱来源、常量、API、测试）、`shared/components/sidebarNavConfig.ts`、`src/router.ts`、`shared/icons/lucide-registry.ts`。
- 测试：前端迁移 3 个用例到 `frontend/tests/serial-log/p0/`，改写 2 个工具箱用例并新增页面冒烟用例；后端新增 `tests/api/test_serial_log_api.py`（未登录 401 / 普通用户可读 / 超管可切 / 未登记端口 400）。
- 不改：采集引擎、日志文件格式与轮转、关键词表文件、AI 引擎工具 `engines/agents/tools/tool_serial.py`、`DEVICE_LOG_*` 配置键。
