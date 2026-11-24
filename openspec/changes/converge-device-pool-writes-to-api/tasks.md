# Tasks: converge-device-pool-writes-to-api

## 1. api 写原语重建

- [ ] 1.1 前置检查：fix-task-runtime-p0-defects 与 retire-backend-dead-code 已合并。api.py 按 D1 增写原语：activate_device / scan_and_register / connect_device / disconnect_device / release_observe / set_device_lock / release_occupy / sync_device_status / heartbeat_sync，内部委托 registry/state_machine，docstring 按模板（Args/Returns/Raises）。验证：新增 integration 用例逐原语断言写效果与改前 View 路径一致；`python -m pytest -c tests/pytest.ini tests/device -q` 通过
- [ ] 1.2 删死白名单 6 函数（list_devices/ensure_device/acquire_device/release_device/release_device_locks_for_device/use_device）与 __all__ 同步；`device` 移出 __all__（pool.py 本体保留）；api.py 模块 docstring 改「内部实现为 manager/registry/state_machine」。验证：grep 六名零生产调用，`python run.py check` 通过

## 2. View 退回分发

- [ ] 2.1 views.py 逐端点改调 api 写原语（activate/scan/connect/disconnect/disconnect-observe/lock/release/heartbeat/list 的状态同步），删除对 registry/state_machine 的直接 import 与调用；响应形状逐一不变。验证：`python -m pytest -c tests/pytest.ini tests/device -q` 全量通过；改前改后同请求响应对拍（至少 lock/connect/scan 三端点手工或脚本核对）
- [ ] 2.2 manager.py:9-10 分工 docstring 对齐 pool.py 现状。验证：ruff check 通过，docstring 与代码一致

## 3. 架构断言

- [ ] 3.1 tests/arch/unit 增「device_pool/views.py 不 import registry/state_machine/manager」AST 断言。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过；故意在临时分支加违规 import 能被抓出（负向自测后还原）

## 4. 关单门禁

- [ ] 4.1 `python run.py check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 零违规；ruff check/format --check device_pool 通过；逐文件暂存、refactor(device_pool) 提交，推特性分支提 PR，确认 python 与 frontend 两个 CI job 全绿后合并