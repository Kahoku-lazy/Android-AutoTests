## Why

D0（边界与配置）复查（静态 + 实跑门禁）后剩余的 D0 内问题，逐条有实测证据：

| # | 项 | 级别 | 证据 |
|---|----|:--:|------|
| 1 | `.env.example` 未覆盖 5 个代码读取的 D0 运维开关 | 🟠 | 全文（88 行，含注释）0 提及：`DEVICE_ENGINE` · `AI_ENGINE`（分层文档写明的**唯二插槽开关**，且 ARCH-00 §七 已列）· `ADMIN_USERS` · `REDIS_URL` · `UPLOAD_CLEANUP_MAX_AGE_DAYS` |
| 2 | `run.py` 3 处空 `except: pass`，无注释说明忽略原因 | 🟡 | `run.py:104`（杀进程）· `:197`（KILL 连接）· `:203`（清理入口）；违反根 `AGENTS.md`「错误不应默默忽略 / 要忽略必须注释」 |
| 3 | D0 内唯一 DB 直连（运维动作）未登记 | 🟡 | `run.py::cleanup_mysql_connections()`：`information_schema.PROCESSLIST` 查询 + `KILL <pid>`，与 D0「不做查询/写库」契约有张力 |
| 4 | `config/test_settings.py` 覆盖 `DB_ENGINE = "sqlite"` 但无消费者 | 🟡 | `DB_ENGINE` 全仓引用只有 `run.py` / `.env*` / `settings.py`，测试侧无人读它；真正生效的是紧随其后的 `DATABASES` 覆盖 |
| 5 | 本地 `.env` 残留两个零引用键 | 🟡 | `AGENTSCOPE_PORT` · `SCREENSHOT_INTERVAL` 全仓 0 命中（`.env` 为 gitignored，不随仓库分发） |

## What Changes

- `.env.example`：补齐 5 个开关（引擎插槽新增一段；Redis 段补 `REDIS_URL`；Admin 段补 `ADMIN_USERS`；维护段补 `UPLOAD_CLEANUP_MAX_AGE_DAYS`），全部按「默认值 + 作用 + 真相源」注释
- `run.py`：3 处空 except 各补一句**说明忽略原因**的注释；清理入口的兜底 except 由静默改为打印一行可诊断线索（`MySQL cleanup skipped: <原因>`）
- `ARCH-00 §七 部署架构`：在「一键启动/停止」块内登记**运维例外** —— `run.py stop` 的 MySQL 孤儿连接清理属 best-effort 运维动作，不承载业务读写
- `config/test_settings.py`：删掉无消费者的 `DB_ENGINE = "sqlite"` 赋值（`DATABASES` 覆盖才是生效机制）
- 本地 `.env`：删除 `AGENTSCOPE_PORT` / `SCREENSHOT_INTERVAL` 两个零引用键（gitignored，不入库）
- **BREAKING**：无（配置示例与注释；`run.py` 仅多一行诊断输出）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- D0 定义与开关总表：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七 部署架构（关键开关清单）· `dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html`（D0 层定义，gitignored）
- 规则：根 `AGENTS.md`（错误不应默默忽略 / 忽略必须注释）· `.agents/skills/django-backend-check/references/calibration.md`
- 前置：`G1`（`stabilize-drifted-index-names`，本轮 D0 复查扫出的 🔴，已单独关单）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 配置示例：`.env.example`（+5 个开关说明）
- 运维脚本：`run.py`（3 处注释 + 1 行诊断输出）
- 架构文档：`ARCH-00` §七（+3 行运维例外）· 测试配置 `config/test_settings.py`（−1 行死赋值）
- 本地环境：`.env`（−2 个残留键，不入库）
- 验证：`manage.py check` 0 issues · `makemigrations --check` 仍 exit 0 · `ruff check` / `ruff format --check` · D0 单测（14）回归 · `python run.py status` 冒烟
