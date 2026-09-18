## Why

设备管理模块（device_pool）职责边界已定为「只管设备状态」（在线/离线/占用/谁在用/是否使用中）。探索发现模块内存在冗余：执行引擎占用前缀常量在 api.py / manager.py 各定义一份（另与 device_inspector、前端同口径散落），且 api.py 存在函数内 import。需做最小收敛，消除重复与不规范。

## What Changes

1. 执行引擎占用前缀收敛到单一常量 `RUNNER_OCCUPIED_PREFIXES`（contracts.py），api.py 的 `_EXECUTION_OCCUPY_PREFIXES` 与 manager.py 的 `_RUNNER_PREFIXES` 删除并改引用。
2. api.py `list_devices` 函数内 import 移到文件顶部。

## 关联文档

- 规则：`apps/device_pool/AGENTS.md`（职责边界 + 代码设计规范）
- 边界分析：设备管理代码 · 职责与边界分析报告（会话内产出）

## Non-Goals（grep 核实后排除，避免过度设计）

- 不删 pool.py 纯透传 action_*：唯一调用方 api.py 的 device_action/list_apps 属「设备操作」能力（AI 助手在用），删除需改其归属，属跨模块大动作。
- 不清理 pool.py d/engine 兼容属性：test_runner/views/task_views.py 仍在用 device.engine。
- 不清理 api.py 历史函数 ensure_device / get_online_devices / release_device_locks_for_device：均有跨 App 调用方（element_locator / ai_assistant / test_runner）。
- 不搬迁 pool/session 设备操作能力、不引入新抽象层。

## Impact

- `apps/device_pool/contracts.py`（新增统一常量）
- `apps/device_pool/manager.py`（改引用）
- `apps/device_pool/api.py`（改引用 + import 规范化）
