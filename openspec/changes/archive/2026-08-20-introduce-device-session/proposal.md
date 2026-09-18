## Why

L2 详档的核心——`DeviceSession` 租用式会话协议尚未落地：DevicePool 单例仍是"current_serial 指针 + 全局 `_op_lock`"模式，且是 u2/Airtest import 的最后一处残留（3b 登记项）；executor 仍有 `d.app_start/d.screenshot` 旁路。Step 4 落地协议层：租用互斥、per-serial 锁、引擎工厂消费、错误语义转换，并把 pool 收敛为协议的消费者——完成"引擎接触点仅 engines/ 一处"的最终红线。

## What Changes

- 新增 `apps/device_pool/session.py`：`DeviceSession` 协议（L2 详档 §2.3 权威实现）——
  - `lease(serial, mode, addr)`：TRANSIENT/EXCLUSIVE 租用互斥（同 serial 同刻至多一个持有者，冲突抛 `LeaseConflict`）；`release()` 归还
  - per-serial 操作锁（替代全局 `_op_lock`，跨 serial 并行）
  - 感知/操作/查询委托 `get_device_engine()`（airtest_u2）；连接惰性建立
  - 错误语义转换：`EngineConnectError` → `LeaseError`（业务语义）
- **`device_pool/pool.py` 收敛**：删除 u2/Airtest import；DevicePool 变协议消费者——`switch_to/_addr/remove_device/current_serial` 状态管理保留，`info/screenshot*/dump_hierarchy(→dict 兼容转换)/app_current/action_*` 委托 DeviceSession；`u2d/ad/d` 属性改取会话引擎原始句柄（单步调试兼容）；全局 `_op_lock` 移除
- **executor 旁路消除**：`executor.py:233/344` 的 `d.app_start/d.screenshot` 改经 adapter 薄方法（`adapter.app_start/pkg`、`adapter.screenshot()`），行为不变
- 基线断言显式更新：pool/hierarchy/screenshot 基线测试改 mock 引擎/会话（旧 `_u2_instances/_airtest_instances` 接口消失）
- 新增 `tests/device_pool/test_session.py`：租用互斥/释放/惰性连接/per-serial 锁/错误转换

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L2-设备交互中台.md`（§2.3 协议权威、§四 租用与并发、§五 错误语义）
- ARCH：`dev_docs/03-设计与架构/设计-目标架构-设备交互协议与引擎分层.md`（§2.3 L2、§三 防火墙）
- 基线：OpenSpec 已归档 `2026-08-20-consolidate-airtest-u2-engine`（本变更关闭其登记项）
- 无 PRD 变更（行为等价重构，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 行为等价重构（协议落地 + 收敛），无需求级行为变化：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 新增：`apps/device_pool/session.py`、`tests/device_pool/test_session.py`
- 修改：`apps/device_pool/pool.py`、`apps/test_runner/executors/ui/{executor,adapter}.py`、`tests/device_pool/test_{pool,screenshot}_baseline.py`、`tests/device_inspector/test_hierarchy_baseline.py`
- 前端/数据库零改动
