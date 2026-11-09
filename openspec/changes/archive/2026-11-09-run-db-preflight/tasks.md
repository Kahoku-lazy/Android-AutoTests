## 1. 数据库探测

- [x] 1.1 `run.py` 增加 `_db_config()`（读取 `DB_ENGINE/DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME/DB_SERVICE_NAME`）与 `_db_reachable(cfg)`（`MySQLdb` 真连，3 秒超时；sqlite 跳过）。验证：`test_run_db_preflight.py` 覆盖成功/失败/sqlite 三路。
- [x] 1.2 增加 `_is_loopback(host)` 与 `_db_status_line()`（ONLINE/OFFLINE/SQLite）。验证：单测覆盖三种输出与四种主机名。

## 2. 启动前置检查

- [x] 2.1 `_ensure_db(cfg, allow_autostart)`：可达直接通过；本机不可达且允许启动时调用 `_start_local_db_service()` 并复检；失败打印原因 + 提权命令并返回 False；远程不可达只报错。验证：单测覆盖可达/远程/本机启动成功/权限失败。
- [x] 2.2 `_start_local_db_service()`：Windows `sc.exe start`、Linux `systemctl start`、macOS `brew services start`；返回 (ok, 输出)。验证：单测断言命令首项。
- [x] 2.3 `cmd_start` 在 backend 前调用 `_ensure_db`，失败则终止且不调用任何 `_START`。验证：单测断言 `_START` 未被调用。
- [x] 2.4 开关：`--no-db`（跳过检查）与 `DB_AUTOSTART=0`（只关自动启动）、`DB_CHECK=0` 接入。验证：单测两路 + `--help` 可见。

## 3. 状态与文档

- [x] 3.1 `cmd_status` 增加数据库行。验证：`python run.py status` 显示 `Database : 127.0.0.1:3306 ONLINE`。
- [x] 3.2 `.env.example` 增补 `DB_SERVICE_NAME` / `DB_AUTOSTART`；README 覆盖「自动检测 + 本机尝试启动 + 远程只检测 + `--no-db`」。验证：文档已更新。
- [x] 3.3 `run.py` usage 与 argparse help 增加 `--no-db`。

## 4. 测试与收口

- [x] 4.1 新增 `tests/graybox/unit/test_run_db_preflight.py`（16 条）：探测、状态行、本机启动命令、远程不启动、权限失败、`--no-db`、`cmd_start` 中止。
- [x] 4.2 门禁：`python run.py check` → **阻塞项 23/23 通过**（0 失败；告警项为既有 engines docstring）。
- [x] 4.3 人工验收（本机）：`python run.py start backend` → 先打印 `Database : 127.0.0.1:3306 ONLINE`，再重建 backend 并 ready；`python run.py status` 输出 Database/ADB 行；`--no-db` 与关闭自动启动由单测覆盖。顺带修掉 `cleanup_mysql_connections()` 漏传 `DB_PASSWORD` 的既有缺陷（此前每次 stop 都打印 `Access denied ... (using password: NO)`）。「停服务后提权提示」需要管理员权限才能制造该状态，留作用户手工验收。
