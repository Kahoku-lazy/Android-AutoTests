# accounts · 用户名唯一性

> 归属模块：`backend/apps/accounts` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/accounts/api.py`（`create_user`）
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 契约

唯一性以**数据库唯一约束**为唯一权威：`api.create_user()` 用 `transaction.atomic()`（savepoint）
包裹写入，捕获 `IntegrityError` 并抛 `ConflictError`，由视图映射为 **409**。

- **校验层不做唯一性判重** —— 那是数据不变量，不是输入格式。前置检查只会在并发下造成
  「校验通过、写入炸库」，把问题从 409 变成 500
- **写口不得泄漏 `IntegrityError`**：必须翻译为领域错误，否则会一路冒成 500
- **savepoint 是必需的**：没有它，`IntegrityError` 会让调用方事务进入不可用状态
  （后续查询报 `TransactionManagementError`）

## 关联

错误码归属（409 落点）见 [accounts_paths_and_errors.md](accounts_paths_and_errors.md)。
