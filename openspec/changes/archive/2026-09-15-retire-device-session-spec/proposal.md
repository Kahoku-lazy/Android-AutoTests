## Why

🟡 **D5 契约面残留：`openspec/specs/device-session/spec.md` 描述的是一个**已删除**的协议**（spec 是「行为契约」，此处是假契约）。

事实链（全部有出处）：

1. 2026-08-20 变更 `introduce-device-session` 落地 `DeviceSession.lease()`、`LeaseMode`、`LeaseConflict`、per-serial 锁与 `DEVICE_SESSION_ENABLED` 开关，并把它写成 `device-session` spec 的 4 条需求。
2. 2026-09-03 归档变更 `flatten-device-session` **删除该层**：`apps/device_pool/session.py` 已不存在；「租用」收敛为 `DeviceLock` 业务锁（`device_pool/api.py` 的 `acquire_device` / `release_device` 操作 `dp_device_locks`），上层改直调引擎工厂 `open_engine` / `close_engine`（引擎无状态、短连接）。
3. `ARCH-00-平台总体架构.md` 已按此改写正文，但在两处把 spec 的处置挂起为「另案」：
   - 行 36：「`openspec/specs/device-session/spec.md`（对应协议已于 2026-09-03 扁平化，**spec 退役另案**）」
   - 行 532（目录树）：「`└── device-session/spec.md ← 协议已扁平化（2026-09-03），spec 退役另案`」

**本单就是那个「另案」。** 实测全仓已无任何代码消费该协议（`grep DeviceSession|LeaseConflict|LeaseMode|LeaseError|DEVICE_SESSION_ENABLED` 在 `apps/` `engines/` `tests/` 零命中），而 spec 仍在断言「lease SHALL 抛 LeaseConflict」等不可能发生的行为 —— 任何人按此 spec 写测试或写代码都会得到错误结论。

## What Changes

- **退役 spec**：新增 `specs/device-session/spec.md` delta，用 `## REMOVED Requirements` 逐条移除现有 4 条需求（`租用互斥` / `EXCLUSIVE 业务锁前置` / `per-serial 并发隔离` / `错误语义转换`），每条附 **Reason** 与 **Migration**；归档时由 OpenSpec 应用到主 spec
- **同步架构文档**：`ARCH-00-平台总体架构.md` 行 36 与行 532 的「spec 退役另案」改为「已于 2026-09-15 退役」
- **清理陈旧 docstring**（两处仍在用已删除的层名解释现状）：
  - `engines/device/base.py`：上层经 `DeviceSession`（L2）消费本协议 → 改为经引擎工厂 `open_engine` / `close_engine` 消费
  - `engines/device/registry.py`：引擎名由调用方（未来 `DeviceSession`）→ 去掉对已删除层的指向

- **BREAKING**：无（纯契约 / 文档 / 注释；零代码行为变化）
- **不设 `skip_specs`** —— 本单正是 spec 层的变更

## 关联文档

- 契约真相源：`ARCH-00-平台总体架构.md` 行 36 / 53 / 369 / 504 / 532 / v3.3 变更行
- 前置归档变更：`flatten-device-session`（2026-09-03，删除该层）· `introduce-device-session`（2026-08-20，引入该层）
- 相关现行 spec：`openspec/specs/engine-protocol/spec.md`（引擎协议，仍在用）
- 门禁：`django-backend-check/references/calibration.md` §2（契约错误）· §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-session`：**移除全部 4 条需求**（能力已随 `flatten-device-session` 消失，无替代 spec —— 引擎协议由 `engine-protocol` 承担，「租用」语义由 `ARCH-00` §4.4 的 `DeviceLock` 业务锁承担）

## Impact

- 契约：`openspec/specs/device-session/spec.md`（归档后 4 条需求被移除）
- 文档：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（2 处）
- 注释：`engines/device/base.py` · `engines/device/registry.py`
- 验证：`openspec validate --strict`（change 与 spec）· `manage.py check` · `ruff` · 全量单测（确保零行为变化）· `--check-boundaries`
- 不在本单范围：不新增「设备租用」能力的 spec（是否需要把 `DeviceLock` 租用写成正式 spec 属独立裁决；现状由 `ARCH-00` §4.4 承担）
