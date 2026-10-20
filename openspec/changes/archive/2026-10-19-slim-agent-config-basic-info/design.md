## Context

「配置」入口来自卡片底栏，落到 `/ai-assistant/agent/:id`。卡片与任务列表的显示名/头像优先取 `route_configs.device_control.name/avatar`（`assistant-cards.ts` 与后端 `resolve_assistant_name` 同口径），因此配置页收缩后仍必须能改这两个值。执行链（`engine_adapter.sop_role_models`）只读 `route_configs` 的三角色模型，配置页不再展示它们。

## Goals / Non-Goals

**Goals:**

- 配置页只剩一个「基本信息」区块，字段为名称 / 头像 / 标签 / 描述 + 只读职责（UI自动化）/ 工作流（ui_auto_workflow）。
- 后端入参同步收缩，杜绝「表单没有、接口能改」的暗门。
- 改名/换头像后，卡片与任务列表立即同步。

**Non-Goals:**

- 不删除 `route_configs` 与模型字段（执行链依赖）。
- 不改卡片上的「校验」入口与健康探测。
- 不新增「职责/工作流」的数据库字段（当前写死）。

## Decisions

**D1 名称/头像仍写入 `route_configs.device_control`，由后端镜像。**
前端只提交基本信息四字段；`update_agent` 把 name/avatar 追加写进 `route_configs.device_control`，保留 planner/executor/verifier 与 health。备选：前端回传整份 route_configs——会把模型配置暴露在表单载荷里，且加密脱敏链路更易出错，否决。

**D2 入参收缩为四个字段，不再接受 status / 模型 / 线路 / max_loops。**
`AgentInputSerializer` 只留 name/avatar/tags/description；`update_agent` 只应用这四个键。status 改由后台维护。备选：保留旧字段但忽略——会留下「能提交但不生效」的假接口，否决。

**D3 详情输出不变。**
`AgentDetailSerializer` 继续返回 `route_configs`（脱敏）与模型字段：卡片列表、任务列表与其他读方仍依赖；配置页只是不再渲染/提交它们。

**D4 职责/工作流是前端展示常量，不落库。**
`constants.ts` 增加 `ASSISTANT_DUTY = "UI自动化"`、`ASSISTANT_WORKFLOW = "ui_auto_workflow"`，配置页以只读输入展示。备选：写进 DB——产品明确「当前写死」，不引入迁移。

**D5 删除 `encrypt_route_configs` 及其辅助函数。**
线路入参取消后它没有调用方；`decrypt_route_configs` / `mask_route_configs` 仍服务详情输出，保留。

## 模块防火墙自检

- 跨 App import：无新增；只改本 App。
- 写库收敛：`create_agent` / `update_agent` 仍在 `api.py`。
- 前端不直连数据库：仍走 `djangoClient`。
- 数据：无迁移，`ai_agents` 表结构不变。

## Risks / Trade-offs

- [镜像写入覆盖模型配置] → 读-改-写 `route_configs`，只改两个键；单测/手工验证模型键仍在。
- [老数据 route name 为空] → 前端载入时按 `route.name || agent.name` 回退，保存后补齐。
- [模型配置此后只能后台改] → 产品口径如此；执行链不受影响。
- [表单收缩后新建设智能体没有模型] → 目前没有「新建」入口；如将来恢复，需要单独设计模型初始化。

## Migration Plan

无数据迁移。回滚 = 还原 `AgentDetail.vue` / `AgentBasicInfo.vue` / `serializers.py` / `api.py`。
