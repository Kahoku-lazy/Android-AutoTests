## Context

- 现状：唯一性由 `RegisterSerializer.validate()` 的 check-then-act 保证；写口 `api.create_user()` 无任何冲突处理
- 仓库既有解法：`apps/case_manager/api_directories.py:64-74` 与 `apps/element_locator/api_projects.py` ——
  `ConflictError(Exception)` + `with transaction.atomic()` + `except IntegrityError`
- `tests/api/case/register.yaml:176` 已有「用户名已存在 → 409」用例，本变更不得改变该行为
- pytest 的 `django_db` 会把每个用例包在一个事务里，**因此写口必须用 savepoint**，否则一次
  `IntegrityError` 会污染整个用例事务（这也是既有解法用 `transaction.atomic()` 的原因）

## Goals / Non-Goals

**Goals**：让「用户名唯一」在并发下也成立，并把唯一性的权威收敛到一处（写口）。

**Non-Goals**：邮箱唯一性；前端防抖；幂等键；重试。

## Decisions

**D1：以数据库约束为唯一权威，写口翻译异常。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 保留 serializer 的 `exists()`，只在写口加捕获（**否决**） | ❌ | 同一规则存在两处，且真正生效的仍是写口；前置检查给人「已保证」的错觉 |
| 移除前置检查，写口捕获 `IntegrityError` → `ConflictError`（**采用**） | ✅ | 唯一真相源；与 `case_manager`/`element_locator` 既有解法一致；顺序与并发走同一条路径 |

**D2：领域错误放在 `apps/accounts/api.py`。**

该 App 只有一个 `api.py`，无需像 `case_manager` 那样拆出 `api_projects.py` 作为错误宿主。
视图通过 `api.ConflictError` 引用，保持「写口定义契约、视图消费」的方向。

**D3：用 `transaction.atomic()` 包裹写入（savepoint）。**

不只为整洁：Django 在 `IntegrityError` 后事务进入不可用状态，若不用 savepoint 隔离，
调用方（含 pytest 的用例事务）后续查询会报 `TransactionManagementError`。

**D4：`RegisterView` 的 409 判定不再依赖字符串相等。**

原实现靠 `msg == "用户名已存在"` 反查状态码；前置检查移除后该分支消失，
serializer 的其余错误一律 400，409 只从 `ConflictError` 产生 —— 类型驱动而非文案驱动。

## Risks / Trade-offs

- [顺序重名多一次 INSERT 尝试] 唯一索引判定，代价可忽略；换来单一权威
- [文案仍有两处来源] 409 文案在写口，其余校验文案在 serializer —— 两者语义本就不同（数据冲突 vs 输入非法）
- [并发窗口仍在] 本变更不消除竞态，而是让竞态的**结果正确**（409 而非 500）；这是数据库唯一约束应有的角色

## Migration Plan

无需迁移。行为变化仅在并发重名的响应码（500 → 409）。回滚 = 还原三个文件。

## Open Questions

1. 是否给 `email` 也加唯一约束？（会与 Django `User` 内置表结构冲突，需独立评估）
2. `ConflictError` 是否值得提升为 `shared/` 级通用错误，供各 App 复用？（当前各 App 各有一份，共 3 处）
