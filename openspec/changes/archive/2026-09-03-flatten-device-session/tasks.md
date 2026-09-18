## 1. 引擎吞操作编排（全部回退：短连接+独占场景下缓存/锁/幂等均无用）

- [x] 1.1 registry 缓存（已回退：跨运行缓存无用，短连接每次 new+connect+disconnect）
- [x] 1.2 U2Engine 实例锁（已回退：业务锁 DeviceLock 已保证同设备互斥）
- [x] 1.3 connect 幂等（已回退：显式 connect/disconnect 无需幂等）

> 结论：引擎保持无状态，连接生命周期由上层（执行器/AI 运行前 connect、运行后 disconnect；设备管理用 adb 查询不连接）。
- 验证：ruff + 引擎层 import + 零 django 依赖保持

## 2. 删 session 层

- [x] 2.1 删除 session.py（pool 操作收敛后已删）
- [x] 2.2 执行器 connect.py 删 EXCLUSIVE 会话分支（DEVICE_SESSION_ENABLED 开关已删，统一走 get_device_engine + connect）
- 验证：ruff + grep connect.py 无 DeviceSession/LeaseMode 引用

## 3. pool 收敛

- [x] 3.1 删除 pool.py 操作部分（info/screenshot/dump_hierarchy/app_current/action_*）
- [x] 3.2 pool 只留 switch_to/current_serial/连接类型/remove_device
- 验证：ruff + 状态管理接口不变

## 4. 上层直调引擎

- [x] 4.1 检查器截图/层级/前台改经 open_engine（open_inspector_engine）
- [x] 4.2 AI 工具 device_action/list_apps 改经 open_engine + _resolve_device 占用校验
- [x] 4.3 单步调试（task_views）改经 open_engine
- 验证：ruff + 各契约不变

## 5. 回归验收

- [x] 5.1 manage.py check + ruff check engines apps
- [x] 5.2 pytest tests/graybox 29 passed
- [x] 5.3 --check-boundaries 零违规
