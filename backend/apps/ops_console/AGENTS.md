# ops_console — 模块约束

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件（本文件只写增量）。

运营后台（用户管理）的**管理面**：账号列表、停用、启用、重置密码、本页批量停用、仅超管批量注销。
没有自有数据表：账号数据全部经 `backend.apps.accounts` 的 `api.py` 读写。

规格真相源：`openspec/changes/add-ops-user-console`（归档后为 `openspec/specs/ops-user-console/`）。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/ops/users/` | 运营可读（分页 / 关键字 / 状态筛选） |
| POST | `/api/ops/users/<id>/disable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/enable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/reset-password/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/grant-operator/` | 仅超级管理员，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/revoke-operator/` | 仅超级管理员，且目标必须是运营或普通用户 |
| POST | `/api/ops/users/disable/` | 运营，本页批量停用；不可管理的行逐行拒绝，不拖垮整批 |
| POST | `/api/ops/users/purge/` | 仅超级管理员，批量注销；只删账号，不删业务表 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case。
- 运营判定用 `shared.users.is_operator`（超级管理员天然算运营），禁止在本 App 另写组判定。

## 红线

| 只做 | 禁止 |
|------|------|
| 经 `accounts.api` 的 `set_user_active` / `set_user_password` / `set_operator` / `purge_users` 写库 | 在本 App 直接 `user.save()`、`user.delete()` 或 `groups.add` 改账号 |
| 读 `auth.User` Model 做列表与身份展示 | import `accounts` 的 views / serializers / jwt_auth 内部实现 |
| 本页批量停用；批量注销仅超管，且只删账号行 | 跨页全选、按 `created_by` 清扫业务表、批量授权、第二档角色，或让运营互相授权 / 互相注销 |

## 边界口径

- **不能动自己**：任何账号都不能停用/重置自己，避免自锁。
- **不能停用或注销超级管理员**：谁来操作都 403，包括另一名超管。
- **不能停用或注销运营**：谁来操作都 403，包括超级管理员。运营仍可被超管授予或取消运营身份。
- **注销只删账号**：仅超管、仅 `POST /api/ops/users/purge/`。不删项目、任务、缺陷、设备锁。其它删除路径仍不注册，自然 404，不要补 405 兜底路由。
- **密码只在响应里出现一次**：日志与数据库都不得落明文，日志只记操作人与目标。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check（本 App 不该产生迁移）
[ ] python -m pytest -c tests/pytest.ini tests/ops_console -q
[ ] python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn
```
