# ai-assistant 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant/agents`（`index.vue`）；`viewMode` 由路由驱动（`agents` / `toolbox` / `knowledge` / `evaluator`），四子项共用 `index.vue`。
- `agents` 视图 = 纵向两个区块：
  1. **小助手看板** `.duty-section` → `AgentRouteCard` × 2：每条线路独立 `route_configs.{route}.name/avatar`；头像旁连通徽标（✅已连通 / ❌已断开 / 🔍未检测）；校验结果写入 `route_configs.{route}.health`（手动立即落库；`GET /ai/agents/health` 每 30 分钟复检过期线路）。三模型行未校验显示「🔍未检测」。
  2. **任务卡片列表** `TaskBoard` → `FilterTabs`（全部任务 / 平台任务 / 控制设备，前端按 `route` 过滤）+ 「新建任务」`el-dialog`（7 字段）+ `.task-card-grid` 卡片列表：标题 / 线路种类徽章（🧭平台任务 / 📱控制设备）/ 六态徽标 / 目标 / 设备·时间 / 结果摘要；徽标色：待执行灰、执行中蓝、成功绿、失败红、取消灰、暂停黄。无操作按键。
- 卡片网格 `repeat(auto-fill, minmax(300px, 1fr))`，间距 16px。

## 组件设计


## API 接口


## 快速验证清单

