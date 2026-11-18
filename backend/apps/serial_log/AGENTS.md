# serial-log App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件（本文件只写增量）。

## 职责

- 无线串口日志的**管理面**：端口来源登记（`sources.py`，配置 + 自定义双轨合并）、监听开关持久化（`models.LogPort → sl_log_ports`）、自定义端口增删改（仅超管）、启停编排（`port_service.py`，单端口增量生效）、当前日志文件只读、关键词对照表组装（`keywords.py`）、启动恢复（`apps.py`）。
- 采集与写文件仍在引擎层：`engines/uart_log`、`engines/device/logbus`、`engines/device/logfiles`、`utils/logs`；本 App **不**碰 socket 与文件句柄。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/serial-log/ports/` | 登录可读 |
| POST | `/api/serial-log/ports/` | 仅超级管理员（新增自定义端口） |
| POST | `/api/serial-log/ports/toggle/` | 仅超级管理员 |
| PATCH | `/api/serial-log/ports/<int:port>/` | 仅超级管理员（仅自定义端口） |
| DELETE | `/api/serial-log/ports/<int:port>/` | 仅超级管理员（仅自定义端口） |
| GET | `/api/serial-log/ports/<int:port>/lines/` | 登录可读 |
| GET | `/api/serial-log/keywords/` | 登录可读 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case；超管判定用 `shared.users.is_superuser`。
- 旧路径 `/api/ai/log-ports/…`、`/api/ai/log-keywords/` **不再提供**，也不保留重定向别名。

## 写库与边界

- `sl_log_ports` 的**唯一写点**是 `backend/apps/serial_log/api.py`；View / `apps.py` 只能经 `port_service` → `api.py` 落库。
- 本 App **禁止 import `apps.ai_assistant`**（也不被对方 import）；跨模块读取开关状态时走 `api.py`。
- 端口登记实行**双轨制**（2026-11-18 变更申请获批，见 `openspec/changes/archive` 的 add-serial-log-custom-ports）：**配置行**（`origin=config`）的端口 / SKU / 波特率三列真相源是 `DEVICE_LOG_*` 配置，配置同步只刷新配置行、不得改写开关值；**自定义行**（`origin=custom`）的三列真相源是 `sl_log_ports` 本身，配置同步不得创建、改写或删除自定义行。
- 新增 / 编辑 / 删除端口一律**单端口增量生效**（`PortSwitch.open/close` 幂等），禁止以全局 reset 方式生效；删除自定义端口只删登记，历史日志文件保留。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/serial_log/api/test_serial_log_api.py -q
[ ] python manage.py spectacular --validate
[ ] 临时 SQLite 演练：全新安装 + 旧表升级（开关状态保留、旧表删除）
```
