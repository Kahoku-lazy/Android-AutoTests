## Why

平台只有一个「平台小助手」，模型与线路配置属于引擎执行期的装配数据，日常维护只需要基本信息。当前「配置」页却把模型、线路、循环次数、模型校验摊在同一张表单里，既容易误改执行链，也不符合产品口径。改为：配置页只留基本信息，并把「职责（UI自动化）」「工作流（ui_auto_workflow）」作为写死信息展示。

## What Changes

- **BREAKING（前端）** 配置页只保留「基本信息」区块：名称 / 头像 / 标签 / 描述 + 只读的职责（UI自动化）、工作流（ui_auto_workflow）。
- 删除「循环次数」「控制设备 Device Control（规划/执行/校验模型）」「模型校验」三个区块，以及 `AgentRouteConfig` / `ModelConfigField` 两个组件。
- **BREAKING（后端）** `AgentInputSerializer` 收缩为基本信息入参（name / avatar / tags / description）；模型、线路、循环次数、状态不再接受更新。
- `update_agent` / `create_agent` 把名称与头像**镜像写入 `route_configs.device_control`**（只改 name/avatar，保留 planner/executor/verifier 与 health），保证卡片与任务列表的显示名同步。
- 删除不再有调用方的 `api.encrypt_route_configs` 及其辅助函数。
- 不动：智能体详情输出（卡片列表仍读 `route_configs`）、卡片上的「校验」入口、执行链装配。

## 关联文档

产品口头决策「配置页只保留基本信息 + 职责/工作流写死」，无 PRD 编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-agent-model-config`: 整个能力退役（配置页不再管理主推理/视觉/强模型，也不再有模型清单与多模态提醒）。
- `ai-agent-routes`: 移除「配置页多线路模型配置」需求；线路内 API Key 加密与脱敏仍保留。

## Impact

- 前端：`AgentDetail.vue`、`components/AgentBasicInfo.vue`、删除 `components/AgentRouteConfig.vue` 与 `components/ModelConfigField.vue`、`constants.ts` 增加两项固定文案。
- 后端：`serializers.py`（入参收缩）、`api.py`（create/update 镜像、删 `encrypt_route_configs`）、`__all__`。
- 数据：无迁移（`route_configs`、模型字段仍在 DB，只是不再经配置页修改）。
- 文档：模块 AGENTS 中「配置」入口描述同步。
