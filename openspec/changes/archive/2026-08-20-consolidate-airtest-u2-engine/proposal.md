## Why

Step 3a 已立契约（`UiEngine` Protocol + 注册表），但引擎实现仍散落：connect.py 的连接预检、recovery.py 的重连、views.py/service.py 的裸 u2 调用——换引擎无实现可换。Step 3b 落地 `AirtestU2Engine`（组合双栈：Airtest 操作 + u2 dump/XPath），并把执行链路 4 处接触点收敛到 engines/，让"引擎实现只有一处"成立。

## What Changes

- 新增 `engines/android/airtest_u2.py`：`AirtestU2Engine` 实现完整 `UiEngine` 协议——
  - 连接：无线 adb connect（关键词判定）/ Airtest+u2 双连 / u2 超时调优（U2_OP_TIMEOUT=20）/ display 验证（ATX 消息映射），失败抛 `EngineConnectError`（技术语义）
  - 感知：`screenshot()`→JPEG bytes、`screenshot_b64`/`screenshot_file`、`dump_hierarchy()`→`list[Node]`（3 层 fallback + algorithms.hierarchy 解析 + Node 构造）、`app_current`
  - 操作原语：click/long_click/swipe/input_text/press_key/shell/start_app/stop_app（Airtest）
  - XPath 能力：exists/get_text/wait_toast（u2，`capabilities(xpath_locate=True, toast_wait=True, ocr=False)`）
  - 生命周期：disconnect/is_alive/reconnect；静态辅助 `probe_u2(addr)`（连接验证）、`fetch_device_info(addr)`（元信息）
- **执行链路 4 处收敛**：
  - `executors/ui/connect.py`：删除 u2/Airtest import 与 `_adb_connect/_connect_u2/_tune_u2_http_timeout/_verify_display`（迁入引擎）；`check_and_connect` 改经引擎构建，`DeviceConnection` 兼容壳保留（`DEVICE_CHECK_TIMEOUT=45` 属执行编排，留 connect.py）
  - `executors/ui/recovery.py`：删除 u2/Airtest import；检测/存活探测保持；`reconnect_u2/reconnect_device/wait_and_reconnect*` 改经引擎（签名不变，runner 零改动）
  - `device_pool/views.py`：删除 u2 import；连接验证改 `AirtestU2Engine.probe_u2`（错误消息映射不变）
  - `device_pool/service.py`：`collect_device_info` 改经 `AirtestU2Engine.fetch_device_info`，删除 u2 import
- **不触碰**：`device_pool/pool.py`（DevicePool 单例在 Step 4 被 DeviceSession 替代时一并收敛，本变更只收敛执行链路）；`adapter.py`（无引擎 import）；executor.py 233/344 的 `d.app_start/d.screenshot` 旁路（Step 4 协议化时处理）
- 基线断言显式更新：test_connect_baseline（关键词/常量迁移到引擎契约测试）、test_recovery_baseline（重连测试迁引擎）
- 新增 `tests/engines/test_airtest_u2_contract.py`：引擎契约测试（全 mock，覆盖连接流/感知/操作/XPath/生命周期）

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L1c-引擎层.md`（§五 现引擎实现规格、§八 迁移映射、§六 契约测试规范）
- ARCH：`dev_docs/03-设计与架构/设计-L0-第三方与外部目标.md`（接触点收敛矩阵）
- 基线：OpenSpec 已归档 `2026-08-20-add-engine-protocol`（契约）、`2026-08-20-refactor-baseline-tests`
- 无 PRD 变更（纯实现收敛，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯实现收敛（行为等价，接口激活面不变）：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 新增：`engines/android/{__init__,airtest_u2}.py`、`tests/engines/test_airtest_u2_contract.py`
- 修改：`executors/ui/connect.py`、`executors/ui/recovery.py`、`device_pool/views.py`、`device_pool/service.py`、`tests/test_runner/test_{connect,recovery}_baseline.py`
- `pool.py` 登记为 Step 4 收敛（门禁说明见 design）；前端/数据库零改动
