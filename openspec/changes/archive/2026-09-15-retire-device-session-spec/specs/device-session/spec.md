## REMOVED Requirements

### Requirement: 租用互斥

**Reason**: 该需求描述的 `DeviceSession.lease()` 协议已于 2026-09-03 归档变更 `flatten-device-session` 中整体删除（`apps/device_pool/session.py` 已不存在）；全仓零代码消费，需求成为假契约。

**Migration**: 设备互斥改由业务锁承担 —— 跨模块经 `apps/device_pool/api.py` 白名单的 `acquire_device(serial, user_id, timeout)` 建立 `dp_device_locks` 的 `lock_type=process` 记录（兜底 TTL 30 分钟由心跳回收），`release_device(serial, reason)` 释放。见 `ARCH-00-平台总体架构.md` §4.4。

### Requirement: EXCLUSIVE 业务锁前置

**Reason**: `LeaseMode.EXCLUSIVE` 与 `LeaseConflict` 随 `flatten-device-session` 删除，无对应实现。

**Migration**: 「先持锁再操作」的语义保留在调用方：需要独占设备的流程先调 `acquire_device`，失败即返回业务错误；不再有协议层的 EXCLUSIVE 模式开关。

### Requirement: per-serial 并发隔离

**Reason**: 协议层的 per-serial 锁随会话层一起删除；「把惰性连接与 per-serial 锁塞进引擎」的诉求在 `flatten-device-session` 中被明确否决（引擎保持无状态、短连接）。

**Migration**: 引擎按 `open_engine(serial, addr)` 每次新建并连接、调用方用完 `close_engine(engine)` 断开；同设备互斥由 `DeviceLock` 业务锁保证，不再由协议层串行化。

### Requirement: 错误语义转换

**Reason**: 该需求约束的是已删除的会话层（把引擎异常转成 `LeaseError`）；现行链路上不存在 `LeaseError` 类型。

**Migration**: 引擎层失败抛 `EngineConnectError`（`engines/device/base.py`），由 `apps/device_pool` 的 `DeviceDetector.connect` 转成业务错误 `DeviceError`（携带 HTTP 语义与用户文案）。引擎协议本身见 `openspec/specs/engine-protocol/spec.md`。
