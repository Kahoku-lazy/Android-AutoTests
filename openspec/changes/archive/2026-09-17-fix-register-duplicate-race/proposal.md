## Why

注册的用户名唯一性由**输入校验层**用 check-then-act 保证：
`RegisterSerializer.validate()` 先 `User.objects.filter(username=...).exists()` 判重，
真正的写入在 `apps/accounts/api.py:create_user()`，而写口**不捕获任何冲突**。实测：

```
经 serializer 判重（顺序请求）        -> 409 用户名已存在
直接调 api.create_user() 重名         -> IntegrityError: UNIQUE constraint failed: auth_user.username
```

两个请求同时通过判重（并发、连点提交、重试）时，第二个会在写口抛出未被捕获的
`IntegrityError` → **500**。这是**用户操作层可直接触发**的缺陷：前端按钮禁用只能降低概率，不能消除。

同类问题在本仓库已有既定解法（`apps/case_manager/api_directories.py:64-74`）：
**以数据库唯一约束为唯一权威，在写口把 `IntegrityError` 翻译成领域错误 `ConflictError`**，
由视图映射为 409。本变更把注册路径对齐到该解法。

## What Changes

- `apps/accounts/api.py`：新增领域错误 `ConflictError`；`create_user()` 用 `transaction.atomic()` 包裹写入，
  捕获 `IntegrityError` 并 `raise ConflictError("用户名已存在")`（savepoint 隔离，不破坏调用方事务）
- `apps/accounts/views.py`：`RegisterView` 捕获 `ConflictError` → `409`；串映射简化为「其余校验一律 400」
- `apps/accounts/serializers.py`：**移除** `RegisterSerializer` 里的 `exists()` 前置判重 ——
  唯一性是**数据不变量**，属于写口，不属于输入校验层；保留它会给读者「唯一性已保证」的错误印象
- `apps/accounts/AGENTS.md`：登记「唯一性由写口保证」契约

**对用户可见行为**：并发重名由 **500 变为 409**；顺序重名仍为 409 与同一文案（`tests/api/case/register.yaml` 的既有用例不变）

**Non-goals**：
- 不做邮箱唯一性（Django `User.email` 非唯一，属独立需求）
- 不改前端（按钮禁用等防抖策略与本变更正交）
- 不引入重试/幂等键（注册不是幂等操作，重名即应失败）

## Capabilities

### New Capabilities

- `auth-registration`：注册写入的唯一性权威与冲突语义（写口保证唯一、冲突映射 409、事务不被破坏）

### Modified Capabilities

（无）

## Impact

- 后端：`apps/accounts/{api,views,serializers}.py`
- 前端：无
- API 契约：路径与响应形状不变；`register` 的 409 语义不变，**新增的是它在并发下也成立**
- 测试：新增 `tests/graybox/unit/test_register_uniqueness.py`
- 证据产物：`temps/login-backend-map/` 需重跑（B 节写口实测由「IntegrityError」变为「ConflictError → 409」）
