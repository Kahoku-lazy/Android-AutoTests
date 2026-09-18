## Context

session 的「操作编排」（惰性连接/锁）和「租用」分别可下沉引擎、收敛业务锁，故可删掉整层，调用链扁平化。

## Goals / Non-Goals

- Goals：引擎自带动作+操作编排，上层直调引擎+业务锁管租用，删 session 与 pool 操作部分。
- Non-Goals：不动操作语义、不建新层、不做真机验收。

## Decisions

1. 引擎保持无状态：每次 new + connect + 操作 + disconnect，不做缓存/锁/幂等。
2. 并发互斥由业务锁 DeviceLock（acquire/observe）保证，引擎只做动作。
3. 连接生命周期由上层自管：执行器/AI 运行前 connect、运行后 disconnect；设备管理用 adb 查询不连接。
4. 租用 = DeviceLock（acquire/release 已建 process 锁），删 session lease/EXCLUSIVE。

## Risks / Trade-offs

- [引擎从无状态工厂→有状态缓存] → 需管理生命周期：设备断开调 release_device_engine 清理，防连接残留。
- [租用语义等价] → EXCLUSIVE 前置校验移到 test_runner 调用方，行为不变。
- [跨 4 模块改调用链] → 分 5 阶段，每阶段 ruff+契约测试验证。

## Migration Plan

P1 引擎增强（低风险增量）→ P2 删 session → P3 pool 收敛 → P4 上层直调 → P5 回归。
