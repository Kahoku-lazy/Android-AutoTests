## Why

🟡 **D4-1 的下半段：设备域字面量未收敛到 `models/` 枚举**。上一变更 `migrate-ssot-enums-to-strenum` 已把 `models/` 枚举改为 `StrEnum`（`str(member) == member.value`），拆掉了「成员当字符串用会产出限定名」的地雷；本单据此把 `device_pool` 里的散落字面量换成枚举成员。

未收敛时的实际风险（不是风格问题）：

- 状态字面量在 `api.py` / `views.py` / `manager.py` 三处各写一遍（`"ONLINE"` / `"BUSY"` / `"WIFI"` / `"USB"` / `"active"` / `"released"` / `"manual"` / `"timeout"` / `"disconnect"`），**共 62 处**；改一处口径要同时改三处，漏一处就是状态机静默分叉
- `device_pool/contracts.py` 已按 D4 契约转发 `models.constants` 的枚举，但**只在 `DeviceInfo` 的字段声明里用**，业务逻辑全用字面量 —— 「枚举是 SSOT」在设备域实际上没有生效
- `LockStatus` / `LockReleaseReason` 两个枚举当前**零消费**（`"active"` / `"released"` / `"manual"` 等只在设备锁的 filter/save 里裸写）

## What Changes

- `apps/device_pool/contracts.py`：转发面从「`ConnectionType` + `DeviceStatus`」扩到四枚举（补 `LockStatus` / `LockReleaseReason`），使 App 内统一从契约模块取
- `apps/device_pool/api.py`（13 处）· `views.py`（9 处）· `manager.py`（40 处）：`DeviceStatus` / `ConnectionType` / `LockStatus` / `LockReleaseReason` 的字面量换成枚举成员；三文件补 import
- 新增 `tests/graybox/unit/test_device_enum_literals.py`：钉住本次依赖的不变量 —— 枚举成员写入 `CharField` 后**读回是普通取值串**、`filter(status=member)` 命中、`update_fields` 保存不为 `"DeviceStatus.ONLINE"`

- **BREAKING**：无。`StrEnum` 成员与字面量 `==` / 同 hash、`str()` 返回取值、JSON 输出一致；`device_pool` 既有单测与集成测（`test_device_detector` · `test_device_state_machine` · `test_device_serializer`）为行为兜底
- 按 schema 约定设 `skip_specs: true`

## 明确**不改**的地方（逐条有理由）

| 位置 | 字面量 | 为什么不改 |
|---|---|---|
| `apps/device_pool/models.py` | `default="USB"` / `default="ONLINE"` / `default="active"` / `Q(status="active")` / `self.status != "active"` | **避免迁移**：字段 `default` 与约束 `condition` 参与 deconstruct，换枚举可能让 Django 判定字段变更 |
| `api.py:111` | `"timeout": timeout` | 是**响应字典的键**（锁剩余秒数的字段名），不是 `LockReleaseReason` |
| `manager.py:507` | `{"serial": ..., "released": True}` | 是**布尔响应的键**，不是 `LockStatus` |
| `manager.py:210` | `"offline" in error_msg.lower()` | 是对错误文本做子串判断，不是状态值 |
| `manager.py:319,426,429` · `552` | `reason="purge"` / `reason="offline"` / `"offline": removed` | `LockReleaseReason` **没有** PURGE / OFFLINE 成员；扩展枚举属契约变更，另单裁决 |
| `urls.py:26` | `"<str:serial>/disconnect"` | 是 URL 路径段，不是枚举值 |
| `migrations/**` | — | 历史记录，不得改 |

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html` 行 269 / 331 / 375
- 前置变更：`activate-enum-ssot`（转发面建立）· `migrate-ssot-enums-to-strenum`（拆掉 `str()` 地雷，本单的前置条件）
- App 约束：`apps/device_pool/AGENTS.md`（「状态/类型等离散取值用 str Enum 定义，消除魔法字符串；对外序列化用 `.value`」—— 本单令该条真正落地）
- 门禁：`django-backend-check/references/calibration.md` §2 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/device_pool/contracts.py`（+2 转发名）· `api.py`（13 处 + import）· `views.py`（9 处 + import）· `manager.py`（40 处 + import）
- 测试：新增 `tests/graybox/unit/test_device_enum_literals.py`
- 验证：`manage.py check` · `makemigrations --check`（**必须** `No changes detected`：本单刻意不碰 `models.py`）· `ruff check .` / `ruff format --check .` · `pytest tests/graybox/unit tests/arch` · 设备集成测 · `--check-boundaries`
