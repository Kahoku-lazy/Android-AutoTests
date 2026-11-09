## Why

`python run.py start` 只拉起 backend + frontend（Redis 退役后只剩这两件），数据库被当成外部前提：README 让用户先装库、先 `migrate`，`run.py` 既不检测也不启动。本机恰好 MySQL 服务是 Automatic，所以平时无感；换机器或服务停掉时，`start` 会「成功」拉起后端，但所有接口 500，排查成本高。

## What Changes

- `run.py start` 增加数据库前置检查：连不上时，若 `DB_HOST` 是本机则尝试启动本机 MySQL 服务，再复检；仍不可用（含权限不足）**中止启动**并打印对应系统的提权命令。
- 远程数据库（`DB_HOST` 非本机）只检测连通性并报错，**不**尝试启动。
- `run.py status` 增加数据库行（`ONLINE/OFFLINE` + 地址）。
- 开关：`DB_AUTOSTART=0` 关闭自动启动，`--no-db` 跳过检查（CI / 容器 / 库由外部管理时用）；服务名可用 `DB_SERVICE_NAME` 覆盖（Windows 默认 `MySQL`，Linux/macOS 默认 `mysql`）。
- `.env.example` 与 README 增补这两个变量与说明。

## Impact

- 只影响本机运维脚本，不改后端代码、接口与数据库结构。
- `python run.py stop` 行为不变：仍只清理空闲连接，**不**停数据库。
- 迁移不在本变更范围：检测到未应用迁移时只提示（见 README），不自动 `migrate`。
