# Proposal: converge-device-pool-writes-to-api

## Why

审计确认 device_pool 是平台「写库走 api.py」红线的最大破口：真实写路径为 View → registry/state_machine 直调（activate/scan/connect/disconnect/lock/release 等约 10 个端点），而 api.py 白名单 6 函数全仓零调用、形同虚设；api docstring 宣称的 service.py 不存在，app 级 AGENTS.md 为空。需求方已裁决：**写操作收敛进 api.py，manager/registry/state_machine 降为内部实现**。

## What Changes

- **api.py 重写为唯一写入口**：以活路径为准重建写原语——`activate_device`、`scan_and_register`（含无线认领）、`connect_device`（连接态+信息采集+observe 占用）、`disconnect_device`、`release_observe`、`set_device_lock`、`release_occupy`、`sync_device_status`、`heartbeat_sync`；内部委托 registry/state_machine/manager，View 不再直调内部件。
- **删除死白名单**：list_devices/ensure_device/acquire_device/release_device/release_device_locks_for_device/use_device 六个零调用函数与 `__all__` 同步；`device` 单例从 `__all__` 移除（作用域已缩至 app 内，pool.py 本体保留——列表 current 字段仍依赖）。
- **views.py 退回分发**：各端点只做参数提取、鉴权身份读取与调 api，响应形状与状态语义逐一保持不变（device-pool-table 规格「操作收进菜单不改变权限判定与请求语义」同口径）。
- **docstring 修正**：api.py「写逻辑下沉 service.py」改为 manager/registry/state_machine 内部实现；manager.py:9-10 分工描述对齐 pool.py 现状（仅当前设备指针）。
- **observe 链照原样收敛**（occupy/release/disconnect-observe）：虽属疑似死链（另行裁决退役），本变更只改道不改行为，便于日后在 api 层整链退役。
- 纯重构：无端点增删、无响应字段变化、无表结构变化。device_pool/AGENTS.md 的补齐（含写库层定性）属变更⑤文档批。

## 关联文档

无新增 PRD 需求编号——纯重构变更。问题来源为后端审计报告 R-2 / D-19 / D-24；需求方已裁决方案 a（收敛进 api.py）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——写路径改道不改变任何外部可观察行为；按 schema 约定设 `skip_specs: true`。）

## Impact

- **backend/apps/device_pool**：api.py（重写）、views.py（约 10 端点改分发）、manager.py（docstring）；registry/state_machine 本体不动。
- **tests**：tests/device/{unit,integration,api} 全量回归；直调 state_machine 的集成用例保留（内部件测试合法），新增「View 不直调内部件」的架构断言（可并入 tests/arch）。
- **协调**：①fix-task-runtime-p0-defects 先合并（lock_device 身份修复在先，本变更把修复后的形态搬进 api）；②retire-backend-dead-code 的 manager 死函数删除（3.1）先合并，避免同文件冲突。
- **明确排除**：GET 列表自动切换 current 指针的多用户竞争、_current_probe_cache 无上限（行为/产品口径问题，另行裁决）；observe 链退役（疑似项待确认）；devices/current 端点退役（疑似项）。