## Context

动机见 `proposal.md` - Why。四处 `sub` 下标取值是同一条不变量的四个落点，因此**修在源头**（`verify_token` 保证 `sub` 存在）比四处补防御更小、更不易漏。

## Goals / Non-Goals

**Goals:**

- 响应头不再外发任何密钥材料
- 认证路径不再有静默吞错；缺 `sub` 的令牌统一 401
- 清掉随之产生的零消费函数

**Non-Goals:**

- 不改 **D1-4**（Redis 不可用时吊销检查放行）—— 需用户裁定，本单保持 `_blacklist_contains` 原语义
- 不改 `blacklist_token` / `_blacklist_add` 的硬失败语义（登出已 fail-closed）
- 不改 `gateway/middleware.py` / `apps/accounts/views.py` / `drf_auth.authenticate()` 的取值写法（上游不变量已覆盖）

## Decisions

### 1. realm 用静态串

- **选择**：`realm="api"`
- **理由**：RFC 6750 的 realm 是给人看的保护域标识；把密钥前缀写进去等于把秘密材料放进每个 401 响应头（可被任意客户端与日志收集）

### 2. 预检不再兜底，改为上抛

- **选择**：删掉 `except Exception: pass`，不做「日志后继续」
- **理由**：预检的存在意义就是吊销与类型校验；吞掉它的异常等于静默跳过吊销。上抛后由 `middleware.py:82` 与 `drf_auth.py:54` 的 `except Exception` 包成 **401**，是 fail-closed 的正确方向（也符合根 `AGENTS.md`「错误不应默默忽略」）

### 3. 缺 `sub` 修在 `verify_token`（单点）

- **选择**：`if not payload.get("sub"): raise jwt.InvalidTokenError(...)`
- **理由**：四个调用点（middleware / drf_auth / accounts.RefreshView / `get_user_id_from_token`）都先调 `verify_token`，单点不变量即可让它们全部安全；四处补 `.get()` 属重复防御
- **验证**：新增测试同时覆盖「单元层抛错」与「HTTP 层 401 而非 500」

### 4. 删 `is_blacklisted` 与 `decode_token`

- **选择**：两个函数一并删除
- **理由**：`is_blacklisted` 零消费者且自带静默 fail-open；删掉它之后 `decode_token` 也零消费者（全仓唯一调用点就是 `is_blacklisted`）——留一个只为不存在调用方服务的公开函数等于把死代码留在 shared 层

## 模块防火墙自检

- 跨 App import：不涉及（`shared/auth` 为共享层）
- 写库：不涉及 · 引擎/通道边界：不涉及

## Risks / Trade-offs

- [上抛导致某些畸形令牌从 401 变 5xx] → 上游两处都是 `except Exception` 包裹并返回 401，由新增测试断言 401
- [删除公开函数影响外部调用方] → 全仓检索 `is_blacklisted` / `decode_token` 仅剩定义本身（0 外部引用）

## Migration Plan

1. 改 `drf_auth.py`（realm + import）与 `jwt_auth.py`（预检 / sub 守卫 / 删两函数）
2. 新增 `tests/graybox/unit/test_jwt_hardening.py`
3. `manage.py check` + `ruff check` + 相关测试 + unit 全量
4. 归档；回滚 = `git checkout` 两个源文件 + 删测试
