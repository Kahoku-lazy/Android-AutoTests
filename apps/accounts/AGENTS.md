# accounts — 模块约束

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `apps/AGENTS.md` 优先于本文件（本文件只写增量）。

登录鉴权模块。**没有自有表**（无 `models.py`），直接使用 Django 内置 `auth_user`；
写操作全部收敛在 `api.py`（`__all__ = ["create_user"]`）。
规格真相源：`openspec/specs/auth-session/spec.md`。

## 契约：会话与登出

- **会话标识**：一次登录签发的 access 与 refresh 共享同一个 `sid`（`create_token_pair()` 生成）。
  该 claim 只存在于令牌内部，**不得出现在任何 API 响应里**（接口形状与前端均不受影响）。
- **登出 = 作废整个会话**：`POST /api/auth/logout` 按 `sid` 吊销，access 与 refresh 一起失效。
  同时保留按 `jti` 吊销，用于兜底本契约生效前签发、没有 `sid` 的旧令牌。
- **续期必须透传 `sid`**：`RefreshView` 换发新 access 时须带 `payload.get("sid")` ——
  否则续期后的令牌会脱离会话管辖（登出撤不掉它）。
- **吊销记录 TTL = `JWT_REFRESH_TTL`**：登出请求只携带 access（1h），但同会话的 refresh 还有至多 7d 寿命；
  TTL 取短了会让 refresh 在记录过期后恢复可用。
- **fail-closed**：吊销写入失败（Redis 不可用）时登出返回 `503` + `retry`，不得假装成功。

## 契约：用户名唯一性

唯一性以**数据库唯一约束**为唯一权威：`api.create_user()` 用 `transaction.atomic()`（savepoint）
包裹写入，捕获 `IntegrityError` 并抛 `ConflictError`，由视图映射为 **409**。

- **校验层不做唯一性判重** —— 那是数据不变量，不是输入格式。前置检查只会在并发下造成
  「校验通过、写入炸库」，把问题从 409 变成 500
- **写口不得泄漏 `IntegrityError`**：必须翻译为领域错误，否则会一路冒成 500
- **savepoint 是必需的**：没有它，`IntegrityError` 会让调用方事务进入不可用状态
  （后续查询报 `TransactionManagementError`）

## 路径约定

`urls.py` 里的路径**必须带尾斜杠**（`login/` / `register/` / `refresh/` / `logout/` / `me/`）。
`POST /api/auth/login/` 命中；`POST /api/auth/login` 是 **404** —— 容错中间件已删除、
`APPEND_SLASH=False`，缺失尾斜杠不会再被重定向或改写（见 `openspec/specs/api-path-convention`）。

## 错误码

| 端点 | 码 | 触发 |
|---|---|---|
| login | 200 / 400 / 401 | 成功 / 用户名或密码缺失 / 凭证错误 |
| register | 200 / 400 / 409 | 成功 / 长度·一致性·邮箱校验 / 用户名已存在 |
| refresh | 200 / 401 | 换新 access / refresh 无效、已吊销或类型错 |
| logout | 200 / 503 | 已吊销 / Redis 不可用（拒绝登出） |
| me | 200 / 401 / 404 | 身份 / 无令牌或已吊销 / 用户已删除 |
