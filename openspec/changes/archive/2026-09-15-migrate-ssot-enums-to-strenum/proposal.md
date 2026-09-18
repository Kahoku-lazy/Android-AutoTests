## Why

🟠 **`models/` 枚举 SSOT 全部用 `(str, Enum)`，`str(member)` 返回限定名而非取值**（D4-1 的深层缺陷）。实测（Python 3.13.14）：

| 写法 | `str(m)` | `f"{m}"` | `m == m.value` | `isinstance(m, str)` | `json.dumps(m)` |
|---|---|---|---|---|---|
| `class X(str, Enum)` | `'DeviceStatus.ONLINE'` ❌ | `'DeviceStatus.ONLINE'` ❌ | True | True | `"ONLINE"` ✅ |
| `enum.StrEnum` | `'ONLINE'` ✅ | `'ONLINE'` ✅ | True | True | `"ONLINE"` ✅ |

具体危害（`class LockStatus(str, Enum): ACTIVE = "active"` 更严重，取值与成员名都不同）：

1. **写库**：`Device._meta.get_field("status").get_prep_value(DeviceStatus.ONLINE)` 实测**原样返回枚举成员**（Django 不强制 `str()`）→ 落库字符串由驱动决定；MySQL 侧参数按 `%s` 格式化即得 `"DeviceStatus.ONLINE"`，**静默写入错值**。
2. **文案 / 日志**：`f"{m}"` 与 `"%s" % m` 会输出 `"LockStatus.ACTIVE"`，而契约要求 `"active"`（如 `apps/evaluator/AGENTS.md` 的「状态字面量双边同步」）。
3. **它是 D4-1 字面量收敛的前置阻塞**：收敛动作就是把 `"ONLINE"` / `"active"` 换成枚举成员 —— 在当前基类下这么做会直接踩中上述两点。

**当前是潜伏陷阱而非现网 bug**（已实测定性）：全仓「枚举成员 → ORM 字段」的赋值点**为零**（`device_pool` 的写仍用字面量；唯一命中是 `contracts.py` 的 dataclass 默认值），故本单是**在收敛之前先拆掉地雷**。

## What Changes

- `models/constants.py`：`from enum import Enum` → `from enum import StrEnum`；10 个枚举基类 `(str, Enum)` → `(StrEnum)`
- `models/test_models.py`：同上 3 个枚举（`TestRunStatus` / `TaskOutcome` / `TaskCardStatus`）——同一缺陷类、同一 SSOT 包
- 新增 `tests/graybox/unit/test_ssot_enum_strenum.py`：**动态发现**两模块内全部枚举子类，逐个断言
  `str(m) == m.value` · `f"{m}" == m.value` · `isinstance(m, str)` · `m == m.value` · `hash(m) == hash(m.value)`
  —— 用动态发现而非硬编码清单，新增枚举自动纳入门禁

- **BREAKING**：无。所有既存消费方都走 `.value`（`TaskOutcome.terminal_values` / `fail_values` / `choices` 与 `test_models` 的调用点）；`isinstance(m, str)`、`==`、hash、JSON 行为实测均不变
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html` 行 269 / 331 / 375（枚举唯一真相源在 `models/`）
- 前置变更：`activate-enum-ssot`（2026-09-15 归档，令 `device_pool/contracts.py` 转发 `models.constants`）
- 门禁：`django-backend-check/references/calibration.md` §2（🔴 含「假状态反馈」；本项为**潜伏**写库错值，未达现行 bug → 记 🟠）· §4 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`models/constants.py`（1 import + 10 基类）· `models/test_models.py`（1 import + 3 基类）
- 测试：新增 `tests/graybox/unit/test_ssot_enum_strenum.py`
- 验证：`manage.py check` · `makemigrations --check`（**不应**产生迁移：枚举基类不是模型字段）· `ruff` · 全量单测 · `--check-boundaries`
- **不在本单范围**：`models/step_types.py` 的 3 个枚举是**裸 `Enum`**（非 str 混入），语义不同，不属本缺陷类；是否改由 STEP 域自己的变更裁决
