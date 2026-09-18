## Why

🟡 **D4「枚举唯一真相源在 `models/`」名存实亡**（D4-1）。设计文档 `设计方案-Django设计系统分层.html` 三处明写该契约：

> 行 269：枚举与领域类型唯一真相源在 `models/`（L1b）；各 App `models.py` 只写表结构。
> 行 331（D4 节点）：Model / ORM —— db_table 显式 · 表前缀 9 类 · **枚举取 models/**
> 行 375（D4 行）：表结构、`db_table`、索引、**枚举 SSOT**

实测（全仓 grep，2026-09-15）：

| `models/` 模块 | 导出符号 | 生产消费方 | 结论 |
|---|---|---|---|
| `ui_nodes.py` | `Node` | `engines/device/base.py` · `engines/device/android/u2.py` | ✅ 真 SSOT |
| `constants.py` | 10 个枚举（`DeviceStatus` / `ConnectionType` / `LockStatus` / …） | **0** | ❌ 空转 |
| `step_types.py` | `StepResult` / `CaseType` / `TestStep` | **0**（仅出现在文档与 `config/api_docs.py` 文本里） | ❌ 空转 |
| `test_models.py` | `TestRunStatus` / `TaskOutcome` | 仅 `tests/graybox/unit/test_example_unit.py` | ⚠️ 仅测试消费 |

与此同时 `apps/device_pool/contracts.py` **重复定义**了 `DeviceStatus` 与 `ConnectionType`（成员与值完全一致）—— 那才是设备域实际在用的那份；`device_pool` 内另有约 70 处字面量（`"ONLINE"` / `"BUSY"` / `"WIFI"` / `"USB"` …）。

即：**声明中的 SSOT 没有任何生产消费方，真正在用的枚举是各 App 自己复制的一份** —— 契约与事实相反。

## What Changes

本单只做**契约落地的第一步**：消除重复定义，让 `models/constants.py` 获得第一个生产消费方。风险更高的字面量全量替换不在本单。

- `apps/device_pool/contracts.py`：删除本地重复的 `DeviceStatus` / `ConnectionType` 类定义，改为 `from models.constants import ConnectionType, DeviceStatus` 再导出 —— 成员与值完全一致，既有 `from .contracts import ...` 调用方（`manager.py` 等）零改动
- 新增 `tests/graybox/unit/test_enum_ssot.py`：断言 `device_pool.contracts` 的两个枚举**就是** `models.constants` 的同一对象（`is`）且成员值一致 —— 防止重复定义再次出现

- **BREAKING**：无（成员值与 `str, Enum` 语义不变；调用方 import 路径不变；未改模型字段默认值）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 契约真相源：`dev_docs/05-开发与测试/设计方案与报告/设计方案-Django设计系统分层.html` 行 269 / 331 / 375
- App 约束：`apps/device_pool/AGENTS.md`（离散取值用 str Enum 消除魔法字符串）· `apps/AGENTS.md` §1.2 分层纪律
- 前置分析：本会话 D4 复查（缺陷 D4-1）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/device_pool/contracts.py`（-8 行类定义，+1 import，模块仍保持纯数据零 I/O）
- 测试：新增 `tests/graybox/unit/test_enum_ssot.py`
- 验证：`manage.py check` · `makemigrations --check`（**不应**产生迁移）· `ruff check .` / `ruff format --check .` · 全量单测 · `--check-boundaries`
- **不在本单范围（D4-1 续做项，需独立变更）**：
  1. `device_pool` 内约 70 处字面量 → 枚举成员。⚠️ `LockStatus.ACTIVE = "active"` / `LockReleaseReason.MANUAL = "manual"` 等 **name≠value** 的枚举要特别小心：`Enum.__hash__` 基于 name，把成员当字典键会与字面量键失配（`DeviceStatus` / `ConnectionType` 因 name==value 无此问题）
  2. `models/step_types.py` 零消费（随 `test_runner` 下线而失活）—— 删除或保留属独立判断
  3. `models/test_models.py` 仅测试消费 —— 同上
