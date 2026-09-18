## 1. 复核

- [x] 1.1 复验行仍在；验证：修复前检索命中 `shared/auth/drf_auth.py:66`（realm 用 SECRET_KEY[:8]）· `gateway/middleware.py:81` · `shared/auth/drf_auth.py:60` · `apps/accounts/views.py:111` · `shared/auth/jwt_auth.py:205` 五处 `payload["sub"]`/realm
- [x] 1.2 `is_blacklisted` / `decode_token` 零外部消费者；验证：全仓检索仅剩定义处（`jwt_auth.py:170,227`；`decode_token` 唯一调用点就是 `is_blacklisted`）

## 2. 修改

- [x] 2.1 `shared/auth/drf_auth.py`：realm 改静态串 `"api"`（附注释说明禁止密钥材料）；删除随之无用的 `from django.conf import settings`
- [x] 2.2 `shared/auth/jwt_auth.py`：`verify_token` 去掉 `try/except InvalidTokenError/except Exception: pass` 包装（异常上抛 → 上游 fail-closed 401）；返回前新增 `sub` 守卫 `Token missing sub claim`；删除 `is_blacklisted()` 与 `decode_token()`
- [x] 2.3 新增 `tests/graybox/unit/test_jwt_hardening.py` 三条：`verify_token` 缺 sub 抛 `InvalidTokenError` · 请求该令牌得到 **401（非 500）** · `authenticate_header` 不含 `SECRET_KEY[:8]`

## 3. 验证

- [x] 3.1 `python manage.py check` → no issues，exit 0；`python -m ruff check shared/auth tests/graybox/unit/test_jwt_hardening.py` → All checks passed
- [x] 3.1b `ruff format --check`：**初次未过**（`jwt_auth.py` 与新增测试各被判定需格式化）→ 已 `ruff format` 修正；复验 `5 files already formatted` exit 0。归因：`git show HEAD:shared/auth/jwt_auth.py | ruff format --check --stdin-filename … -` **无输出**（HEAD 版本原本合规），即不兼容写法由本次改动引入、也已由本次清掉
- [x] 3.2 目标测试：`test_jwt_hardening.py`(3) + `test_csrf_protection.py`(6) + `test_channels.py`(6) = **15 passed**；格式化后复跑 9 passed
- [x] 3.3 `pytest tests/graybox/unit -q` → **78 passed**（基线 75 + 新增 3，无新增失败）
- [x] 3.4 范围核对：仅 `shared/auth/drf_auth.py` · `shared/auth/jwt_auth.py` 两个源文件 + 1 个新增测试文件

## 4. 范围外登记

- [x] 4.1 **D1-4 未动**：`_blacklist_contains` 在 Redis 不可用时仍放行（需用户裁定：保留并登记 or 加严格开关）。本单只改「预检不再静默吞异常」，**未改吊销检查本身的降级语义**
- [x] 4.2 顺带留档：`gateway/middleware.py:82` 与 `shared/auth/drf_auth.py:54` 的 `except Exception` 是本单依赖的 fail-closed 兜底（已由测试覆盖 401 断言），无需改动
