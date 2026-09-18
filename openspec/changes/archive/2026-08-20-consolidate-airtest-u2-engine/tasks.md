## 1. AirtestU2Engine 实现（engines/android/airtest_u2.py）

- [x] 1.1 连接簇：`_adb_connect`（无线关键词判定/超时）、`_connect_u2`、`_tune_u2_http_timeout`（U2_OP_TIMEOUT=20）、`_verify_display`（ATX 消息映射）、`connect(serial, addr)` 全流程；失败抛 `EngineConnectError`；验证 `python -m ruff check engines/android/airtest_u2.py`
- [x] 1.2 感知簇：`screenshot()->bytes`（BGR→JPEG）、`screenshot_b64`、`screenshot_file`、`dump_hierarchy()->list[Node]`（3 层 fallback + parse_hierarchy_xml + Node 构造）、`app_current`；验证 ruff
- [x] 1.3 操作簇：click/long_click/swipe/input_text/press_key/shell/start_app/stop_app（Airtest）；验证 ruff
- [x] 1.4 XPath 与生命周期：exists/get_text/wait_toast（u2）、disconnect/is_alive/reconnect、`probe_u2`/`fetch_device_info` 静态方法、capabilities 声明；验证 ruff + `python -c "from engines.android.airtest_u2 import AirtestU2Engine"`

## 2. 执行链路 4 处收敛

- [x] 2.1 `executors/ui/connect.py`：删 u2/Airtest import 与 4 个迁移函数；`check_and_connect` 改经引擎构建 DeviceConnection（airtest/u2/info 取自引擎）；验证 `python manage.py check && ruff check apps/test_runner/executors/ui/connect.py`
- [x] 2.2 `executors/ui/recovery.py`：删 u2/Airtest import；`reconnect_u2/reconnect_device/wait_and_reconnect*` 改经引擎（签名不变）；验证 ruff
- [x] 2.3 `device_pool/views.py`：删 u2 import；连接验证改 `AirtestU2Engine.probe_u2`（EngineConnectError→502/504 映射不变）；验证 ruff + `python manage.py check`
- [x] 2.4 `device_pool/service.py`：`collect_device_info` 改经 `AirtestU2Engine.fetch_device_info`；删 u2 import；验证 ruff

## 3. 基线断言显式更新 + 契约测试

- [x] 3.1 重写 `tests/test_runner/test_connect_baseline.py`：关键词判定/超时/失败断言迁至引擎 `_adb_connect`/`connect`；`DEVICE_CHECK_TIMEOUT` 锚定留 connect.py；`U2_OP_TIMEOUT` 锚定迁引擎；验证 `python -m pytest tests/test_runner/test_connect_baseline.py --nomigrations -q`
- [x] 3.2 更新 `tests/test_runner/test_recovery_baseline.py`：reconnect 三测试迁引擎（检测/存活探测断言不变）；验证 pytest 该文件
- [x] 3.3 新增 `tests/engines/test_airtest_u2_contract.py`：全 mock 契约测试（连接流/感知格式/dump→Node/操作转发/XPath 冒烟/reconnect/probe/collect）；验证 `python -m pytest tests/engines -m unit -q`

## 4. 全量门禁与文档同步

- [x] 4.1 全量门禁：`python manage.py check`（0 issues）+ ruff（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**288 passed**，270 基线 + 18 契约/注册测试）
- [x] 4.2 接触点红线（本变更口径）：`grep -rn "import uiautomator2\|from airtest" apps/` 仅剩 `apps/device_pool/pool.py`（Step 4 收敛，已登记）；`python tools/gen_arch_stats.py --check-boundaries`
- [x] 4.3 Checklist §五 P1 引擎实现行标记完成并登记口径调整；L1c 详档 §五/§八 标注"已落地"；L0 详档接触点矩阵更新
