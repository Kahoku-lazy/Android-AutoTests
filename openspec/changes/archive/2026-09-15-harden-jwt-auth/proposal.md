## Why

D1（接入与通道）复查实测出 4 处鉴权实现缺陷（均已在本轮工作区二次核验仍在）：

| # | 现象 | 证据 |
|---|------|------|
| D1-1 | `WWW-Authenticate` 响应头把 **SECRET_KEY 前 8 位当 realm 外发** | `shared/auth/drf_auth.py:66` 的 `authenticate_header` 用 `settings.SECRET_KEY[:8]` 拼 realm |
| D1-2 | `verify_token` 里「吊销 / 类型」预检整段被 `except Exception: pass` 静默吞掉 —— 预检异常时跳过吊销检查直接进第二段 | `shared/auth/jwt_auth.py:180-192` |
| D1-3 | 合法签名但**缺 `sub`** 的令牌 → 直接下标取 `sub` 抛 KeyError → **500**（应 401） | 四处：`gateway/middleware.py:81` · `shared/auth/drf_auth.py:60` · `apps/accounts/views.py:111` · `shared/auth/jwt_auth.py:205` |
| D1-5 | `is_blacklisted()` 零消费者 + `except Exception: return False`（静默 fail-open）；其唯一调用方 `decode_token()` 也随之零消费者 | `jwt_auth.py:170-173` · `:227-233` |

## What Changes

- `shared/auth/drf_auth.py`：realm 改为**静态串** `"api"`（realm 是协议标识，禁止携带密钥材料）；随之删除只剩此处一处用法的 `from django.conf import settings`
- `shared/auth/jwt_auth.py`：
  1. `verify_token` **去掉裸 `except Exception: pass`**（意外异常上抛 → 上游中间件/DRF 均包成 401，属 fail-closed），保留 `InvalidTokenError` 原样上抛
  2. `verify_token` 返回前**统一校验 `sub`**：缺失即抛 `InvalidTokenError` —— 这一处不变量同时覆盖 D1-3 的四个调用点（它们都在 `verify_token` 之后才下标取 `sub`）
  3. 删除零消费者的 `is_blacklisted()` 与其唯一调用方 `decode_token()`
- 新增回归测试 `tests/graybox/unit/test_jwt_hardening.py`：缺 `sub` 的合法令牌 → `verify_token` 抛错、HTTP **401（不是 500）**；`authenticate_header` 不得含 SECRET_KEY 前缀

- **BREAKING**：无（正常令牌行为不变；缺 `sub` 的异常令牌由 500 变 401）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 前置分析：本会话 D1 复查（缺陷 D1-1 / D1-2 / D1-3 / D1-5）
- 门禁：`.agents/skills/django-backend-check/references/calibration.md` §2（静默吞错定级）· §7（强制命令必跑）
- **不在本单**：D1-4（吊销检查在 Redis 不可用时放行）需用户裁定，本单不动 `_blacklist_contains` 语义

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`shared/auth/drf_auth.py` · `shared/auth/jwt_auth.py`（净删除约 15 行）
- 测试：新增 `tests/graybox/unit/test_jwt_hardening.py`
- 验证：`manage.py check` · `ruff check`（两文件）· 新增测试 + `test_csrf_protection.py`（6）+ `tests/arch/test_channels.py`（6）+ `tests/graybox/unit` 全量
