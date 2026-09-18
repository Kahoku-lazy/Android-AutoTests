## Context

见 `proposal.md` 的 Why。现行实现：`TaskDetailPage.vue` 右侧每轮 `article.td-attempt` 把 Executor / Verifier / 执行结果全部放进同一 `el-collapse`，内层再套折叠；`TaskDetailPage.vue` 已超过 500 行。数据仍来自 `taskStepBlocks` / `attemptTraceSides`，本变更不改 API。

## Goals / Non-Goals

**Goals:**

- 执行结果（结论两行 + 验证截图）提到折叠外，默认可见
- 用 scoped 样式拉开标题 / 正文 / 折叠项层级，令牌不硬编码
- 控制 `TaskDetailPage.vue` 体积：尝试卡片拆到私有组件

**Non-Goals:**

- 不改 `GET /ai/agent-tasks/{id}`、轮询、左侧步骤清单、底栏最终结果
- 不改主题令牌；不把尝试卡片抽到 `shared/`

## Decisions

1. **执行结果用静态区块，过程仍用 `el-collapse`**  
   结论是验收主信息，必须常显。过程日志可很长，保留折叠。备选（整卡全展开）会让多轮重试难以扫读，已否决。

2. **拆出 `TaskAttemptCard.vue`**  
   页面已超 500 行且本次会加区块标记。把单轮尝试的模板与样式迁到 `frontend/src/modules/ai-assistant/components/TaskAttemptCard.vue`；展示纯函数仍留在 `helpers/task-detail.ts`。备选（只拆 CSS）减行数有限，模板仍堆在详情页。

3. **截图不套折叠**  
   有 `screenshotUrl` 则直接 `el-image` 预览，不再「验证截图」折叠项。

4. **Agent 折叠默认全部收起**  
   不设 `v-model` 默认展开 name，避免过程盖住结论。

## 模块防火墙自检

- 不改后端，无跨 App import
- 无 INSERT/UPDATE/DELETE
- 前端仍只经现有 `getTask`（`api/tasks.ts` → `djangoClient`）读详情
- 仪表盘不涉及

## Risks / Trade-offs

- [多轮尝试 + 多张截图撑高右侧栏] → 右侧面板保持现有内层滚动，不改左栏
- [折叠样式被 Element Plus 默认挤扁] → 用已有 `.td-trace` `:deep()` 加强标题字重、内边距与左边框，不用硬编码色
