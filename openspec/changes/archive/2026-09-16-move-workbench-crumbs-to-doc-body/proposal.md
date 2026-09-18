## Why

L2 子页把 `WorkbenchCrumbs` 挂在 `WorkbenchHeader` 的 `#nav` 槽，页头同时承担标题带与回退导航，高度被撑开、职责混杂。用户要求页头只保留主标题与副标题（品牌图标仍属标题带），面包屑与返回芯片移入 `.doc-body`。

## What Changes

- 所有当前把 `WorkbenchCrumbs` 放在 `WorkbenchHeader #nav` 的 L2 子页，改为在 `.doc-body` 顶部渲染同一套回退导航（返回芯片 + 波浪面包屑）。
- `WorkbenchHeader` 在这些页面上不再接收 `#nav`；页头只渲染品牌图标、主标题、副标题。已有 `#actions`（如用例文件页的保存/新建行）仍留在页头，不随面包屑迁出。
- 无剩余 `#nav` 消费方时，移除 `WorkbenchHeader` 的 `nav` 槽及 `.wb-header__nav`，避免零消费声明。
- **BREAKING（相对现行 spec）**：`frontend-l2-page-region` 要求「子页导航必须在 L2 页头内、禁止出现在 `.doc-body` 顶部」将被改为「导航必须在 `.doc-body` 顶部、禁止出现在 `.wb-header`」。`frontend-doodle-subpage-nav` 的「页头区」放置口径同步改为正文区顶部。
- 元素定位项目工作台（`ProjectWorkspace.vue`）已按该布局落地，本变更将其纳入范围并推广到其余子页，不回滚。

## 关联文档

- UI 规范：`dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md`（页头与正文水平内边距、滚动策略）
- 主 spec：`openspec/specs/frontend-l2-page-region/spec.md`、`openspec/specs/frontend-doodle-subpage-nav/spec.md`
- 无单独 PRD/ARCH 编号：本变更为既有 L2 工作台布局契约调整，不新增业务能力。

## Capabilities

### New Capabilities

- （无）本变更不引入新能力，只改放置区域。

### Modified Capabilities

- `frontend-l2-page-region`: 子页可见回退从页头 `#nav` 改为 `.doc-body` 顶部；页头不再承载面包屑。
- `frontend-doodle-subpage-nav`: 「L2 页头区」可见回退改为「L2 页面正文区顶部」；三种导航模版与祖先链语义不变。

## Impact

- 前端共享件：`WorkbenchHeader.vue`、`WorkbenchCrumbs.vue`（注释与挂载约定）
- 页面（迁出 `#nav`）：
  - element-locator：`LocatorFileView.vue`；`ProjectWorkspace.vue`（已完成）
  - case-manager：`ProjectWorkspace.vue`、`CaseFileSheet.vue`（保留 `#actions`）
  - report-generator：`ReportDetail.vue`、`TaskReport.vue`、`CaseBreakdown.vue`
  - ai-assistant：`TaskDetailPage.vue`、`AgentDetail.vue`、`SkillViewerPage.vue`
- 测试：`WorkbenchCrumbs.spec.ts` 仍测零件本身；若有门禁/快照断言「面包屑在 `.wb-header` 内」须改为断言「在 `.doc-body` 内且不在 `.wb-header`」
- 后端 API、路由、数据契约不变
