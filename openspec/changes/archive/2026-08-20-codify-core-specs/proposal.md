## Why

七步重构全程 `skip_specs`，`openspec/specs/` 为空——DeviceSession 与 UiEngine 两大目标态契约只有设计文档、无正式规范。沉淀为 spec delta 后：新引擎/协议变更有了需求级判据，后续变更的 Modified Capabilities 有了基线。

## What Changes

- 新增能力规范（spec delta，写入本变更 `specs/` 后经 archive 合并进 `openspec/specs/`）：
  - `device-session`：租用互斥、EXCLUSIVE 业务锁前置、per-serial 并发隔离、错误语义转换
  - `engine-protocol`：操作原语契约、感知标准化（JPEG/Node）、能力声明探测、注册表 fail-fast、契约测试门槛

## 关联文档

- ARCH：`设计-L2-设备交互中台.md`、`设计-L1c-引擎层.md`（契约权威详版）
- 纯文档（spec 沉淀），不改变任何实现：本变更**不是** skip_specs，specs 即交付物

## Capabilities

### New Capabilities

- `device-session`: 设备交互租用式会话协议（租用/感知/操作/生命周期与错误语义）
- `engine-protocol`: Android 执行引擎统一契约与注册表（可替换引擎的规范判据）

### Modified Capabilities

（无）

## Impact

- 新增 `openspec/specs/device-session/spec.md`、`openspec/specs/engine-protocol/spec.md`（archive 后）
- 代码/前端/数据库零改动
