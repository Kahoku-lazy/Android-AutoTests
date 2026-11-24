# accounts · 会话与登出

> 归属模块：`backend/apps/accounts` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/accounts/api.py`、`backend/gateway/middleware.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 契约

- **会话标识**：一次登录签发的 access 与 refresh 共享同一个 `sid`（`create_token_pair()` 生成）。
  该 claim 只存在于令牌内部，**不得出现在任何 API 响应里**（接口形状与前端均不受影响）。
- **登出 = 作废整个会话**：`POST /api/auth/logout` 按 `sid` 吊销，access 与 refresh 一起失效。
  同时保留按 `jti` 吊销，用于兜底本契约生效前签发、没有 `sid` 的旧令牌。
- **续期必须透传 `sid`**：`RefreshView` 换发新 access 时须带 `payload.get("sid")` ——
  否则续期后的令牌会脱离会话管辖（登出撤不掉它）。
- **吊销记录 TTL = `JWT_REFRESH_TTL`**：登出请求只携带 access（1h），但同会话的 refresh 还有至多 7d 寿命；
  TTL 取短了会让 refresh 在记录过期后恢复可用。
- **停用 = 账号档吊销**：`kind=user`，`ref` 为账号主键。判定时令牌 `iat` 早于该行
  `created_at`（含同一秒）才算作废。启用不删该行：新登录的 `iat` 更晚所以放行，停用前的旧令牌仍然无效。
- **吊销记录落库**：判定只看未过期行（`expires_at > now()`），写入时顺手清理一批过期行；
  服务重启不清空吊销状态，也不再依赖 Redis。
- **fail-closed**：吊销写入失败（吊销存储不可用，如数据库异常）时登出返回 `503` + `retry`，不得假装成功。
  校验侧（读）遇存储故障记 error 日志并放行 token —— 不让吊销库抖动把全员踢下线。

## 相关端点

`POST /api/auth/login` → 签发（带 `sid`）｜`POST /api/auth/refresh` → 换发（须透传 `sid`）｜
`POST /api/auth/logout` → 按 `sid`/`jti` 吊销。路径与错误码见
[accounts_paths_and_errors.md](accounts_paths_and_errors.md)。
