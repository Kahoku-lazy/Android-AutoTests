## Why

平台工作台外壳已是 Doodle Craft，但子页导航仍是各页私写「← 返回」按钮、设备列表仍套 `el-card`、报告列表与设备表未共用同一张「表纸」。需要按 `module-subpages-doodle-proto.html` 的 P0 把共享壳与可见回退导航落到 L0–L5 上，且颜色/间距只走 `tokens.css`。

## What Changes

- 新增 L2 共享导航零件：波浪面包屑 + 返回芯片，挂在 `WorkbenchHeader` 内（不另建页头）
- 把既有 L2+ 回退点换成该导航模版：报告详情链（列表行进入）、元素/用例工作台与叶子、AI 深链（任务 / Skill / 智能体编辑）
- 将 SketchTable 定义为 `AppTable` 的表纸皮肤（虚线纸 + 模块色硬阴影），设备管理与报告列表共用；设备列表去掉 `el-card` 外套
- L5 含输入的弹层（设备局域网连接 / 断开确认等）走同一套 EP dialog 纸面皮肤，令牌登记在 `tokens.css`，不自建 DialogForm 覆盖层
- Hub 入口继续只用已有 `SketchCard`（本轮不抽 `HubProjectPage` / `TreeWorkbench` 壳）
- **BREAKING**：无 API / 路由破坏。视觉为有意换皮；页头 actions 里的「← 返回 xxx」文案统一为共享返回芯片 + 面包屑

## 关联文档

- 视觉方案：`dev_docs/项目笔记/平台前端主题参考模版/module-subpages-doodle-proto.html`（P0 共享件 + 三种导航模版；落地顺序第 1–2 段）
- 骨架：`frontend/AGENTS.md` L0–L5；令牌：`frontend/src/shared/styles/tokens.css`
- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（前端壳与模块边界，不改路由深度）
- UI 规范：无单独「子页导航」checklist；组件规格落 `doodle-craft/references/components.md`
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更不改后端接口

## Capabilities

### New Capabilities

- `frontend-doodle-subpage-nav`：L2+ 可见回退（返回芯片与/或波浪面包屑）、三种导航模版（面包屑条 / 侧栏子项 / 列表行进入）及 AI 深链回到对应子项
- `frontend-doodle-sketch-table`：`AppTable` 表纸皮肤（SketchTable）与模块色硬阴影；设备管理与报告列表共用，禁止第二套表格封装

### Modified Capabilities

- `frontend-l2-page-region`：L2 页头仍唯一来自 `WorkbenchHeader`；新增「子页必须可见回退」且导航零件落在页头区内，不得在正文再叠第二套顶栏导航
- `frontend-l4-data-surface`：扁列表表纸走 SketchTable 皮肤；设备列表不得再用 `el-card` 当表纸
- `frontend-l5-overlay`：含输入的设备弹层使用登记过的 dialog 纸面令牌；仍禁止自建 backdrop / 第二套 DialogForm 组件作为覆盖层实现

## Impact

- 共享：`WorkbenchHeader.vue`、新 `WorkbenchCrumbs`（或等价）、`AppTable` / `workbench-theme.css`、`tokens.css`、`style.css` 的 dialog 纸面
- 模块：`device-pool/index.vue` 及连接/断开 dialog；`report-generator` 列表与详情（`index` / `ReportDetail` / `TaskReport` / `CaseBreakdown`）；`element-locator` 与 `case-manager` 的工作台/叶子页头；`ai-assistant` 的 `TaskDetailPage` / `SkillViewerPage` / `AgentDetail`
- 文档：`frontend/AGENTS.md` 共享件条目、`doodle-craft` 组件规格
- 测试：相关 Vue 单测、`cd frontend && npm run typecheck`、`npm run lint:styles`
- 不影响：后端 API、路由表深度、检查器分栏换皮、页面流画布、评测中心、仪表盘钉板收尾（P1/P2）
