# serial_log · 关键词对照表

> 归属模块：`backend/apps/serial_log` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/serial_log/keywords.py`、`api.py`、`models.LogKeyword`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 真相源

关键词对照表的真相源是 **`sl_log_keywords` 表**，不是 JSON 文件。

（2026-11-18 变更 `serial-log-keyword-db-scope`：存量 JSON 经 `0005_keyword_snapshot` 冻结快照迁库，
`device_log_keywords.json` 退役为**种子档案**。）

- 一行 = 关键词 × 功能点 × 范围。
- `scope="*"` 为通用，其余为 SKU 名；某型号可用词为通用与专用的**并集**。
- 平台展示与取词 **MUST NOT** 再读该 JSON 文件。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/serial-log/keywords/` | 登录可读 |
| POST | `/api/serial-log/keywords/` | 仅超级管理员（新建关键词） |
| PATCH | `/api/serial-log/keywords/<int:row_id>/` | 仅超级管理员（部分更新） |
| DELETE | `/api/serial-log/keywords/<int:row_id>/` | 仅超级管理员（删除条目） |

- 旧路径 `/api/ai/log-keywords/` **不再提供**，也不保留重定向别名。
- 超管判定用 `shared.users.is_superuser`。

## 写库

`sl_log_keywords` 的**唯一写点**是 `backend/apps/serial_log/api.py`；
关键词写入（一期为迁移导入与维护函数）同样只经 `api.py`，View 不得直写 ORM。

## 边界

本 App **禁止 import `apps.ai_assistant`**（也不被对方 import）；按型号取关键词时走 `api.py`。

端口登记与启停见 [serial_log_port_management.md](serial_log_port_management.md)。
