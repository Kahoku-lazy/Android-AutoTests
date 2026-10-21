## Why

「平台运营」与「AI 用量」章节头右侧的两条 chip 摘要行（设备/智能体/任务/工作流、角色·累计/角色·今日）与下方 KPI 卡及角色数据重复，只增加视觉噪声。产品要求按截图标记删除这两条摘要行。

## What Changes

- 删除「平台运营」章节头的「设备 / 智能体 / 任务 / 工作流」chip 行。
- 删除「AI 用量」章节头的「角色·累计 / 角色·今日」chip 行。
- 同步移除仅供角色 chip 使用的 `roleBreakdown` 计算与失去唯一消费者的 chip 修饰样式。
- 「测试资产」章节头右侧的「用例 N」chip 保留不动。
- 不改统计接口、`by_role` 字段、KPI 卡与其它章节内容。

## 关联文档

- PRD-01 仪表盘

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-chapter-boards`: 章节头不再呈现 chip 摘要行（平台运营汇总 chip 与 AI 分角色 Token chip 均删除）

## Impact

- `frontend/src/modules/dashboard/index.vue`：删除两处 chip 行与 `roleBreakdown` 解构
- `frontend/src/modules/dashboard/DashboardView.logic.ts`：移除 `roleBreakdown`、`ROLE_LABELS`
- `frontend/src/modules/dashboard/DashboardView.style.css`：移除失去消费者的 chip 修饰类
- `frontend/tests/dashboard/`：按需调整/补充单测
- 后端聚合与 `GET /api/dashboard/stats/` 契约不变
