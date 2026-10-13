## Why

验收模型调用截图工具时必然报错 `unexpected keyword argument 'user_id'`，导致验收拿不到截图、只能凭日志判定，页面类断言因此被误判为不通过（引擎级端到端跑测实测：两次截图调用全部失败）。

## What Changes

- 修掉验收角色的截图工具包装把 `user_id` 转发给不接受它的引擎自带截图实现的问题：仅在**被包装的实现声明了** `user_id` 时才转发。
- 补一条单测锁住该行为（引擎自带截图实现 + 平台实现两种签名各测一次）。

## 关联文档

- 关联需求编号：`PRD-08-AI助手`（智能体管理 · 设备操控）。
- 说明：纯缺陷修复，无需求级行为变化（按仓库惯例置 `skip_specs: true`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无：本单只修实现缺陷，对外行为与既有规格一致）

## Impact

- **引擎**：`engines/ai/agents/verifier.py`（截图工具包装的转发条件）。
- **测试**：新增单测覆盖两种被包装实现的签名。
- **平台与前端**：无影响。
