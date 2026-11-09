## Context

`run.py` 是唯一的一键启停入口，但它对数据库零感知。要补的是「启动前置检查 + 本机服务尽力拉起 + 失败可操作」，不是把数据库变成 `run.py` 管理的第三件套（远程库、容器库、共享库都不该由它停/启）。

## Decisions

### D1 用真实连接检测，不用端口探活

`127.0.0.1:3306` 通不代表能登录、库存在、账号有权限。检测直接 `MySQLdb.connect(host, port, user, passwd, db, connect_timeout=3)`：一次同时验证网络、账号、库名。`DB_ENGINE=sqlite` 时跳过检查（文件库无服务）。

### D2 自动启动只对本机数据库生效

`DB_HOST` 属于 `127.0.0.1` / `localhost` / `::1` 时才算「本机」；远程库只报告不可达并中止，**不**尝试启动（既没有权限，也不该替别人管库）。

### D3 本机启动方式按平台走命令行，不弹 UAC

| 平台 | 查询 | 启动 |
|---|---|---|
| Windows | `sc.exe query <service>` | `sc.exe start <service>` |
| Linux | `systemctl is-active <service>` | `systemctl start <service>` |
| macOS | `brew services list` | `brew services start <service>` |

普通权限下 `sc start` / `systemctl start` 会失败——这是预期分支：把原始输出回显，并打印提权命令（`net start MySQL` 以管理员 / `sudo systemctl start mysql`），然后中止启动。脚本不弹 UAC（静默、可 CI）。

### D4 失败即中止，不启动注定 500 的后端

数据库不可达时 `cmd_start` 直接返回、不拉起 backend/frontend。`python run.py start backend` 同样生效。`--no-db` 完全跳过检查（CI / 容器 / 远程库由外部保证时用）；`DB_AUTOSTART=0` 只关闭「尝试启动」，检测仍执行且不可达时仍中止。

### D5 `status` 增加数据库行

`MySQL (127.0.0.1:3306) ONLINE` / `OFFLINE`；sqlite 显示 `SQLite (DB_ENGINE=sqlite)`。检测失败不抛异常，状态命令永远可跑。

### D6 不做的事

- 不自动 `migrate`（检测到缺失只在 README 提示）。
- 不停数据库（`stop` 只清理空闲连接，保持现状）。
- 不管理远程库 / 容器编排。
- 不把数据库加入 `SERVICE_ORDER`（它不是 `run.py` 启停的进程）。

## Risks

| 风险 | 缓解 |
|---|---|
| 本机无管理员权限，自动启动失败被误判为脚本缺陷 | 明确打印提权命令并中止；文档写清「首次需手动/管理员启动服务」 |
| 检测增加启动耗时（3 秒超时） | 只在 `start` 前执行一次；`--no-db` 可跳过 |
| 远程库短暂抖动导致 `start` 中止 | 行为可预期（失败即中止）；`--no-db` 或先确认库恢复 |
| 服务名与安装方式不一致（MariaDB / 自定义实例） | `DB_SERVICE_NAME` 覆盖，默认 Windows `MySQL`、Unix `mysql` |

## Migration Steps

1. `run.py` 增加 DB 配置读取、连通性检测、本机服务查询/启动、`_ensure_db`、`status` 行与 `--no-db`。
2. `.env.example` 与 README 增补 `DB_SERVICE_NAME` / `DB_AUTOSTART` 与说明。
3. 单测：可达/远程不可达/本机自动启动成功/权限失败中止/`--no-db` 跳过/`status` 行。
4. 门禁与人工验收（停掉 MySQL 服务试一次 start）。
