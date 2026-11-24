# ai-assistant · 工作台网格与卡片

> 归属模块：`frontend/src/modules/ai-assistant` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/ai-assistant/index.vue`、`components/AssistantCard.vue`、`components/SopWorkflowSection.vue`、`components/SopWorkflowEditor.vue`、`components/SopRunForm.vue`、`components/AssistantEditor.vue`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## UI 布局（工作台与卡片）

- 入口 `/ai-assistant` 是助手颜料片网格（`WorkbenchHeader` + `.doc-body` + 卡片网格）。对话在 `/ai-assistant/:assistantId/chat`。
- 页面顺序：**助手网格在上、工作流网格在下**（`components/SopWorkflowSection.vue`），两区之间有一条 `SectionDivider` 虚线。两张卡片同在 `components/AssistantCard.vue` 里（虚线白名单按文件判定）：`item.kind === "assistant"` 出颜料片（图钉 + 头像或笔色圆 + 两枚按钮），`"workflow"` 出**便签卡 Tape Strip**（顶部半透明笔色胶带 + 白卡 + 浅墨虚线框；正文三行 = 名称 / `执行者：…` / `验收者：…`；底部三块同尺寸，`配置` 天蓝渐变、`任务` 薰衣草紫渐变（均纵向 20%→5%）、第三块是笔色占位块，无文字无交互）。助手颜料片的「配置/对话」同口径：配置天蓝、对话薄荷绿。不要再新开第二个虚线卡组件。
- 工作流卡片只有「配置」「任务」两个动作。配置弹窗 `SopWorkflowEditor.vue`：新建 `POST`、编辑预填后 `PATCH`、删除走 `ElMessageBox` 二次确认后 `DELETE`。任务弹窗 `SopRunForm.vue`：里程碑 YAML + **设备下拉**（选项来自设备管理 `GET /api/devices/`，必须选择设备，不手填），成功后关窗并提示任务编号。设备地址口径用 `shared/helpers/device-address.ts`，不要在本模块另写一份。
- 工作流的「新建工作流」入口在工作流区块自己的标题条里（与助手区块的「新建助手」同位），不放页面顶部动作区；页面上不再有常驻的工作流表单。
- 配置弹窗在 `index.vue` 的 `el-dialog` 里，`components/AssistantEditor.vue` 只出表单本体；**不要**给弹窗加 `append-to-body`（会脱离 `.ai-assistant-page`，取不到笔色令牌）。
- 点「配置」是**编辑**：预填该名片、保存走 `PATCH /api/ai/assistants/{id}/`。新建才 `POST`。
