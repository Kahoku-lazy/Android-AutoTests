## Why

真机发现 #4（P2）：单步调试"连接设备"（observe 模式，`occupy_observe`）**不创建锁、无超时回收**，且前端 `useDebugDevice` 无卸载钩子——用户关闭编辑页/崩溃后设备永久 BUSY（本轮实测：浏览器关闭后 RF8N21MSW7A 仍 BUSY occupied_by=admin，排队任务卡死，需手动 release）。双重缺失：正常路径（关页）无钩子、异常路径（崩溃）无兜底。

## What Changes

- 后端 `apps/device_pool/service.py`：
  - `occupy_observe` 建 `DeviceLock(lock_type="observe", timeout_seconds=OBSERVE_LOCK_TTL)`（常量 1800s=30min，调试会话宽松上限）
  - `heartbeat_sync` 增过期回收：active observe 锁 `is_expired` → `release_observe(device)`（崩溃兜底；执行引擎占用经前缀保护不受影响）
- 前端 `useDebugDevice.ts`：`onUnmounted` 钩子——`debugConnected` 时 best-effort 调 `disconnectDebugDevice`（与 useEditLock 的 pagehide 模式一致）
- 新增后端单测 `tests/device_pool/test_observe_lock.py`

## 关联文档

- 真机验证发现 #4；基线：`2026-08-20-fix-real-device-findings`
- Bug 修复，无需求级行为变化：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- `apps/device_pool/service.py`、`frontend/src/modules/case-manager/composables/useDebugDevice.ts`、`tests/device_pool/test_observe_lock.py`
