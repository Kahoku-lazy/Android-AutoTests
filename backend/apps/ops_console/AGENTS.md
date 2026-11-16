# ops_console — 模块约束

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件（本文件只写增量）。

运营后台（用户管理）的**管理面**：账号列表、停用、启用、重置密码。
没有自有数据表：账号数据全部经 `backend.apps.accounts` 的 `api.py` 读写。

规格真相源：`openspec/changes/add-ops-user-console`（归档后为 `openspec/specs/ops-user-console/`）。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/ops/users/` | 运营可读（分页 / 关键字 / 状态筛选） |
| POST | `/api/ops/users/<id>/disable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/enable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/reset-password/` | 运营，且目标必须是普通用户 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case。
- 运营判定用 `shared.users.is_operator`（超级管理员天然算运营），禁止在本 App 另写组判定。

## 红线

| 只做 | 禁止 |
|------|------|
| 经 `accounts.api` 的 `set_user_active` / `set_user_password` 写库 | 在本 App 直接 `user.save()` 改账号字段 |
| 读 `auth.User` Model 做列表与身份展示 | import `accounts` 的 views / serializers / jwt_auth 内部实现 |
| 四个端点的运营边界校验 | 新增删除账号、批量操作、授予运营的端点（需另开变更） |

## 边界口径

- **不能动自己**：任何账号都不能停用/重置自己，避免自锁。
- **不能动超级管理员**：运营对超管一律 403（超管之间互不干预属非目标）。
- **不能动其他运营**：除超级管理员外，运营只能管理普通用户。
- **不提供删除**：删除请求自然 404，不要补 405 兜底路由。
- **密码只在响应里出现一次**：日志与数据库都不得落明文，日志只记操作人与目标。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check（本 App 不该产生迁移）
[ ] python -m pytest -c tests/pytest.ini tests/ops_console -q
[ ] python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn
```
