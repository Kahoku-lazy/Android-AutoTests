# ai-assistant · 对话页、对话栏与运行日志

> 归属模块：`frontend/src/modules/ai-assistant` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/ai-assistant/chat.vue`、`components/AssistantLanePanel.vue`、`components/ThreadLogPanel.vue`、`helpers/time-label.ts`、`api/assistants.ts`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## UI 布局（对话页与运行日志）

- 对话页页头用 `WorkbenchHeader`，助手名从路由 `query.name` 带入（`openChat` 负责带），不为此多打一次列表请求。
- 页头**不放动作按钮**：「‹ 返回助手」在 `.doc-body` 顶部工具条。左栏与对话区之间的纵向虚线由 `AssistantLanePanel.vue` 自己声明（拉满整列高度；落在两栏间距中线，与面板右边框留 12px，不贴边）。
- 对话栏：`✎` 就地改名（Enter 提交 / Esc 取消 / 失焦提交）、`✕` 删除（`ElMessageBox` 二次确认）。改名走 `PATCH /ai/assistants/threads/{id}/`，删除走 `POST /ai/assistants/threads/{id}/delete/`；取消仍是 `DELETE /ai/assistants/threads/{id}/`，**不要**把三者混用。
- 当前栏的唯一选中信号是**浅蓝填充 + 2px 墨框**；「新建对话」用 `DoodleBtn tone="teal"`。
- 运行日志入口是工具条那个「日志」按钮（已开再点收起）。日志卡住在**左栏、对话栏下面**（`AssistantLanePanel` 的默认插槽），与「这一栏」同列；展开时 `.ai-chat__body` 挂 `is-logs-open`，左栏 `240px → clamp(320px, 30%, 420px)`、聊天列相应收窄，收起回 240px。
- **不要**把日志卡塞进 `.ai-chat__body` 当第三个网格子项（会把对话区挤进 240px 左栏，整页变形），也**不要**塞回对话区消息流里（会把消息往下顶、右侧空出一大片）。日志卡列表自身不滚，多了由 `.doc-body` 滚。切栏时日志属于「当前栏」，跟消息一起清掉、面板开着就按新栏重取。
- 日志面板三态用共享件（`SkeletonCard` variant="list" / `ErrorState` 可重试 / `EmptyState`），进行中的一轮只显示「还在写」且不可点、不显示时间。
- 日志卡是**一轮一张**：`1.5px` 虚线（该助手笔色 70% + 纸色）+ 顶部居中胶带 + `4px 4px` 硬影 + `--app-radius-md` + 白卡底，**0° 不倾斜**（需求方指定，参考图见 doodle-craft `assistant-marker-card.md` §5.2）；卡内首行时间 + 一句话结果，右侧「查看 / 还在写」。
- 时间只有一个来源：后端消息的 `created_at`（本地 ISO，带 `+08:00`）。气泡时刻 `HH:mm` 用 `helpers/time-label.ts` 的 `clockLabel` 只取墙上时间、**不换算时区**；日志卡用 `logCardTime`（缺 `created_at` 才回落报告编号）。
