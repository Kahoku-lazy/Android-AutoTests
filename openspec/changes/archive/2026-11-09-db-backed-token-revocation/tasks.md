## 1. 存储层（`apps/accounts`）

- [x] 1.1 新增 `backend/apps/accounts/models.py`：`TokenRevocation`（`kind` / `ref` / `expires_at` / `created_at`，表名 `acc_token_revocations`，唯一约束 `(kind, ref)`，`expires_at` 建索引）。验证：`makemigrations accounts` 产出 `0001_initial`；`makemigrations --check --dry-run` → `No changes detected`。
- [x] 1.2 在 `apps/accounts/api.py` 增加写口与读口：`revoke_session(sid, ttl_seconds)` / `revoke_token(jti, ttl_seconds)` / `is_revoked(sid, jti)` / `purge_expired(limit)`，写口用 `update_or_create` 保持幂等并顺手清理过期行。验证：用例覆盖重复吊销、过期清理。
- [x] 1.3 `api.py` 的 `__all__` 同步导出新函数。验证：`from backend.apps.accounts import api; api.is_revoked` 可用。

## 2. 校验层（`shared/auth/jwt_auth.py`）

- [x] 2.1 删除 `_get_redis()`、`_redis_client`、`_BLACKLIST_PREFIX`、`_SESSION_PREFIX`；`_is_revoked(jti, sid)` 改为查表（惰性 import `apps.accounts.api`，避免循环导入）。验证：全仓 `_get_redis` / `jwt:session_revoked:` 0 命中。
- [x] 2.2 `_revocation_add(kind, ref, ttl_seconds)` 保留为内部缝；写失败（`DatabaseError`）统一抛 `BlacklistUnavailableError`。验证：monkeypatch 写口抛 `OperationalError` → 抛该错误。
- [x] 2.3 读失败（`DatabaseError`）记 `error` 日志并放行，保持 D4 的 fail-open 取舍。验证：用例断言不抛错。
- [x] 2.4 更新 `BlacklistUnavailableError` 的 docstring 与日志文案：Redis → 吊销存储。验证：`backend/` 内只剩 channel layer 的 Redis 引用。

## 3. 登出端点（`apps/accounts/views.py`）

- [x] 3.1 503 响应体改为存储无关文案（`{"message": "吊销服务不可用，请稍后重试", "retry": true}`，经信封渲染），状态码不变。验证：用例断言 503 + `retry` + 文案。
- [x] 3.2 登出路径仍先按 `sid` 吊销、再按 `jti` 兜底；旧令牌（无 `sid`）行为不变。验证：既有场景用例全绿。

## 4. 去重复验（`shared/auth/drf_auth.py`）

- [x] 4.1 认证类优先复用 `request.user_id`（网关中间件已注入），缺失时才调用 `verify_token`；仍按 `sub` 查 `User` 并保留「用户已删除 → 401」。验证：`test_auth_single_verify.py` 断言 `verify_token` 只被调用 1 次。
- [x] 4.2 保留独立可用性：直接构造不带 `user_id` 的请求（模拟绕过中间件）仍能完成鉴权。验证：同文件回退路径用例绿。

## 5. 测试

- [x] 5.1 改写 `tests/graybox/unit/test_logout_session_revocation.py`：去掉真实 Redis 依赖，夹具改为数据库；保留原有 7 个场景。验证：15 条用例（含新增）全绿。
- [x] 5.2 新增用例：过期记录不再生效（`expires_at` 置为过去后令牌恢复可用）。验证：断言 `verify_token` 通过。
- [x] 5.3 新增用例：写失败返回 503 + `retry` 且会话仍可用（替换原「Redis 不可用」用例）。验证：monkeypatch `api.revoke_session` 抛 `OperationalError`。
- [x] 5.4 新增用例：一次受保护请求只解析一次令牌（计数 `verify_token` 调用 = 1）。验证：`test_auth_single_verify.py` 全绿。
- [x] 5.5 新增用例：过期行会被清理（`purge_expired()` 返回删除条数，未过期行不受影响）。验证：断言条数。
- [x] 5.6 顺带修掉一条**既有**红测：`test_csrf_protection.py::test_jwt_request_is_not_csrf_blocked` 用假 `sub` 打 `/api/reports/`，前者会被「用户不存在」拦、后者已只允许 GET。改为真实用户 + `/api/auth/logout/`（HEAD 上同样失败，非本变更引入）。验证：该文件 6 条全绿。

## 6. 文档与收口

- [x] 6.1 `backend/apps/accounts/AGENTS.md`：删掉「没有自有表」的表述与「Redis 不可用」措辞，改为吊销表 + 存储不可用；错误码表 logout 行同步。
- [x] 6.2 文档同步：`README.md`（表前缀、依赖说明）、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`dev_docs/ARCH_PRD/PRD-平台总需求.md`。验证：`jwt:blacklist:` / `jwt:session_revoked:` 全仓 0 命中。
- [x] 6.3 门禁：`python run.py check` → **阻塞项 23/23 通过**（`openapi-schema` 与 `pytest-collect` 均 PASS；本次运行时前端 `vitest` 也已转绿，此前基线 22/23 的登录页失败已不复现）。
- [x] 6.4 人工验收（开发服务器 `:8766` 实测）：登录 → `/api/auth/me/` 200 → 登出 200 → 同一 access 再请求 `/api/auth/me/` **401**；同一会话 refresh 登出后 **401**；库内落了两行（`session` 到期 +7d、`token` 到期 +1h）。「重启后仍 401」由「记录落库 + 无进程内缓存」保证，并由 `test_revocation_row_is_persisted` 锁定；未主动重启开发后端（避免打断正在运行的任务）。
