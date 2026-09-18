## 1. 变更与规格

- [x] 1.1 `openspec/changes/revoke-session-on-logout/` 四件套
- [x] 1.2 新能力规格 `specs/auth-session/spec.md`（6 个 Scenario）
- [x] 1.3 `openspec validate revoke-session-on-logout` 通过 —— `Change 'revoke-session-on-logout' is valid`

## 2. 令牌层（shared/auth/jwt_auth.py）

- [x] 2.1 新增 `_SESSION_PREFIX = "jwt:session_revoked:"`
- [x] 2.2 `create_access_token(user_id, extra=None, sid=None)` / `create_refresh_token(user_id, sid=None)`：`sid` 可选写入（签名向后兼容，8 个测试文件仍在调旧签名）
- [x] 2.3 `create_token_pair(user_id)`：生成一个 `sid` 并写入两个令牌；**返回键集不变**
- [x] 2.4 `verify_token()`：`jti` 与 `sid` 两级吊销检查，用一次 `EXISTS key1 key2`
- [x] 2.5 新增 `revoke_session(sid, ttl_seconds=None)`（默认 TTL = `JWT_REFRESH_TTL`）；新增 `session_id_of(token)`
- [x] 2.6 把 `_blacklist_add` 重构为通用 `_revocation_add(key, ttl)`，并把 `setex` 改为 `set(..., ex=)`
- [x] 2.7 保留 `blacklist_token()`（旧令牌兜底） —— 部署前签发的 access 无 sid，只能按 jti 撤

## 3. 视图层（apps/accounts/views.py）

- [x] 3.1 `LogoutView`：优先按 `sid` 吊销整个会话，再按 `jti` 兜底；Redis 不可用仍 503 + `retry`
- [x] 3.2 `RefreshView`：换发新 access 时**透传 `sid`**（否则续期后脱管）
- [x] 3.3 更新两个 View 的 docstring，使其与真实语义一致 —— docstring 由「把当前 access 令牌写入黑名单」改为「吊销本次登录的整个会话」

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_logout_session_revocation.py`
- [x] 4.2 逐条覆盖规格的 6 个 Scenario：refresh 失效 / access 失效 / 续期保持归属 / 其他会话不受影响 / Redis 不可用 503 / 无 sid 旧令牌不报错
- [x] 4.3 跑 `pytest tests/graybox/unit/test_logout_session_revocation.py tests/graybox/unit/test_jwt_hardening.py tests/graybox/unit/test_csrf_protection.py -q` 全绿 —— 18 passed（新增 9 + jwt_hardening 3 + csrf 6）

## 5. 证据产物与文档

- [x] 5.1 重跑 `temps/login-backend-map`：F 节结论由「断点」变为「已闭合」，采集器改引 `_is_revoked`
- [x] 5.2 自检器断言随实测值变化（登出后 refresh 由 200 变 401）；`--check` exit 0 —— 登出后 refresh 由 200 变 401；`--check` exit 0，verify errs []
- [x] 5.3 `apps/accounts/AGENTS.md`：登记登出契约（会话级吊销 + 续期透传 `sid`），结束该文件 0 字节状态 —— 该文件此前 0 字节；现含会话契约、路径约定与错误码表
- [x] 5.4 端到端复验：用 `temps/probe_logout_refresh.py` 确认 \[4\] 由 200 变 401 —— `[4] REFRESH after logout -> 401`（原 200）

## 6. 门禁

- [x] 6.1 `python manage.py check` —— `System check identified no issues`
- [x] 6.2 `ruff check` + `ruff format --check`（改动的路径） —— `All checks passed` + `3 files already formatted`（修掉 I001 与未用 import）
- [x] 6.3 `python tools/gen_arch_stats.py --check-boundaries` —— `✅ 模块边界检查通过 — 零违规`
- [x] 6.4 归档变更并把 delta 同步进 `openspec/specs/auth-session/spec.md`
## 7. 实施期补记

- [x] 7.1 采集器原引用 `jwt_auth._blacklist_contains` 已随重构改名，同步改为 `_is_revoked`，并补 `revoke_session` / `session_id_of` 两个图例项
- [x] 7.2 证据产物的 F 节结论改为**数据驱动**：`refresh_after_logout == 401` 时呈现「会话级吊销已闭合」，`== 200` 时呈现断点警告 —— 同一条代码路径在修复前后都能得到诚实表述，不会留下过期结论
- [x] 7.3 顺带修掉 `redis.setex` 废弃告警（`_revocation_add` 内改为 `set(..., ex=)`），该函数本就被本变更重构
