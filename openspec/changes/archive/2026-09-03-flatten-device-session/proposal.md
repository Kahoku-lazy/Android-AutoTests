## Why

引擎（`get_device_engine`）只做「动作原语」，但上层要用它还得自己处理「惰性连接 / per-serial 锁 / 租用」，这些被塞进了 `session.py`，又寄生在 device_pool。其实「惰性连接 + 锁」是「用引擎的通用姿势」该归引擎；「租用」与已有的业务锁 `DeviceLock` 重复。应把操作编排下沉引擎、租用收敛到业务锁，**删掉 session 中间层**，让调用链从 `上层→pool→session→engine` 扁平为 `上层→engine`。

## What Changes

1. 引擎吞操作编排（engines/device）：
   - `get_device_engine(serial)` 改进程级缓存（serial → 单实例复用），设备断开时清理；
   - `U2Engine` 实例内部加锁（`self._lock`），操作原语串行；
   - `U2Engine.connect` 改幂等（已连跳过）。
2. 删 session 层：`session.py` 的惰性连接/锁已由引擎吞掉；租用收敛到 `DeviceLock`（acquire/release 已是业务占用）；操作原语上层直调引擎。
3. pool 收敛：删除 `pool.py` 操作部分（info/screenshot/dump_hierarchy/app_current/action_*），只留状态管理（switch_to/current_serial/连接类型/remove_device）。
4. 上层直调引擎：检查器/AI 工具/执行器/单步调试改经 `get_device_engine(serial)` 拿引擎直调动作，业务租用经 `DeviceLock`。

## 决策点

| # | 决策 | 推荐 |
|---|------|------|
| D1 | 引擎缓存粒度 | serial → 单实例（进程内），`release_device_engine(serial)` 清理 |
| D2 | 锁的位置 | 不加引擎锁（业务锁 DeviceLock 已保证同设备互斥） |
| D3 | connect 幂等 | U2Engine 加 `_connected` 标志 |
| D4 | 租用收敛 | 删 session lease，用 `DeviceLock`（acquire/release）管占用 |

## Non-Goals

- 不新建设备交互层、不引入新抽象。
- 不改操作语义（点击/滑动/截图行为等价）。
- 不做真机验收（按约定跳过）。

## Impact

- 引擎：`engines/device/registry.py`（缓存）、`engines/device/android/u2.py`（实例锁 + connect 幂等）
- 删除：`device_pool/session.py`、`pool.py` 操作部分
- 改调用链：`ai_assistant/tools.py`、`device_inspector/{service,api}.py`、`test_runner/executors/ui/connect.py`、`test_runner/views/task_views.py`
