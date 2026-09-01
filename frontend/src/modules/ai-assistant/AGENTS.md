# ai-assistant 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant/agents`（`index.vue`）；`viewMode` 由路由驱动（`agents` / `toolbox` / `knowledge` / `evaluator`），四子项共用 `index.vue`。
- `agents` 视图 = 纵向两个区块：
  1. **小助手看板** `.duty-section` → `AgentRouteCard` × 2（控制设备 / 平台任务），展示图标 + 线路名 + 规划 / 执行 / 校验模型 + 超管「配置」入口。
  2. **任务卡片列表** `TaskBoard` → 「新建任务」`el-dialog`（7 字段）+ `.task-card-grid` 卡片列表（六态徽标）。
- 卡片网格 `repeat(auto-fill, minmax(280px, 1fr))`，间距 16px。

## 组件设计


## API 接口


## 快速验证清单

