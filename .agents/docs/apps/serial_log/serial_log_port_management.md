# serial_log · 端口登记与启停

> 归属模块：`backend/apps/serial_log` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/serial_log/urls.py`、`api.py`、`sources.py`、`port_service.py`、`models.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

无线串口日志的**管理面**：端口来源登记（`sources.py`，配置 + 自定义双轨合并）、
监听开关持久化（`models.LogPort → sl_log_ports`）、自定义端口增删改（仅超管）、
启停编排（`port_service.py`，单端口增量生效）、当前日志文件只读、启动恢复（`apps.py`）。

采集与写文件仍在引擎层：`engines/uart_log`、`engines/device/logbus`、`engines/device/logfiles`、`utils/logs`；
本 App **不**碰 socket 与文件句柄。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/serial-log/ports/` | 登录可读 |
| POST | `/api/serial-log/ports/` | 仅超级管理员（新增自定义端口） |
| POST | `/api/serial-log/ports/toggle/` | 仅超级管理员 |
| PATCH | `/api/serial-log/ports/<int:port>/` | 仅超级管理员（仅自定义端口） |
| DELETE | `/api/serial-log/ports/<int:port>/` | 仅超级管理员（仅自定义端口） |
| GET | `/api/serial-log/ports/<int:port>/lines/` | 登录可读 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case；超管判定用 `shared.users.is_superuser`。
- 旧路径 `/api/ai/log-ports/…` **不再提供**，也不保留重定向别名。

## 端口登记双轨制

（2026-11-18 变更申请获批，见 `openspec/changes/archive` 的 `add-serial-log-custom-ports`）

- **配置行**（`origin=config`）：端口 / SKU / 波特率三列真相源是 `DEVICE_LOG_*` 配置；
  配置同步只刷新配置行、**不得改写开关值**。
- **自定义行**（`origin=custom`）：三列真相源是 `sl_log_ports` 本身；
  配置同步**不得创建、改写或删除**自定义行。

## 写库与边界

- `sl_log_ports` 的**唯一写点**是 `backend/apps/serial_log/api.py`；
  View / `apps.py` 只能经 `port_service` → `api.py` 落库。
- 本 App **禁止 import `apps.ai_assistant`**（也不被对方 import）；跨模块读取开关状态时走 `api.py`。
- 新增 / 编辑 / 删除端口一律**单端口增量生效**（`PortSwitch.open/close` 幂等），
  禁止以全局 reset 方式生效；删除自定义端口只删登记，历史日志文件保留。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/serial_log/api/test_serial_log_api.py -q
[ ] python manage.py spectacular --validate
[ ] 临时 SQLite 演练：全新安装 + 旧表升级（开关状态保留、旧表删除）
```

关键词对照表见 [serial_log_keyword_table.md](serial_log_keyword_table.md)。
