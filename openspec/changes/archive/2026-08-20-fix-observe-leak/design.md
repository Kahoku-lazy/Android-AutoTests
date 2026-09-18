## Context

`occupy_observe`（service.py:473）注释明示"轻量，不创建锁"；`DeviceLock.is_expired`（models.py:102）与 `release_internal`（service.py:200）已有成熟机制，仅 observe 路径未接入。前端 `disconnectDebugDevice` 存在但无生命周期钩子调用。

## Goals / Non-Goals

**Goals:**

- 关页/路由离开 → 设备即刻释放（前端钩子）
- 崩溃/无钩子场景 → 30 分钟超时自动回收（后端兜底）

**Non-Goals:**

- 不改执行引擎占用的锁语义（release_observe 前缀保护保持）

## Decisions

- `OBSERVE_LOCK_TTL = 1800` 模块级常量（后续可提 settings）；锁类型 `"observe"` 与 process/user 并列
- 回收点选 `heartbeat_sync`（既有 30s 心跳周期，前端设备页轮询触发；无需新调度器）
- 前端钩子 `onUnmounted`（SPA 路由切换即触发；无刷新场景由后端兜底）

## 模块防火墙自检

- 后端本 App 内修改；前端 composable 内修改（API 走既有 api 通道）；通过

## Risks / Trade-offs

- [TTL 过短打断长调试会话] → 30min 宽上限；续期策略另行评估（当前调试为短会话）
- [心跳回收误伤正在观察的设备] → 仅回收 is_expired（超时）锁；正常会话心跳刷新 last_heartbeat 不影响 TTL（TTL 基于 locked_at）——**注意**：当前观察会话不续锁，超过 30min 仍会回收。登记为已知边界，单次调试超过 30min 需重连
