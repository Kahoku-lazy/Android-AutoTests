## Why

L4 还有两处已登记缺口：

1. **`report-generator` 的分页/表高常量三处各写各的**：实测 `constants.ts` 的 `PAGE_SIZE_OPTIONS = [10,50,100]` / `TABLE_HEADER_HEIGHT = 54` / `TABLE_ROW_HEIGHT = 50` **零消费**（死常量），`ReportDetail.vue:29-31` 另有本地 `[10,20,50,100]` / `45` / `41`，`index.vue:120` 用内联 `[10,50,100]`。模块 `AGENTS.md` 要求「常量经 `constants.ts`」，现状是唯一真相源缺失。
2. **最后一处「仅 `required`」**：`AgentBasicInfo.vue:22` 的名称项空值时由父组件 `AgentDetail.save():123-129` 取线路名或「平台小助手」兜底——即该字段**实际不是必填**，星号本身是误导。

## What Changes

- `report-generator/constants.ts`：`TABLE_HEADER_HEIGHT` 54→**45**、`TABLE_ROW_HEIGHT` 50→**41**（对齐唯一真实消费方 `ReportDetail` 的现值，零行为变化）；`PAGE_SIZE_OPTIONS` [10,50,100]→**[10,20,50,100]**（按裁决统一，列表页由此新增「20」档，属**可见变化**）
- `report-generator/ReportDetail.vue`：删除 3 个本地常量，改为从 `./constants` 导入
- `report-generator/index.vue`：分页选项由内联 `[10,50,100]` 改为导入的 `PAGE_SIZE_OPTIONS`（模板取用同一常量）
- `ai-assistant/components/AgentBasicInfo.vue`：移除名称项的 `required` 星号（该字段非必填，空值有默认兜底），零行为变化
- **BREAKING**：无。props / emits / 接口 / 路由不变；两处可见变化 = 列表页分页多「20」档、AgentBasicInfo 名称项星号消失

## 关联文档

- `openspec/specs/frontend-l4-data-surface/spec.md`：本变更修改「Single pagination implementation」与「Form validation uses Element Plus rules」两条需求
- `openspec/changes/archive/2026-09-15-add-l4-spec-and-l4-l5-quickref/`：两处缺口的登记出处
- `frontend/AGENTS.md` L4 速查 §⑥：两处缺口的登记处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端实现收敛，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Single pagination implementation」新增「分页选项集唯一（来自 `constants.ts`）」场景；「Form validation uses Element Plus rules」的债务场景改为**全仓归零**（原 `AgentBasicInfo` 例外实为非必填，已移除星号）

## Impact

- `frontend/src/modules/report-generator/constants.ts` · `ReportDetail.vue` · `index.vue` · `frontend/src/modules/ai-assistant/components/AgentBasicInfo.vue`
- `openspec/specs/frontend-l4-data-surface/spec.md`（归档时更新）· `frontend/AGENTS.md`（L4 速查 §⑥）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过改动文件；报告列表分页与 Agent 基本信息页的浏览器目视（本环境待补）
- 不影响：`device-pool` 的分页常量（其 `constants.ts` 本就是独立真相源）、后端接口、路由表
