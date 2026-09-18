## 1. DeviceSession 协议落地（apps/device_pool/session.py）

- [x] 1.1 `LeaseMode`/`LeaseError`/`LeaseConflict`/per-serial 锁 + `DeviceSession` 类：`lease/release/_ensure_connected/感知/操作/查询` 委托引擎；验证 `python -m ruff check apps/device_pool/session.py`
- [x] 1.2 新增 `tests/device_pool/test_session.py`：租用互斥（同 serial 二次 lease 抛 LeaseConflict）、release 后可再租、惰性连接（lease 不 connect、首操作 connect）、per-serial 锁（同 serial 串行/跨 serial 并行）、EngineConnectError→LeaseError 转换；验证 `python -m pytest tests/device_pool/test_session.py -m unit -q`

## 2. pool.py 收敛 + executor 旁路消除

- [x] 2.1 `apps/device_pool/pool.py`：删 u2/Airtest import 与 `_op_lock`；`_sessions` 持有 DeviceSession（TRANSIENT）；`info/screenshot_b64/screenshot_file/dump_hierarchy(app_current/action_*` 委托会话（dump 转 dict）；`u2d/ad/d` 取会话句柄；`remove_device` 释放会话；验证 ruff + `python manage.py check`
- [x] 2.2 `executors/ui/adapter.py` 增 `app_start(pkg)`/`screenshot()` 薄方法；`executor.py:233/344` 改调；验证 ruff + `python manage.py check`

## 3. 基线断言显式更新（mock 注入点迁移）

- [x] 3.1 重写 `tests/device_pool/test_pool_baseline.py` 与 `tests/device_pool/test_screenshot_baseline.py`：mock 引擎类（注入 session 工厂），断言语义不变；验证 pytest 两文件
- [x] 3.2 重写 `tests/device_inspector/test_hierarchy_baseline.py`：经 pool 委托链 mock 引擎 dump；断言不变；验证 pytest 该文件

## 4. 全量门禁与文档同步

- [x] 4.1 全量门禁：`python manage.py check`（0 issues）+ ruff（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**300 passed**，288 基线 + 12 协议/委托测试）
- [x] 4.2 接触点红线（最终口径）：`grep -rn "import uiautomator2\|from airtest" apps/` **0 命中**（仅 engines/ 内）——3b 登记的 pool.py 收敛项正式关闭；`--check-boundaries` 零违规
- [x] 4.3 Checklist §五 P1 协议接入行标记完成（e2e/双设备专测注记为待真机环境执行）；L2 详档标注"协议已落地"；3b 登记的 pool 收敛项关闭
