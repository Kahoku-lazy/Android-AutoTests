# dashboard App CLAUDE.md

> 全局边界 / 协议要点 / 关单清单 → `../CLAUDE.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 dashboard 行的展开）

| 只做 | 禁止 |
|------|------|
| 聚合各 App 数据的只读统计（stats/activities） | **任何写操作**（全平台唯一只读区，前端同理） |
| 跨 App 只读 ORM 查询（防火墙 #2 读放开） | import 其他 App 的 service/内部实现 |

- 聚合口径依赖各 App Model 字段；字段改名时本 App 的统计 SQL/查询必须同改，否则静默返回错误口径。

## 本 App 契约（特例 + 真相源）

真相源：`apps/dashboard/urls.py`（4 端点挂在 `/api/` 下：`dashboard/stats/` / `dashboard/activities/` / `devices/stats/` / `cases/stats/`）+ `views.py`。

- **路由前缀特例**：本 App 是唯一挂载在 `/api/` 根下而非 `/api/{app}/` 的 App（`config/urls.py` 第 18 行），新增端点时注意路径命名不与其它 App 冲突。
- 信封走全局标准 `{status, data}`。
- 无 models（纯聚合），无 `api.py`——无写路径，也就不存在跨 App 写问题。

## 本 App 协议要点

无 WS / SSE。数据经 HTTP 拉取，仪表盘不订阅实时通道。

## 关单附加项（全局清单的 delta）

```
[ ] 无任何 INSERT/UPDATE/DELETE（grep 本 App 无 .create(/.save(/.delete(）
[ ] 聚合口径与来源 App Model 字段逐一核对（字段改名时）
[ ] 只读跨 App 访问仅 Model import，无 service import
```
