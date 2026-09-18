## Context

真实流时序：`dp_acquire_device`（建 process 锁，execution.py:243/423）→ `check_and_connect_async`（execution.py:323/499）→ `_execute_tests` finally → `_cleanup_device`。EXCLUSIVE 前置校验与释放点均已天然存在，开关只需在 connect 与 cleanup 两点接线。

## Goals / Non-Goals

**Goals:**

- 开关 True：执行链路经 EXCLUSIVE 会话（业务锁前置 + 会话释放）
- 开关 False（默认）：行为与现状完全一致

**Non-Goals:**

- 不删旧路径（真机验证开关后另立变更）
- 不改 TRANSIENT 链路（设备管理/检查器已走协议）

## Decisions

- **前置校验落 session.lease**：EXCLUSIVE 时查 `DeviceLock(lock_type="process", status="active", device__serial=serial)`，无则 LeaseConflict——锁语义唯一来源仍是 device_pool（session 只读校验）
- **会话登记**：`connect._sessions[serial] = session`（进程内）；`_cleanup_device` 释放顺序 = 先 release_session 再 dp_release_device（会话先于业务锁，符合总纲 §2.3.3）
- **settings 读取**：`os.environ.get("DEVICE_SESSION_ENABLED","False").lower() in ("1","true","yes")`

## 模块防火墙自检

- session 读 DeviceLock 属本 App（device_pool）内部；test_runner import 协议属过渡期已登记通道；通过

## Risks / Trade-offs

- [开关 True 的会话释放遗漏导致设备卡 BUSY] → 释放挂唯一 cleanup 点 + release_session no-op 幂等
- [前置校验误拒] → 真实流先 acquire 后 connect（时序已核）；单测覆盖有锁通过
