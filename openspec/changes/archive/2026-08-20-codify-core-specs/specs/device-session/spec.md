## Purpose
DeviceSession 租用式会话协议：统一 Android 设备交互的租用、感知、操作与生命周期入口，保证同设备互斥、多设备并行与业务锁前置。

## ADDED Requirements

### Requirement: 租用互斥
同一 serial 同一时刻 MUST 至多存在一个会话持有者；对已持有会话的 serial 再次 lease SHALL 抛出 LeaseConflict。

#### Scenario: 同设备二次租用被拒
- **WHEN** 对已持有会话的 serial 再次调用 lease
- **THEN** 抛出 LeaseConflict 且不产生第二个持有者

### Requirement: EXCLUSIVE 业务锁前置
EXCLUSIVE 模式租用前 MUST 已持有该设备的 process 业务锁（由 acquire_device 建立）；未持锁时 SHALL 抛出 LeaseConflict。

#### Scenario: 未持业务锁的 EXCLUSIVE 租用
- **WHEN** 该 serial 无 active process 锁时调用 lease(EXCLUSIVE)
- **THEN** 抛出 LeaseConflict（提示先 acquire_device）

### Requirement: per-serial 并发隔离
协议层操作 MUST 经 per-serial 锁串行化同设备操作；不同 serial 的操作 SHALL 互不阻塞。

#### Scenario: 双设备并行
- **WHEN** 两个不同 serial 的会话并发执行操作
- **THEN** 各自独立完成，无全局串行化

### Requirement: 错误语义转换
引擎连接失败 MUST 转换为 LeaseError（业务语义）；协议层不得向业务层泄漏引擎异常类型。

#### Scenario: 引擎连接失败
- **WHEN** 会话首次操作触发引擎连接且失败
- **THEN** 抛出 LeaseError（携带原因），由上层转 4xx 用户文案
