## 1. 元素定位

- [x] 1.1 确认 `ProjectWorkspace.vue` 已把 `WorkbenchCrumbs` 放在 `.doc-body` 顶部且页头无 `#nav`（静态检索无 `<template #nav>`；浏览器打开 `/elements/projects/android` 可见面包屑在正文内）
- [x] 1.2 将 `LocatorFileView.vue` 的 `WorkbenchCrumbs` 从 `#nav` 挪到单一 `.doc-body` 顶部，加载/错误/有文件三态共用该面包屑；主区 flex 填满剩余高度。验证：源码无 `#nav`；打开文件详情页 `.wb-header` 内无 `.wb-crumbs`、`.doc-body` 内有

## 2. 用例管理

- [x] 2.1 将 `case-manager/ProjectWorkspace.vue` 按元素定位工作台同样结构迁移（Crumbs 在 `.doc-body` 顶、主区 flex）。验证：打开 `/cases/projects/:id` 页头无面包屑，正文顶部可回 `/cases`
- [x] 2.2 将 `CaseFileSheet.vue` 的 Crumbs 迁入 `.doc-body` 顶部，**保留** `#actions`。验证：文件页页头仍有保存/新建行；面包屑在正文顶；错误/加载态仍能点返回目录

## 3. 测试报告

- [x] 3.1 将 `ReportDetail.vue` 的 Crumbs 挪到现有 `.doc-body` 第一子节点。验证：`/reports/{runId}` 页头无 `.wb-crumbs`，正文顶部可回列表
- [x] 3.2 将 `TaskReport.vue` 的 Crumbs 挪到有数据态 `.doc-body` 顶部；错误态 `.doc-body` 同样放回退（至少返回芯片或等价 Crumbs）。验证：任务报告页页头无面包屑
- [x] 3.3 将 `CaseBreakdown.vue` 的 Crumbs 挪到 `.doc-body` 顶部（在 summary pill 之上）。验证：用例拆解页页头无面包屑

## 4. AI 助手深链

- [x] 4.1 将 `TaskDetailPage.vue` 的 Crumbs 迁入 `.doc-body` 顶部，错误态也在同一 `.doc-body` 内。验证：任务详情页头无面包屑，可回 `/ai-assistant/agents`
- [x] 4.2 将 `AgentDetail.vue` 同样迁移。验证：新建/编辑智能体页头无面包屑，可回平台小助手
- [x] 4.3 将 `SkillViewerPage.vue` 同样迁移。验证：Skill 查看页头无面包屑，可回 `/ai-assistant/toolbox`

## 5. 共享件与门禁

- [x] 5.1 全仓检索 `template #nav` / `$slots.nav`：无页面消费后删除 `WorkbenchHeader` 的 `#nav` 与 `.wb-header__nav`；更新 `WorkbenchCrumbs` 注释为挂在 `.doc-body` 顶部。验证：`rg "slots.nav|#nav" frontend/src` 无页头导航槽
- [x] 5.2 若门禁或测试断言面包屑在 `.wb-header` 内，改为断言在 `.doc-body` 且不在 `.wb-header`。验证：`cd frontend && npx vitest run tests/shared/p0/WorkbenchCrumbs.spec.ts` 通过
- [x] 5.3 前端构建通过：`cd frontend && npx vite build --mode development`
