## Context

D4 契约要求 `models/` 为枚举唯一真相源（文档行 269/331/375），实测该模块零生产消费，而 `apps/device_pool/contracts.py` 复制了一份同值枚举。本单先消除「两个定义」，再谈「字面量收敛」。

## Goals / Non-Goals

**Goals:**

- 消除 `DeviceStatus` / `ConnectionType` 的重复定义，令 `models/constants.py` 成为设备域枚举的唯一定义点
- 用测试把「同一对象」这一不变量固定下来，防止重复定义回归

**Non-Goals:**

- 不做 `device_pool` 内约 70 处字面量的全量替换（触及 30s 心跳与状态机核心，风险与收益不匹配；且 `name≠value` 的枚举有 `Enum.__hash__` 陷阱）
- 不删 `models/step_types.py` / `models/test_models.py`（失活原因与处置属独立判断）
- 不改模型字段默认值（会触发无谓迁移）

## Decisions

### 1. 改定义点，而不是改消费方

- **选择**：`contracts.py` 从 `models.constants` 导入后导出，保留 `from .contracts import DeviceStatus` 的既有 import 路径
- **理由**：`apps/device_pool/AGENTS.md` 把 `contracts.py` 定为「数据契约文件」；保持它的导入面不变可让本单 diff 只落在定义处，零调用方改动

### 2. 用 `is` 断言而不是值相等断言

- **选择**：`assert device_contracts.DeviceStatus is models_constants.DeviceStatus`
- **理由**：值相等的断言在「两份重复定义」下也会通过 —— 那正是本单要防的病。`is` 才能证明只有一个定义

### 3. 不顺手删零消费的 SSOT 模块

- **选择**：本单不删 `step_types.py` / `test_models.py`
- **理由**：`rules` 明确「只碰必须碰的」；`step_types.TestStep` 仍出现在 `config/api_docs.py` 的文档文本与 ARCH-00 的架构叙述里，删它要先判定「文档是否也要改」，属另一个变更的裁决面

## Risks / Trade-offs

- [导入 `models` 顶层包是否安全] → `models/constants.py` 只依赖标准库 `enum`，`models/__init__.py` 无可执行副作用；`contracts.py` 仍是无 I/O 纯数据模块
- [`str, Enum` 语义是否变化] → 两个定义成员名与值逐字相同，`isinstance(x, str)` / 比较 / 序列化行为不变；由既有 device 单测兜底
- [模型默认值是否受影响] → 未改 `models.py`，`makemigrations --check` 必须仍为 `No changes detected`

## Migration Plan

1. `contracts.py`：删两个类定义，改为 `from models.constants import ...`
2. 新增 `test_enum_ssot.py`（`is` 断言 + 值断言）
3. 验证 `manage.py check` · `makemigrations --check` · `ruff` · 全量单测 · `--check-boundaries`
4. 归档；回滚 = `git checkout apps/device_pool/contracts.py` + 删测试
