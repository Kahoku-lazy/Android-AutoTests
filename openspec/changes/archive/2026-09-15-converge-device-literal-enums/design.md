## Context

`models/` 已是 `StrEnum` SSOT，`device_pool/contracts.py` 已转发其中两个枚举，但 62 处业务字面量仍散在三个文件里。本单做替换，并明确划出「不是枚举值」的字面量。

## Goals / Non-Goals

**Goals:**

- 设备域的状态 / 连接类型 / 锁状态 / 锁释放原因一律取 `models.constants` 的枚举成员
- 让 `LockStatus` / `LockReleaseReason` 从「零消费」变为真实 SSOT

**Non-Goals:**

- 不改 `models.py` 的字段默认值与约束条件（保 `makemigrations --check` 绿）
- 不为 `purge` / `offline` 扩 `LockReleaseReason`（契约变更，另单裁决）
- 不改与状态同形的**非状态字面量**（响应键、URL 段、错误文本子串）

## Decisions

### 1. 逐行定点替换，不做全局 `replace_all`

- **选择**：按「文件 + 行号」白名单替换（脚本内固化 skip 名单）
- **理由**：`"released"` 既是 `LockStatus.RELEASED` 也是响应键 `{"released": True}`；`"timeout"` 既是 `LockReleaseReason.TIMEOUT` 也是响应键 `"timeout": <秒数>`。全局替换会把响应契约一起改掉，属静默行为变更

### 2. 转发面扩到四枚举，而不是让各文件直连 `models.constants`

- **选择**：`contracts.py` 补 `LockStatus` / `LockReleaseReason`
- **理由**：该文件已是设备域「数据契约」的唯一进口（`apps/device_pool/AGENTS.md`）；让 `api/views/manager` 都从它取，保证设备域枚举只有一个进口，且上层不必知道 SSOT 的物理位置

### 3. 不动 `models.py`

- **选择**：字段 `default` 与 `UniqueConstraint.condition` 保留字面量
- **理由**：这两处参与 `Field.deconstruct()` / 约束比较，是**唯一可能触发迁移**的地方；本单是可回滚的纯逻辑替换，不该夹带 schema 风险

### 4. 用「枚举写入 CharField 后读回取值」的测试兜底

- **选择**：新增 `test_device_enum_literals.py`，断言写入 / 过滤 / `update_fields` 三条路径读回的都是普通取值串
- **理由**：本次替换的正确性**完全依赖** `StrEnum` 的性质；把它显式钉住，比依赖「既有测试恰好覆盖到」更可靠（且能防止未来有人把基类改回 `(str, Enum)` 而无人察觉）

## Risks / Trade-offs

- [状态机行为漂移] → 替换只把字面量换成等值成员（`==` / hash / `str()` 实测一致）；`device_pool` 的单元与集成测（检测 / 状态机 / 序列化）为兜底，全量跑
- [漏掉一处致口径分叉] → 用「扫描 → 逐行白名单 → 复扫」三步，替换后复扫同 pattern，剩余命中必须全部落在 skip 名单里
- [误改响应契约] → skip 名单已在 proposal 逐条列表并给理由；diff 逐文件复核

## Migration Plan

1. `contracts.py` 扩转发面 → 三文件补 import → 逐行替换 62 处
2. 新增不变量测试；跑设备单测 / 集成测 + 全量
3. 复扫字面量，确认剩余命中 == skip 名单
4. 归档；回滚 = `git checkout` 四个文件 + 删测试
