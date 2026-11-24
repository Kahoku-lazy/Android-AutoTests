# ops_console · 用户管理控制台

> 归属模块：`backend/apps/ops_console` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/ops_console/urls.py`、`api.py`、`views.py`
> 规格真相源：`openspec/specs/ops-user-console/`（原变更 `add-ops-user-console`）
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

运营后台（用户管理）的**管理面**：账号列表、停用、启用、重置密码、模型名单、助手作者授权、
本页批量停用、仅超管批量注销。
**没有自有数据表**：账号数据全部经 `backend.apps.accounts` 的 `api.py` 读写。

## 接口

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/ops/users/` | 运营可读（分页 / 关键字 / 状态筛选） |
| POST | `/api/ops/users/<id>/disable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/enable/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/reset-password/` | 运营，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/model-grants/` | 仅超级管理员（改模型名单，body `model_config_id` + `enabled`） |
| POST | `/api/ops/users/<id>/grant-author/` | 仅超级管理员，授予助手作者 |
| POST | `/api/ops/users/<id>/revoke-author/` | 仅超级管理员，收回助手作者 |
| POST | `/api/ops/users/<id>/grant-operator/` | 仅超级管理员，且目标必须是普通用户 |
| POST | `/api/ops/users/<id>/revoke-operator/` | 仅超级管理员，且目标必须是运营或普通用户 |
| POST | `/api/ops/users/disable/` | 运营，本页批量停用；不可管理的行逐行拒绝，不拖垮整批 |
| POST | `/api/ops/users/purge/` | 仅超级管理员，批量注销；只删账号，不删业务表 |

- 路径必须带尾斜杠；响应遵循 `{status, data}` 与 snake_case。
- 运营判定用 `shared.users.is_operator`（超级管理员天然算运营），**禁止在本 App 另写组判定**。

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
- **注销只删账号**：仅超管、仅 `POST /api/ops/users/purge/`。不删项目、任务、缺陷、设备锁。
  其它删除路径仍不注册，自然 404，不要补 405 兜底路由。
- **密码只在响应里出现一次**：日志与数据库都不得落明文，日志只记操作人与目标。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check（本 App 不该产生迁移）
[ ] python -m pytest -c tests/pytest.ini tests/ops_console -q
[ ] python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn
```

全局关单清单见 `backend/AGENTS.md` §3。
