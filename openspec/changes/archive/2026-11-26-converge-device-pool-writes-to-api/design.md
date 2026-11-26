# Design: converge-device-pool-writes-to-api

## Context

动机见 proposal.md。写路径现状（审计实测）：views.py 直调 registry.register_device / touch_last_seen / set_connection_state / collect_device_info / delete_device_record 与 state_machine.claim_wireless_device / occupy_observe / release_observe / set_device_lock / release_occupy / update_device_status / heartbeat_sync。api.py 白名单 6 函数零调用。约束：响应形状与权限语义逐一不变；跨 App 消费方（task_list.engine_adapter 已死、dashboard 只读 Model）不受影响。

## Goals / Non-Goals

**Goals**
- View 只分发；device_pool 全部写操作经 api.py；死白名单清除；架构断言防回潮。

**Non-Goals**
- 不改 current 指针语义与 GET 副作用（产品口径另行裁决）；不退役 observe 链；不动 registry/state_machine/manager 内部实现逻辑。

## Decisions

### D1 api 写原语按端点语义命名，一函数一职责
每个写原语对应一个端点的完整写事务（如 `connect_device(serial, user_id, connection_type, address)` 内部顺序执行 set_connection_state → collect_device_info → occupy_observe），View 不再编排多步写。理由：编排留在 View 就是现状违规的根源；api 函数承载「一个操作」的完整语义，Tool 未来可复用同一 api。备选：细粒度原语逐个导出由 View 组合——等于把违规合法化，弃。

### D2 读路径同步收口但保留 GET 副作用现状
`sync_device_status` / `heartbeat_sync` 经 api 导出供 GET 端点调用；列表自动切 current 指针的行为原样保留在 api 内部（注释标注「多用户竞争，待产品裁决」），不在本变更改语义。

### D3 架构断言防回潮
tests/arch/unit 增用例：AST 扫描 device_pool/views.py，断言不 import registry/state_machine/manager（只允许 api/models/pool/contracts）。与变更③的门禁规则互补（③管跨 App，本断言管 app 内分层）。

### D4 时序：①②先合并
lock_device 身份修复（①）与 manager 死函数删除（②）先行，本变更基于其后工作树重写，避免三方同文件冲突。

## Risks / Trade-offs

- [重写面大，行为漂移风险] → 以 tests/device/api 全量 + 逐端点响应对拍（改前改后同请求同响应）为验收；每个端点独立提交便于回退定位。
- [api 函数粒度变粗，单测要造更多前置] → 集成用例直调内部件的既有测试保留，api 层补编排顺序断言。

## Migration Plan

纯重构，无迁移。回退 = 还原提交。部署无感知（契约不变）。

## Open Questions

无。current 指针产品口径已明确划出（Non-Goals），不影响本设计。