# ai-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## UI 布局

- 入口 `/ai-assistant`（redirect 到 `/ai-assistant/agents`，`index.vue`）；侧栏「AI 助手」是**单一入口**，没有子项、页内也没有第二套 Tab。评测中心、知识库、AI 工具箱均已下线。
- `agents` 视图 = **小助手看板**：`AgentRouteCard` × 1（`device_control`）直接置于页面背景，不再使用 `.doc-section` 白底外框，也没有「平台小助手 / Assistant / N 个助手」区块标题行；卡片约 312px 宽、头像约 120px，右侧三行依次为名称/职责/配置，窄屏降档收缩。身份卡 = **左正方形头像**（边长 = 右侧三行自然总高）+ **右三行**（名称 / `职责：UI自动化` / 「配置」，仅超管）+ 无底部整行操作区。无独立功能标题带，**无连通状态徽标与校验按钮**（校验功能已下线）。每条线路独立 `route_configs.{route}.name/avatar`。任务卡片列表不在此页。
- **配置页** `/ai-assistant/agent/:id`（`AgentDetail`）：只保留**基本信息**——名称 / 头像 / 标签 / 描述，加两栏只读的**职责（UI自动化）**与**工作流（ui_auto_workflow）**（当前写死，不落库）。模型 / 线路 / 循环次数 / 模型校验区块已删除；保存时名称与头像仍会写入 `route_configs.device_control`，卡片与任务列表随之同步；模型配置改由后台维护。
- **AI 工具箱（装配台）已整体下线**：`/ai-assistant/toolbox`、Skill 查看页、平台工具调试页、`api/toolbox.ts` 与其组合式/纯函数全部删除；平台业务工具与自定义 Skill 不再有平台侧开关，SOP 的工具集由引擎代码固定装配（见 `sop-task-run`）。

## 组件设计


## API 接口


## 快速验证清单
