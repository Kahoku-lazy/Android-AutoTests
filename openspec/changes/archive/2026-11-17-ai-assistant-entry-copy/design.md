## Context

`/ai-assistant` 页（`modules/ai-assistant/index.vue`）结构：`WorkbenchHeader` → `.doc-body` → 助手网格 → `SectionDivider` → `SopWorkflowSection`。

两个区块的标题条现在不一致：

- 助手区只有一行 `<div class="ai-assistant-page__bar">`：计数在左、按钮在右，没有标题（`justify-content: space-between`）。
- 工作流区是 `<div class="sop-section__bar">`：`h2` 标题（20px / heavy / 墨色）+ 计数 + 弹性空白 + 按钮，样式写在 `SopWorkflowSection.vue` 的 scoped block 里。

侧栏那边，`NAV_CATEGORIES.ai` 分组只剩「AI 助手」一条，`AppSidebar.vue` 用 `v-if="cat.label && !collapsed"` 渲染分组标题行 —— label 为空串时该行不出现。

## Goals / Non-Goals

**Goals:**

- 助手区与工作流区标题条位置、字号、对齐完全一致，由同一个组件渲染。
- 入口与页头文案统一为「平台助手」，侧栏不再显示「AI 功能」标题。
- 助手区标题仍是「AI 助手」（它描述的是这一区列出的名片实体）。

**Non-Goals:**

- 不改工作流区的卡片、弹窗与数据流。
- 不改对话页（`/ai-assistant/:id/chat`）的页头：那里显示的是具体助手的名字。
- 不改 `shared/components/SectionDivider.vue` 与两区之间的虚线。
- 不恢复测试报告 / 执行报告入口。

## Decisions

**1. 抽模块内共享件 `components/SectionBar.vue`，两处都用它。**
两份手写 CSS 一定会漂移（这次就是一边 20px 带标题、另一边 14px 不带）。抽成一个组件后「位置相同」由构造保证，不靠人对照。
备选：把 `sop-section__bar` 的样式复制进 `index.vue`（最快，但下次改样式要改两处，且 scoped 样式互相看不见）——否决。
备选：放进 `shared/components/`（跨模块复用）——目前只有 ai-assistant 一个模块用，放模块内更合适，等第二个模块用到再上提。

**2. 标题条只接 title / count / action 插槽，不做成通用 PageSection。**
它要管的只有「一行三件 + 弹性空白」，再加属性就会变成第二套布局件。动作区用插槽，是因为两个区块的按钮文案与事件不同，但几何一致。

**3. 助手区标题写「AI 助手」而不是「平台助手」。**
页头已经叫「平台助手」，它指的是这个页面；区块标题描述的是「这一区列的是 AI 助手名片」，与下面的「工作流」同一层级。两个层级各说各的，不重复也不冲突。

**4. 改名要同时改三处：侧栏文案、`WorkbenchHeader`、路由 `meta.title`。**
只改一处会出现「侧栏叫平台助手、标签页还叫 AI 助手」的不一致。`sidebarNavConfig.spec.ts` 里已有对入口文案的断言，改名后它会红，正好当护栏。

## 模块防火墙自检

- 只改 `frontend/src/shared/components` 的静态导航配置，以及 `frontend/src/modules/ai-assistant/**` 的页面与组件，不跨模块 import。
- 不涉及后端、数据库、接口；`SectionBar` 是纯展示组件，无状态无请求。

## Risks / Trade-offs

- [抽组件后工作流区样式出现细微变化（例如行高或 gap）] → 直接把原 `.sop-section__bar` 的声明整段搬进 `SectionBar.vue`，值一一对应；`vue-tsc` 与 `tests/ai-assistant` 全绿，且两区用同一个组件，不会再各走一套。
- [「平台助手」与页内「AI 助手」两个词并存，读者可能困惑] → 层级不同：页头 = 页面名（平台助手），区块标题 = 列出的实体（AI 助手）；与「工作流」区块并列时语义清楚。
- [改名会与历史文档/spec 里的大量「AI 助手」字样产生漂移] → 本次只改入口与页头三处文案，其它文档按各自变更单独收敛，不做全局替换。
