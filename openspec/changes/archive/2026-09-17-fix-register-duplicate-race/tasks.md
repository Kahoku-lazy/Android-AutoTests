## 1. 变更与规格

- [x] 1.1 `openspec/changes/fix-register-duplicate-race/` 四件套
- [x] 1.2 新能力规格 `specs/auth-registration/spec.md`（4 个 Scenario）
- [x] 1.3 `openspec validate fix-register-duplicate-race` 通过 —— `Change 'fix-register-duplicate-race' is valid`

## 2. 写口（apps/accounts/api.py）

- [x] 2.1 新增 `ConflictError(Exception)` 并加入模块文档说明
- [x] 2.2 `create_user()` 用 `transaction.atomic()` 包裹写入
- [x] 2.3 捕获 `IntegrityError` → `raise ConflictError("用户名已存在")`（`from exc` 保留因果链） —— `raise ConflictError(...) from exc`，`__cause__` 保留底层 IntegrityError

## 3. 视图与校验层

- [x] 3.1 `RegisterView` 捕获 `api.ConflictError` → 409
- [x] 3.2 409 判定改为类型驱动：serializer 的其余错误一律 400 —— 409 只从 `ConflictError` 产生；serializer 错误一律 400（不再靠文案相等反查）
- [x] 3.3 `RegisterSerializer` 移除 `exists()` 前置判重（含其 import 清理）
- [x] 3.4 `apps/accounts/AGENTS.md` 登记「唯一性由写口保证」契约 —— 新增「契约：用户名唯一性」小节

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_register_uniqueness.py`
- [x] 4.2 覆盖 4 个 Scenario：顺序重名 409 / 并发重名 409（强制两个请求都越过前置校验）/ 写口抛 `ConflictError` 而非 `IntegrityError` / 冲突后调用方事务仍可用
- [x] 4.3 跑 `pytest tests/graybox/unit/test_register_uniqueness.py tests/graybox/unit -m auth -q` 全绿 —— 5 passed；`-m auth` 全量 23 passed

## 5. 证据产物与门禁

- [x] 5.1 重跑 `temps/login-backend-map`：B 节「写口重名兜底」实测由 `IntegrityError` 变为 `ConflictError`；`--check` exit 0、verify errs `[]` —— 写口实测 `IntegrityError` → `ConflictError`；指纹 `cd14cdfba544`，`--check` exit 0，verify errs []
- [x] 5.2 `python manage.py check` / `ruff check` / `ruff format --check` / `gen_arch_stats.py --check-boundaries` —— check / ruff / format / 边界检查全部通过
- [x] 5.3 端到端复验：既有 `tests/api/case/register.yaml` 的「用户名已存在 → 409」语义不变（灰盒等价用例覆盖） —— `register.yaml` 的 409 与文案由 `test_sequential_duplicate_returns_409` 等价覆盖
- [x] 5.4 归档并把 delta 同步进 `openspec/specs/auth-registration/spec.md`
## 6. 实施期补记

- [x] 6.1 **A/B 实测证据**：修复前 `api_create_user_duplicate = {"raised": "IntegrityError", "detail": "UNIQUE constraint failed: auth_user.username"}`；修复后 `{"raised": "ConflictError", "detail": "用户名已存在"}` —— 同一测量点、同一采集器
- [x] 6.2 竞态用例的构造方式：真实并发无法稳定复现，故把竞态那一瞬固定下来 —— monkeypatch 写口，在真正插入前先插入一个同名用户。修复前该路径抛未捕获的 IntegrityError → 500
- [x] 6.3 证据产物的 B 节写口结论改为**数据驱动**（`raised === "ConflictError"` 呈现绿色结论，否则呈现 check-then-act 警告），避免修复后仍显示旧结论
- [x] 6.4 采集器原先只捕获 `IntegrityError`，修复后会误记为「未抛异常」；改为同时捕获两种并显式标记 `translated: false`，使回归可被产物直接看见
