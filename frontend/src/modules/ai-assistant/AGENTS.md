# ai-assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## UI 布局

- 入口 `/ai-assistant` 是助手颜料片网格（`WorkbenchHeader` + `.doc-body` + 卡片网格）。对话在 `/ai-assistant/:assistantId/chat`。
- 页面顺序：**助手网格在上、工作流网格在下**（`components/SopWorkflowSection.vue`），两区之间有一条 `SectionDivider` 虚线。两张卡片同在 `components/AssistantCard.vue` 里（虚线白名单按文件判定）：`item.kind === "assistant"` 出颜料片（图钉 + 头像或笔色圆 + 两枚按钮），`"workflow"` 出**便签卡 Tape Strip**（顶部半透明笔色胶带 + 白卡 + 浅墨虚线框；正文三行 = 名称 / `执行者：…` / `验收者：…`；底部三块同尺寸，`配置` 天蓝渐变、`任务` 薰衣草紫渐变（均纵向 20%→5%）、第三块是笔色占位块，无文字无交互）。助手颜料片的「配置/对话」同口径：配置天蓝、对话薄荷绿。不要再新开第二个虚线卡组件。
- 工作流卡片只有「配置」「任务」两个动作。配置弹窗 `SopWorkflowEditor.vue`：新建 `POST`、编辑预填后 `PATCH`、删除走 `ElMessageBox` 二次确认后 `DELETE`。任务弹窗 `SopRunForm.vue`：里程碑 YAML + **设备下拉**（选项来自设备管理 `GET /api/devices/`，必须选择设备，不手填），成功后关窗并提示任务编号。设备地址口径用 `shared/helpers/device-address.ts`，不要在本模块另写一份。
- 工作流的「新建工作流」入口在工作流区块自己的标题条里（与助手区块的「新建助手」同位），不放页面顶部动作区；页面上不再有常驻的工作流表单。
- 配置弹窗在 `index.vue` 的 `el-dialog` 里，`components/AssistantEditor.vue` 只出表单本体；**不要**给弹窗加 `append-to-body`（会脱离 `.ai-assistant-page`，取不到笔色令牌）。
- 点「配置」是**编辑**：预填该名片、保存走 `PATCH /api/ai/assistants/{id}/`。新建才 `POST`。
- 对话页页头用 `WorkbenchHeader`，助手名从路由 `query.name` 带入（`openChat` 负责带），不为此多打一次列表请求。
- 页头**不放动作按钮**：「‹ 返回助手」在 `.doc-body` 顶部工具条。左栏与对话区之间的纵向虚线由 `AssistantLanePanel.vue` 自己声明（拉满整列高度；落在两栏间距中线，与面板右边框留 12px，不贴边）。
- 对话栏：`✎` 就地改名（Enter 提交 / Esc 取消 / 失焦提交）、`✕` 删除（`ElMessageBox` 二次确认）。改名走 `PATCH /ai/assistants/threads/{id}/`，删除走 `POST /ai/assistants/threads/{id}/delete/`；取消仍是 `DELETE /ai/assistants/threads/{id}/`，**不要**把三者混用。
- 当前栏的唯一选中信号是**浅蓝填充 + 2px 墨框**；「新建对话」用 `DoodleBtn tone="teal"`。
- 运行日志入口是工具条那个「日志」按钮（已开再点收起）。日志卡住在**左栏、对话栏下面**（`AssistantLanePanel` 的默认插槽），与「这一栏」同列；展开时 `.ai-chat__body` 挂 `is-logs-open`，左栏 `240px → clamp(320px, 30%, 420px)`、聊天列相应收窄，收起回 240px。
- **不要**把日志卡塞进 `.ai-chat__body` 当第三个网格子项（会把对话区挤进 240px 左栏，整页变形），也**不要**塞回对话区消息流里（会把消息往下顶、右侧空出一大片）。日志卡列表自身不滚，多了由 `.doc-body` 滚。切栏时日志属于「当前栏」，跟消息一起清掉、面板开着就按新栏重取。
- 日志面板三态用共享件（`SkeletonCard` variant="list" / `ErrorState` 可重试 / `EmptyState`），进行中的一轮只显示「还在写」且不可点、不显示时间。
- 日志卡是**一轮一张**：`1.5px` 虚线（该助手笔色 70% + 纸色）+ 顶部居中胶带 + `4px 4px` 硬影 + `--app-radius-md` + 白卡底，**0° 不倾斜**（需求方指定，参考图见 doodle-craft `assistant-marker-card.md` §5.2）；卡内首行时间 + 一句话结果，右侧「查看 / 还在写」。
- 时间只有一个来源：后端消息的 `created_at`（本地 ISO，带 `+08:00`）。气泡时刻 `HH:mm` 用 `helpers/time-label.ts` 的 `clockLabel` 只取墙上时间、**不换算时区**；日志卡用 `logCardTime`（缺 `created_at` 才回落报告编号）。

## 样式

- 虚线只允许四个落点：`AssistantCard.vue`（助手颜料片外框 2.5px、卡内动作 1.5px；工作流便签卡外框 1.5px 浅墨）、`AssistantLanePanel.vue`（面板框与两栏分隔，1.5px 浅墨）、`ThreadLogPanel.vue`（日志卡 1.5px，笔色 70%）、`shared/components/SectionDivider.vue`（页面分区横线，1.5px 浅墨，**现在 `index.vue` 里用它分隔助手区与工作流区**）。四者都已登记在 `check-dashed-whitelist.mjs` 的 OWNERS 里；配置弹窗、气泡、输入框、按钮一律实线。
- 笔色色值只在 `tokens.css`；`helpers/marker.ts` 只映射变量名。深到浅的浅底 / 渐变由消费它的组件用 `color-mix` 现算，**不要**在 `.ai-assistant-page` 上预置（不会随卡片笔色重算）。
- 规格与反模式见 `.agents/skills/doodle-craft/references/components/assistant-marker-card.md`。

## 红线

- **禁止**把虚线或笔色渐变扩散到其它模块、弹窗、表格。
- **禁止**在卡片上补工具清单、模型名、编号、状态角标——卡片只放名称、头像或笔色圆、Agent 配置名。
- **禁止**用 `--c-ai` 冒充笔色（模块色只给侧栏与页头默认图标）。
- 智能体看板、对话工作流、配置页已随重设计下线，不再有 `/ai-assistant/agents` 与 `/ai-assistant/agent/:id`。
- `api/agents.ts` 与 `constants.ts` 的 `TASK_KIND_*` 仍被任务清单的发布弹窗引用，删除前先改 `task-list`。助手名片与测试对话走 `api/assistants.ts`，不要塞回 `agents.ts`。

## 快速验证

```bash
cd frontend
npx vitest run tests/ai-assistant
npx vue-tsc --noEmit
node tests/check-style-gates.mjs
```
