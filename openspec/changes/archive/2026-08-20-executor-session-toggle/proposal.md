## Why

总纲 §四 差距 #4：执行链路（runner→DeviceConnection）直用引擎，未走 `DeviceSession.lease(EXCLUSIVE)`——目标架构唯一结构性缺口。执行链路是核心路径，按 Checklist 铁律"灰度不硬切"，以 **开关式接入**落地：默认旧路径零行为变化，真机验证后切开关、再删旧路径。

## What Changes

- `apps/device_pool/session.py`：EXCLUSIVE 租用**业务锁前置校验**——该 serial 须持有 active `process` 业务锁（`acquire_device` 已建），否则 `LeaseConflict`（落实"业务锁先于物理会话"）
- `apps/test_runner/executors/ui/connect.py`：`check_and_connect(serial, on_log, use_session=False)`——True 时经 `DeviceSession.lease(EXCLUSIVE)` 取引擎构建 DeviceConnection，会话登记进程内 `_sessions[serial]`；新增 `release_session(serial)`（无会话时 no-op）
- `apps/test_runner/views/execution.py`：两处 `check_and_connect_async` 调用传 `use_session=getattr(settings, "DEVICE_SESSION_ENABLED", False)`
- `apps/test_runner/views/executor.py::_cleanup_device`：加 `release_session(effective_serial)`（默认路径 no-op）
- `config/settings.py`：`DEVICE_SESSION_ENABLED`（env，默认 False）
- 单测：EXCLUSIVE 前置（无锁拒/有锁过）、use_session 注册与释放、settings 默认 False
- 真机：默认 False 路径由既有验证覆盖；True 路径登记"重启后端开开关后复验"

## 关联文档

- ARCH：`设计-L2-设备交互中台.md`（§2.3.2 lease 前置）、`设计-现状架构-重构落地实测.md`（差距 #1）
- 纯增量（默认路径零行为变化）：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- `apps/device_pool/session.py`、`apps/test_runner/executors/ui/connect.py`、`apps/test_runner/views/{execution,executor}.py`、`config/settings.py`、`tests/`
