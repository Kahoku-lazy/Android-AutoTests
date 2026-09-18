## ADDED Requirements

### Requirement: 用户名唯一性由写口保证

用户名的唯一性 SHALL 以数据库唯一约束为唯一权威。
`apps/accounts/api.py` 的用户创建 SHALL 在冲突时抛出领域错误 `ConflictError`，不得泄漏 `IntegrityError`。
HTTP 视图 SHALL 将 `ConflictError` 映射为 `409` 与文案「用户名已存在」。

前置校验（serializer 的 `exists()`）**不得**作为唯一性保证；写入冲突 SHALL 在写口被翻译为领域错误。

#### Scenario: 顺序重名注册

- **WHEN** 使用已存在的用户名调用 `POST /api/auth/register`
- **THEN** 返回 409，且响应 message 为「用户名已存在」

#### Scenario: 并发重名注册

- **WHEN** 两个请求以同一用户名并发通过前置校验并各自尝试写入
- **THEN** 后写入者返回 409，而不是 500
- **AND** 先写入者的账号保持完好

#### Scenario: 写口不泄漏底层异常

- **WHEN** 直接调用 `api.create_user()` 且用户名已存在
- **THEN** 抛出 `ConflictError`
- **AND** 不抛出 `IntegrityError`

#### Scenario: 冲突不破坏调用方事务

- **WHEN** 写口因重名失败，且调用方处于一个更大的事务中
- **THEN** 失败被 savepoint 隔离，调用方事务仍可继续执行后续写操作
