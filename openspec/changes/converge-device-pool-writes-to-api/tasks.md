# Tasks: converge-device-pool-writes-to-api

## 1. api 写原语重建

- [x] 1.1 前置已裁决（2026-11-26，需求方确认）：`fix-task-runtime-p0-defects` 与 `retire-backend-dead-code` 已于 2026-11-23 取消（0 进度、零提交、`CANCELLED.md` 在 `openspec/cancelled/`），不再等待「已合并」；本单自行重建原语。api.py 按 D1 写原语：activate_device / scan_and_register / connect_device / disconnect_device / release_observe / set_device_lock / release_occupy / sync_device_status / heartbeat_sync，内部委托 registry/state_machine，docstring 按模板（Args/Returns/Raises）。验证：新增 integration 用例逐原语断言写效果与改前 View 路径一致；`python -m pytest -c tests/pytest.ini tests/device -q` 通过
- [x] 1.2 删死白名单 6 函数（list_devices/ensure_device/acquire_device/release_device/release_device_locks_for_device/use_device）与 __all__ 同步；`device` 移出 __all__（pool.py 本体保留）；api.py 模块 docstring 改「内部实现为 manager/registry/state_machine」。验证：grep 六名零生产调用，`python run.py check` 通过

## 2. View 退回分发

- [x] 2.1 views.py 逐端点改调 api 写原语（activate/scan/connect/disconnect/disconnect-observe/lock/release/heartbeat/list 的状态同步），删除对 registry/state_machine 的直接 import 与调用；响应形状逐一不变。验证：`python -m pytest -c tests/pytest.ini tests/device -q` 全量通过；改前改后同请求响应对拍（至少 lock/connect/scan 三端点手工或脚本核对）
- [ ] 2.2 **skipped（无 docstring 可改）** —— 2026-11-24 全仓去注释后 `manager.py` 已无模块 docstring，本条对象消失；改编为在 `.agents/docs/apps/device_pool/device_pool_write_boundaries.md` 登记分工口径（见 4.2）

## 3. 架构断言

- [x] 3.1 tests/arch/unit 增「device_pool/views.py 不 import registry/state_machine/manager」AST 断言（新增 `tests/arch/unit/test_device_pool_view_boundary.py`，3 条：模块存在性、只允许 api/models/pool/contracts、负向自测样例）。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过；故意在临时分支加违规 import 能被抓出（负向自测后还原）

## 4. 关单门禁

- [ ] 4.1 门禁部分已绿（2026-11-26：`run check` 阻塞项 30/30；`tests/device` 30 passed + 1 条既有顺序相关失败；`tests/arch/unit` 224 passed + 4 条既有失败；`spectacular --validate` exit 0；boundary 零违规）；**提交与 PR 未做**（工作区尚未建分支提交）。原任务：`python run.py check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 零违规；ruff check/format --check device_pool 通过；逐文件暂存、refactor(device_pool) 提交，推特性分支提 PR，确认 python 与 frontend 两个 CI job 全绿后合并

## 5. 落地记录（2026-11-26）

- [x] 5.1 实现：`api.py` 按端点重写为 14 个出口（10 写原语 + `list_devices` / `list_connectable_serials` / `sync_device_status` / `get_online_devices`），
  `views.py` 只 import `api` / `contracts` / `models` / `pool`；`DeviceError` 从 `manager.py` 移到 `contracts.py`（移动、非新增，`manager` 仍 re-export）。
- [x] 5.2 测试：新增 `tests/device/integration/test_device_write_api.py`（7 条，逐原语断言写效果与改前 View 路径一致）；
  新增 `tests/arch/unit/test_device_pool_view_boundary.py`（分层防回潮）。
- [x] 5.3 文档（范围外追加）：`.agents/docs/apps/device_pool/device_pool_write_boundaries.md` 的「写库边界」节按目标态重写，
  删掉「尚未收敛」的现状说明——原 `align-backend-docs-with-code` 7.2 要求合并后回改，该单已归档，故并入本单收口。
- [x] 5.4 门禁（结果见 4.1）：`run check` / `tests/device` / `tests/arch/unit` / `spectacular --validate` / boundary 结果与既有失败见下方 4.1 说明。
