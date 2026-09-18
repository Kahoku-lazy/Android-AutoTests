## Context

L2 详档 §2.3/§四/§五 已定契约：租用互斥、per-serial 锁、业务锁先于物理会话、四类错误语义。3b 已落地引擎并收敛 4 处接触点；本变更关闭最后 1 处（pool.py）并落地协议。executor 经 DeviceConnection/DeviceAdapter 的执行链路在 Step 5 与权威 state 一起会话化（登记）。

## Goals / Non-Goals

**Goals:**

- DeviceSession 协议落地且单测覆盖（mock 引擎）
- pool.py 收敛：u2/Airtest import 清零 → 红线"仅 engines/ 一处"完全达标
- executor 两处 adapter 旁路消除
- 行为等价：设备管理/检查器链路（inspector 快照、设备连接、单步调试）零变化

**Non-Goals:**

- executor 执行链路不切 lease(EXCLUSIVE)（Step 5 与权威 state 联动，登记）
- 不做 settings.DEVICE_ENGINE 接线（Step 5；当前工厂默认 airtest_u2）
- 不做业务锁联动校验（acquire_device → lease 的强制关系，Step 5）
- 不做 Node→dict 之外的任何数据契约变更

## Decisions

- **租用模型**：pool 持 TRANSIENT 会话（设备管理/检查器链路）；EXCLUSIVE 语义已定义、执行链路 Step 5 接入。同 serial 同刻至多一个持有者（进程内 `_lease_holders`），冲突抛 `LeaseConflict`
- **惰性连接**：`lease()` 只登记，首次操作才 `engine.connect(serial, addr)`（保持 pool 现有惰性语义；`_ensure_connected` 幂等）
- **per-serial 锁**：`DeviceSession._locks[serial]` 进程级 dict + 守护锁；session 的感知/操作全部经该锁串行（跨 serial 并行）
- **错误转换**：引擎 `EngineConnectError` → `LeaseError`（带原因）；`RuntimeError`（dump 失败等）原样传播
- **pool 兼容面**：`u2d/ad/d` 属性返回会话引擎原始句柄（`task_views.py:85-86` 单步调试依赖）；`dump_hierarchy` 返回 dict 列表（`dataclasses.asdict` 转换，inspector 契约不变）
- **adapter 薄方法**：`app_start(pkg)`/`screenshot()` 直接转发 `self.d`，消灭 executor 对原始句柄的越层访问

## 模块防火墙自检

- pool.py 收敛后无第三方引擎 import；pool import 本 App session + engines.registry（跨层调引擎工厂——过渡期登记：Step 5 后消费方统一经 api/协议）
- session.py 在 device_pool App 内（协议层宿主），无跨 App 依赖
- 无 ORM 写变化；前端零改动
- 通过（1 处过渡期登记）

## Risks / Trade-offs

- [pool 基线的 19 个测试需重写 mock 目标] → 新 mock 经引擎类注入，断言语义不变（同一行为、不同注入点）
- [惰性连接与租用登记的时序差] → `_ensure_connected` 幂等 + 单测覆盖"未连接即操作"路径
- [同 serial 并发（inspector+管理页）语义变化] → 原全局锁串行所有设备，现 per-serial 并行——单测覆盖跨 serial 并行、同 serial 串行
- [executor 仍走 DeviceConnection 而非 session] → 登记 Step 5；adapter 薄方法已消除 executor 对原始句柄的越层访问
