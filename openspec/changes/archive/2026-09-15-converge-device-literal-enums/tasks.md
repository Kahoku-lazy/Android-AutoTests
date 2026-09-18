## 1. 复核（已完成）

- [x] 1.1 全量清点 `device_pool` 字面量：`api.py` 14 · `views.py` 9 · `manager.py` 46 · `models.py` 5 · `urls.py` 1
- [x] 1.2 逐条判定「是枚举值 vs 同形非枚举」：`api.py "timeout": timeout`（响应键，**不是** `LockReleaseReason`）· `manager.py {"released": True}`（布尔响应键，**不是** `LockStatus`）· `manager.py "offline" in error_msg`（错误文本子串）· `reason="purge"/"offline"`（枚举**无**该成员）· `urls.py` 路径段
- [x] 1.3 定下 `models.py` 全部不改（字段 default + `Q(status="active")` + `self.status != "active"`），以保 `makemigrations --check` 绿
- [x] 1.4 确认 import 现状：`manager.py` 已有 2 个枚举；`api.py` 只引 `RUNNER_OCCUPIED_PREFIXES`；`views.py` 不引枚举；`LockStatus`/`LockReleaseReason` 全 App 零 import
- [x] 1.5 确认替换可行性：`StrEnum` 下 `member == "literal"` 为 True、`hash` 相等（故以枚举为键的 `status_order` 仍可按字符串查）、`str()` 返回取值

## 2. 修改

- [x] 2.1 `contracts.py`：转发面扩到四枚举，并**显式加 `__all__`**
- [x] 2.2 `api.py`：补 import + **13** 行定点替换
- [x] 2.3 `views.py`：补 import + **9** 行定点替换
- [x] 2.4 `manager.py`：补 import + **40** 行定点替换
- [x] 2.5 新增 `tests/graybox/unit/test_device_enum_literals.py`（5 条：写入往返 / 按成员过滤 / `update_fields` / 设备锁 `filter().update()` / 枚举键字典按字符串查）

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check --dry-run` → **`No changes detected`**（未碰 `models.py` 的设计生效）
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → 0 待重排
- [x] 3.3 `pytest tests/graybox/unit tests/arch -q` → **104 passed**（99 + 新增 5）；`pytest tests/graybox/integration -q` → **16 passed**（含 `test_device_registry` · `test_device_serializer` · `test_device_state_machine` —— 62 处替换的行为兜底）
- [x] 3.4 复扫字面量：剩余命中 **恰为 skip 名单**（`api.py:119` · `manager.py:217/326/439/442/522/567` · `models.py` ×5 · `urls.py:26` · migrations），零意外残留
- [x] 3.5 `--check-boundaries` → 零违规；范围 `git diff --numstat` = api.py 22/14 · contracts.py 14/15 · manager.py 57/41 · views.py 21/9（`models.py` 的 8/2 是**既有会话改动** `name-all-model-indexes`，非本单）

## 4. 过程中发现并修正的坑（值得记下）

**`ruff check --fix` 会把「只为转发而 import」的名字当 F401 删掉。** `contracts.py` 本文件不使用 `LockStatus` / `LockReleaseReason`，加进 import 后 `--fix` 直接删除，导致 `manage.py check` 报
`ImportError: cannot import name 'LockReleaseReason' from 'apps.device_pool.contracts'`。
修法：给 `contracts.py` 加显式 `__all__` 声明转发面（F401 认可 `__all__` 中的名字为已使用）。
**教训**：对「转发/再导出模块」跑 `ruff check --fix` 后必须复跑 `manage.py check`，不能只看 lint 绿。

## 5. 续做

1. `LockReleaseReason` 缺 `PURGE` / `OFFLINE` 两个实际在用的原因值 —— 是补枚举（契约变更，需与迁移/前端口径一起看）还是把这两个值规范掉，另单裁决
2. `models.py` 的字段 `default` 与 `UniqueConstraint.condition` 仍是字面量；若要收敛需先验证 Django 是否判定字段变更（本单刻意规避）
3. `apps/ai_assistant` 侧字面量（`"failed"` / `"running"` / `"dashscope"` 等）仍未使用任何 `models/` 枚举，属 D4-1 的另一半
