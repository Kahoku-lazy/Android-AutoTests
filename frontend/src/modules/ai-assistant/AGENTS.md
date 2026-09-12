# ai-assistant 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant/agents`（`index.vue`）；`viewMode` 由路由驱动（`agents` / `toolbox` / `knowledge` / `evaluator`），四子项共用 `index.vue`。
- `agents` 视图 = 纵向两个区块：
  1. **小助手看板** `.duty-section` → `AgentRouteCard` × 2：每条线路独立 `route_configs.{route}.name/avatar`；头像旁连通徽标（✅已连通 / ❌已断开 / 🔍未检测）；校验结果写入 `route_configs.{route}.health`（手动立即落库；`GET /ai/agents/health` 每 30 分钟复检过期线路）。三模型行未校验显示「🔍未检测」。
  2. **任务卡片列表** `TaskBoard` → `FilterTabs` + 「新建任务」+ 调试「清空」（`POST /ai/agent-tasks/clear`，确认后删全部）+ 按状态 `el-collapse` 分组 + 卡片（标题 / 线路 / 六态 / 目标 / 设备·时间 / 摘要 / 「详情」+「删除」）。「详情」跳转全屏页 `/ai-assistant/tasks/:taskId`（`TaskDetailPage`）：`GET /ai/agent-tasks/{id}`，左右分栏展示逐步执行（左步骤清单 / 右当前步操作·断言·重试记录），KPI 为步骤进度。运行中按步执行验收增量写入 `result`；详情页未终态时轮询。列表只下发短摘要。旧任务无过程日志时详情空态提示。
- `toolbox` 视图 = **装配台**（`ToolboxPanel`）：上区「助手此刻可用」生效芯片（总闸 AND 目录启用）；下区左两源（平台业务 / 自定义 Skill，源行「交给助手」总闸）+ 右目录（搜索 / 折叠 / 启停）。自定义 Skill 目录 = `engines/ai/skills`（本地仓库 + 上传）。点击 Skill 卡片进入 `/ai-assistant/toolbox/skills/:name`（左目录 / 右内容，Markdown 渲染）。业务模块默认折叠。

## 组件设计


## API 接口


## 快速验证清单

