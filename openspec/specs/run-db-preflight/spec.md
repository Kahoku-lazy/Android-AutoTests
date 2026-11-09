# run-db-preflight Specification

## Purpose
TBD - created by archiving change run-db-preflight. Update Purpose after archive.

## Requirements

### Requirement: 启动前检查数据库连通性

`python run.py start` SHALL 在拉起后端前检查数据库：`DB_ENGINE=mysql` 时用真实连接（网络 + 账号 + 库名）验证；`DB_ENGINE=sqlite` 时跳过。不可达时 MUST NOT 拉起 backend/frontend，并 SHALL 输出可操作的失败原因。`--no-db` 或 `DB_CHECK=0` SHALL 跳过该检查。

#### Scenario: 数据库可用时正常启动

- **WHEN** 本机 MySQL 已运行且 `.env` 的账号可连
- **THEN** `python run.py start` 打印数据库 ONLINE
- **AND** backend / frontend 按原顺序启动

#### Scenario: 数据库不可达时中止启动

- **WHEN** `DB_ENGINE=mysql` 且数据库连接失败，本机服务也无法启动
- **THEN** `python run.py start` 打印失败原因与修复命令
- **AND** backend / frontend 不被拉起

#### Scenario: 显式跳过检查

- **WHEN** 使用 `--no-db` 启动，且数据库不可达
- **THEN** 跳过数据库检查
- **AND** backend / frontend 仍按原逻辑启动

### Requirement: 本机数据库服务尽力启动

当 `DB_HOST` 为本机（`127.0.0.1` / `localhost` / `::1`）且连接失败时，`run.py start` SHALL 尝试启动本机数据库服务（Windows `sc start`、Linux `systemctl start`、macOS `brew services start`），并在启动后复检。服务名 SHALL 可由 `DB_SERVICE_NAME` 覆盖。远程数据库 MUST NOT 尝试启动。

权限不足或启动失败时 SHALL 打印对应平台的提权命令（如 `net start MySQL` 以管理员运行、`sudo systemctl start mysql`）并中止启动。

`DB_AUTOSTART=0` SHALL 关闭「尝试启动」，但检测仍执行。

#### Scenario: 本机服务未运行且可被当前用户启动

- **WHEN** 本机 MySQL 服务已停止，`DB_AUTOSTART` 未关闭，当前用户有启动权限
- **THEN** `run.py start` 先启动服务并复检通过
- **AND** 随后正常启动 backend / frontend

#### Scenario: 权限不足时给出提权命令

- **WHEN** 本机 MySQL 服务已停止且当前用户无启动权限
- **THEN** 输出启动失败的原始原因
- **AND** 输出当前平台的提权启动命令并中止

#### Scenario: 远程数据库不尝试启动

- **WHEN** `DB_HOST` 不是本机地址且连接失败
- **THEN** 不执行任何服务启动命令
- **AND** 报出 `host:port` 不可达并中止

### Requirement: 状态命令包含数据库

`python run.py status` SHALL 输出数据库状态行：MySQL 显示 `host:port` 与 `ONLINE` / `OFFLINE`；SQLite 显示 `DB_ENGINE=sqlite`。状态命令 MUST NOT 因数据库不可达而异常退出。

#### Scenario: 数据库在线

- **WHEN** 数据库可连接，执行 `python run.py status`
- **THEN** 输出包含数据库地址与 `ONLINE`

#### Scenario: 数据库离线

- **WHEN** 数据库不可连接，执行 `python run.py status`
- **THEN** 输出包含 `OFFLINE`
- **AND** 命令仍以成功退出码结束
