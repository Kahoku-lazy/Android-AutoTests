# serial-log App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `apps/AGENTS.md` 优先于本文件（本文件只写增量）。

## 职责

- 无线串口日志的**管理面**：端口来源登记（`sources.py`）、监听开关持久化（`models.LogPort → sl_log_ports`）、启停编排（`port_service.py`）、当前日志文件只读、关键词对照表组装（`keywords.py`）、启动恢复（`apps.py`）。
- 采集与写文件仍在引擎层：`engines/uart_log`、`engines/device/logbus`、`engines/device/logfiles`、`utils/logs`；本 App **不**碰 socket 与文件句柄。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/serial-log/ports/` | 登录可读 |
| POST | `/api/serial-log/ports/toggle/` | 仅超级管理员 |
| GET | `/api/serial-log/ports/<int:port>/lines/` | 登录可读 |
| GET | `/api/serial-log/keywords/` | 登录可读 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case；超管判定用 `shared.users.is_superuser`。
- 旧路径 `/api/ai/log-ports/…`、`/api/ai/log-keywords/` **不再提供**，也不保留重定向别名。

## 写库与边界

- `sl_log_ports` 的**唯一写点**是 `apps/serial_log/api.py`；View / `apps.py` 只能经 `port_service` → `api.py` 落库。
- 本 App **禁止 import `apps.ai_assistant`**（也不被对方 import）；跨模块读取开关状态时走 `api.py`。
- 端口 / SKU / 波特率三列的真相源是 `DEVICE_LOG_*` 配置；表里只存开关，配置变更不得改写开关值。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check
[ ] python -m pytest tests/api/test_serial_log_api.py -q
[ ] python manage.py spectacular --validate
[ ] 临时 SQLite 演练：全新安装 + 旧表升级（开关状态保留、旧表删除）
```
