## 1. 复核

- [x] 1.1 `.env.example` 缺口；验证：对 52 个代码读取的 env 名与 `.env.example` 全文（88 行，含注释）比对 → 缺 `DEVICE_ENGINE` / `AI_ENGINE` / `ADMIN_USERS` / `REDIS_URL` / `UPLOAD_CLEANUP_MAX_AGE_DAYS`（`LOG_LEVEL` 已有；`DB_PASSWORD` 等属误报）
- [x] 1.2 `run.py` 三处空 except；验证：`:104`（`_kill` 竞态）· `:197`（单连接 KILL）· `:203`（外层兜底）均为 `except Exception: pass` 且无注释
- [x] 1.3 `DB_ENGINE` 测试侧消费者；验证：全仓引用仅 `config/settings.py`（定义/分支）· `run.py`（×2）· `.env` / `.env.example`，测试目录 0 引用 → `test_settings.py` 的覆盖是死赋值

## 2. 修改

- [x] 2.1 `.env.example` 补 5 个开关；验证：`:41-43` 引擎插槽段（DEVICE_ENGINE / AI_ENGINE，含默认值与 registry 真相源）· `:56-57` REDIS_URL · `:96-97` ADMIN_USERS · `:99-100` UPLOAD_CLEANUP_MAX_AGE_DAYS
- [x] 2.2 `run.py` 三处空 except；验证：`:104` 与 `:198` 各补一句说明忽略原因的注释；`:204-206` 外层兜底改为 `except Exception as exc` + `print(f"  MySQL cleanup skipped: {exc}")`
- [x] 2.3 `ARCH-00` §七 运维例外；验证：在「一键启动/停止/状态」块内新增 3 行，写明该 DB 直连属 best-effort 运维动作、不承载业务读写
- [x] 2.4 `config/test_settings.py` 删死赋值；验证：`git diff` = `0 1`（仅 −1 行），保留紧随的 `DATABASES` 覆盖
- [x] 2.5 本地 `.env` 清理；验证：43 → 41 行，`AGENTSCOPE_PORT` / `SCREENSHOT_INTERVAL` 残留命中 0（该文件 gitignored，不入库）

## 3. 验证

- [x] 3.1 `python manage.py check` → no issues，exit 0；`python manage.py makemigrations --check --dry-run` → `No changes detected`，exit 0（G1 修复保持）
- [x] 3.2 `python -m ruff check config run.py run_daphne.py manage.py` → All checks passed，exit 0；`ruff format --check` → 10 files already formatted，exit 0
- [x] 3.3 D0 单测回归：`test_api_docs_consistency` + `test_logging_config` + `test_env_loader` → **14 passed**，exit 0
- [x] 3.4 冒烟：`python run.py status` → exit 0，正常打印 Redis / Django backend / Vue frontend 三行状态（脚本可导入、可运行）

## 4. 有意未做（Non-Goals，已在 design 登记）

- [x] 4.1 `CORS_ALLOW_CREDENTIALS = True` 保持（既有登记；生产侧由 `CORS_ALLOW_ALL_ORIGINS=False` 兜住）
- [x] 4.2 `check --deploy` 5 条告警保持（W004/W008/W012/W016/W018 全为本地 DEBUG 预期；生产默认已 fail-closed）
- [x] 4.3 不搬迁 `cleanup_mysql_connections()`（依赖 `run.py` 已解析的 `BASE_ENV` 与子进程上下文，搬迁会引入新耦合）
- [x] 4.4 `DJANGO_ASGI_SERVER` 不写入 `.env.example`（`run.py` 自行注入的内部约定，写进示例会诱导手工设置）
