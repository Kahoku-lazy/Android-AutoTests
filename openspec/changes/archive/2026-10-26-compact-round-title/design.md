## Context

任务详情的轮次标题由 `frontend/src/modules/task-list/TaskDetailPage.vue` 里的 `roundTitle(round)` 拼成一个字符串：`stepName(step_seq)` + 重试次数 + 角色类别 + `role · model` + `subject`；模板在行首另渲染 `roundOffset + roundIndex + 1` 的序号，于是序号出现两次。角色名与模型名之间用 `·` 连接，与角色类别同处一段纯文本。

## Goals / Non-Goals

**Goals:**

- 标题里只保留一处序号；不再写中文步骤序号与模型名。
- 角色名以徽章呈现，与 PASS / FAIL 徽章同一视觉族，扫读时能一眼分出「类别 / 实例名 / 判决」。
- 拼装逻辑离开组件、进 `helpers/task-detail.ts` 并单测覆盖。

**Non-Goals:**

- 不改 `GET /api/tasks/{id}/report/` 的字段与事件聚合口径（`role` / `role_kind` / `model` 照旧下发）。
- 不改 PASS / FAIL 徽章、交付块、结论块、分页与折叠行为。
- 不新增设计令牌、不改字号刻度。

## Decisions

**1. 徽章内联在标题文本里，而不是把标题拆成多个 flex 子盒。**

`roundTitle` 现在是 flex 容器的一个文本子项（`.flow-round__text`）。若把「序号+类别」「角色徽章」「动作」拆成三个 flex 子项，每个子项都是不可断行的盒子，长动作文本会整段换行、留出半行空白。改为在文本流里插入 `display: inline-block` 的徽章，文本仍按自然断行流动。备选（flex 子项）被否决，理由即断行效果。

**2. 角色名原样展示 `executor_role`，不去 `_role` 后缀、不映射中文。**

报告接口的 `role` 是会话里的实例名，排查时要和事件日志（`ReplyStartEvent.name`）逐字对得上；改写成中文会丢掉这条对齐线索。

**3. 新增 `.badge-role` 复用 `.badge` 基础样式。**

只换底色与字重：底色 `--paper`、字色 `--app-text-secondary`、边框沿用 `--ink` 2px、字号沿用 `--app-size-xs`。样式门禁只允许既有令牌，故不引入新色值。徽章之间的间距由标题的 `gap` 之外单独给 `margin`（内联元素不吃 flex gap）。

**4. 两段纯函数，未知角色回落执行模型。**

`roundKindLabel(role_kind)`：`executor` / `verifier` / `planner` → 中文类别，未知或空回落「执行模型」，与改动前 `else` 分支一致，避免存量事件出现空标题。
`roundTitleTail({attempt, subject})`：`第 N 次`（仅 `attempt > 1`）与 `：动作` 拼接；两者皆无时返回空串，模板据此不渲染尾段。

## 模块防火墙自检

- 只改 `frontend/src/modules/task-list` 内部与同模块 `helpers/`；不新增跨模块 import，`ai-assistant` 未被反向引用。
- 组件只保留渲染与事件绑定，拼装逻辑进 `helpers/`（符合 frontend AGENTS「组件不写业务逻辑」）。

## Risks / Trade-offs

- [存量事件 `role` 为空] → 该轮不渲染角色徽章，其余标题不变（模板 `v-if`）。
- [徽章比纯文本略宽] → 「executor_role」纯文本变徽章后宽度接近，已省掉「步骤一」与 `deepseek-flash`，整行更短。
- [样式门禁] → 只用既有令牌与既有字号刻度，不硬编码颜色与 `font-size`。
