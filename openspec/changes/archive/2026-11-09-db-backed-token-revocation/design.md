## Context

`verify_token()` 在每个受保护请求上跑一次（网关中间件 [`middleware.py:89`](../../backend/gateway/middleware.py)，DRF 视图再由 [`drf_auth.py:52`](../../backend/shared/auth/drf_auth.py) 跑第二次），其中「是否被吊销」一项现在是一次 Redis `EXISTS`。登出写一次 `SET ... EX`。

本设计只回答三件事：吊销记录放哪、失败怎么算、怎么保证不引入新的性能/语义问题。

## Decisions

### D1 存储：MySQL 表，不保留 Redis，也不用进程内字典

| 选项 | 否决/采纳理由 |
|---|---|
| 进程内字典 | 单进程可用，但重启后 7 天内的旧令牌复活、多 worker 之间不一致 —— 安全上不可接受 |
| 保留 Redis | 运维多一个常驻服务、失败语义双轨，而它已经不承担缓存/队列/广播 |
| **MySQL 表（采纳）** | MySQL 已是硬依赖；每请求一次唯一索引查询；吊销是低频写。唯一代价是热路径 +1 查询，内部平台 QPS 下可忽略 |

### D2 单表 `kind + ref`，不建两张表

`acc_token_revocations(kind, ref, expires_at)`，`kind ∈ {session, token}`，唯一约束 `(kind, ref)`。
一次查询用 `Q(kind=session, ref=sid) | Q(kind=token, ref=jti)` 同时判定两级吊销；清理只需一条语句。两张表会重复 schema、迁移与清理逻辑，收益只是可读性。

### D3 不做「未吊销」负缓存

给否定结果加 5 秒缓存会让「登出后立刻用旧 access 请求」在窗口内返回 200，直接违反 `auth-session` 的「登出后原 access 失效」场景，也会让现有单测变红。因此 v1 **不缓存**：每次请求查一次唯一索引。
将来若 QPS 证明有必要，可加「缓存否定结果 + 登出时进程内失效」，但多进程仍有 ≤ TTL 的窗口，属另一次变更。

### D4 失败语义：写 fail-closed、读 fail-open（与现状一致）

- **写**（登出）：任何数据库异常 → `BlacklistUnavailableError` → `503` + `retry`。宁可不让你登出，也不假装吊销成功（否则重启后令牌「复活」）。
- **读**（校验）：数据库异常 → 记 error 日志并放行 token。理由：吊销库抖动不应把全员踢下线；且数据库整体不可用时请求本来就在别处失败。
- 已知取舍：极短窗口内已吊销令牌可能可用。这与 Redis 版的取舍相同（只是把「Redis 抖动」换成「DB 抖动」），并写进风险表。

### D5 一个受保护请求只解析一次令牌

网关中间件已经验签并把 `user_id` 注入 `request`；DRF 认证类改为优先复用：

```
user_id = getattr(request, "user_id", "")
if user_id:  # 中间件已验签（/api/ 路径 + Bearer 头）
    直接按 sub 查 User，跳过 verify_token
else:
    回退到 verify_token（DRF 视图被直接调用/测试时仍可用）
```

等价性：同一请求内两次校验之间不存在过期或吊销的可观察变化；DRF 仍按 `sub` 查 `User` 并保留「用户已删除 → 401」的语义。

### D6 过期记录清理

- 判定条件带 `expires_at__gt=now()`，过期行不参与判定，清理只为控制表大小。
- 每次写入吊销记录时顺手删最多 100 条过期行（先取 id 再删，跨库安全）。
- 另导出 `purge_expired()` 供将来的定时任务使用（本变更不接入调度）。

### D7 迁移与回滚

- `apps/accounts` 此前没有 `models.py`，本次新增模型并生成 `0001_initial`。
- 存量 Redis 吊销记录**不迁移**：TTL ≤ `JWT_REFRESH_TTL`（7 天），最迟 7 天自然收敛。
- 如需零窗口：先双写（DB + Redis）一周，再切读 DB。本变更**不实现**双写，只登记为可选的部署手段。
- 回滚：`git revert` + `python manage.py migrate accounts zero`。吊销记录会自然过期，丢表不产生正确性问题（只是已登出的会话在 7 天内可能重新可用）。

### D8 明确不做的事

- 不退役 Redis 服务、不改 `CHANNEL_LAYERS` 配置（它当前 0 调用；是否保留属另一件事）。
- 不改 `JWT_ACCESS_TTL` / `JWT_REFRESH_TTL`，不改 `sid` / `jti` 契约，不改前端。
- 不做「在线会话列表 / 强制下线」——那需要会话 allowlist，是另一条路线。

## Risks

| 风险 | 缓解 |
|---|---|
| DB 抖动期间已吊销令牌短暂可用 | 读失败打 `error` 日志，便于从日志发现；内部平台可接受；与现状同性质 |
| 每请求 +1 次查询 | `(kind, ref)` 唯一索引 + `expires_at` 索引；实测 QPS 低；必要时再引入带失效的缓存 |
| 表无界增长 | 写入时顺手清理 100 条过期行 + `purge_expired()` |
| 旧 Redis 记录未迁移 | TTL 自然收敛（≤7 天）；必要时先双写 |

## Migration Steps

1. 新增模型与迁移，`manage.py migrate`（MySQL / 测试用 `--nomigrations` 直接建表）。
2. 替换 `jwt_auth` 的读写实现，保留 `_revocation_add(kind, ref, ttl)` 这个内部缝（测试需要捕获 TTL）。
3. 登出文案改为存储无关；更新 `accounts/AGENTS.md` 与 `auth-session` 场景。
4. 更新测试：真实 Redis 夹具 → 数据库夹具；新增「过期记录不再生效」「跨重启仍有效」「写失败 503」「一次请求只验一次」四类用例。
5. 门禁：`python run.py check`。
