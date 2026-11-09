## Why

登出吊销记录目前存在 Redis 里（`jwt:session_revoked:<sid>` / `jwt:blacklist:<jti>`），于是 Redis 成了平台唯一一个「只为这一件事而必须常驻」的外部服务：它不承担缓存（`settings.py` 没有 `CACHES`，任务报告缓存走的是默认 `LocMemCache`）、不承担任务队列（无 celery），channels 的 channel layer 虽然配了 Redis 后端，但唯一的生产 consumer 明确不接 channel layer（[`consumer.py:88-101`](../../backend/apps/knowledge_assistant/consumer.py)），当前全仓 0 处 `group_send`。

代价有三条：

1. 部署与运维多一个必须常驻、还必须开持久化（`run.py` 用 `--save 900 1`）的组件；
2. 多一套并行的失败语义「读放行 / 写 503」，与数据库已有的失败语义分开维护；
3. 吊销记录只活在一个 Redis 实例里，换机器或清库即丢失，而平台其余需要持久的状态都在 MySQL。

平台已经硬依赖 MySQL；会话吊销是低频写（每次登出 1 行）、低频读（每请求 1 次主键查询，内部平台 QPS 很低），迁过去不引入新的运维对象。

## What Changes

- 新增 `apps/accounts` 的吊销表 `acc_token_revocations`（`kind` + `ref` + `expires_at`，唯一约束 `(kind, ref)`，`expires_at` 上有索引），取代 Redis 的两个键前缀；写库一律经 `apps/accounts/api.py`。
- `shared/auth/jwt_auth.py` 删除 Redis 客户端、键前缀与连接自愈逻辑，改为写/查该表；`BlacklistUnavailableError` 的含义变为「吊销存储写入失败」，登出仍映射 `503` + `retry`（对外契约不变，文案从「Redis 不可用」改为「吊销服务不可用」）。
- 合掉一处重复鉴权：DRF 认证类复用网关中间件已解析出的 `request.user_id`，使一个受保护请求只解析一次令牌（此前中间件与 DRF 各解析一次 = 2 次 JWT 解码 + 2 次吊销查询）。
- 文档与场景措辞：`backend/apps/accounts/AGENTS.md` 与 `auth-session` 的「Redis 不可用时拒绝登出」改为存储无关表述。

## Impact

- 受影响的能力：`auth-session`（登出与吊销校验）。`logout` 对前端的行为不变：成功 200，存储不可用 503 + `retry`。
- 数据：新增 1 张表。存量 Redis 吊销记录**不迁移**——其 TTL ≤ `JWT_REFRESH_TTL`（7 天），最迟 7 天自然收敛；如需零窗口可先双写一周再切读。
- 依赖：Redis 不再是登录/登出的必需依赖。`run.py` 的 redis 服务与 channel layer 配置保持不变（退役 Redis 属另一件事，见设计文档「不做的事」）。
- 不做：不改令牌 TTL、不改 `sid` / `jti` 契约、不改前端、不新增管理端接口。
