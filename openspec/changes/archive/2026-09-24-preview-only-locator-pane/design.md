## Context

上一单 `relayout-locator-workspace`（已归档）在工作台右栏挂载了可编辑的 `LocatorFilePanel`，于是右栏与文件详情页同时具备写能力。需求方要求右栏退回只读预览，编辑仍走文件详情页。现有可复用资产：`LocatorFilePanel.vue`（文件详情页在用，不改）、`PageElementsWorkbench.vue`（可编辑表，含勾选/新增/删除/测试点开关）、`usePageElements.ts`（带 `immediate: true` 的自动加载与分页）、`helpers/elementPresentation.ts` 的 `interactionLabels`。

## Goals / Non-Goals

**Goals:**

- 右栏成为纯预览：可读、可跳转，不可写
- 预览与详情页共用同一张表纸与同一套列，不做第二套列口径
- 写入口唯一：文件详情页

**Non-Goals:**

- 不改后端端点、DTO 与写入口径
- 不改文件详情页的任何行为（仍可编辑、仍可删除）
- 不做右栏内联编辑（本单是反向收口）

## Decisions

**D1 新建独立只读预览组件，不复用 `PageElementsWorkbench`**
`PageElementsWorkbench` 携带勾选、新增、删除与测试点开关的全部状态与事件；用 props 把它「关掉」会引入一个可编辑/只读双模组件，反而更容易误开写入口。新建 `LocatorPagePreview.vue`，只消费 `usePageElements` 的读状态（`loading / error / rows / total`）与 `interactionLabels`，写函数一个不导入。

**D2 预览只取首屏若干条，并如实标注总数**
右栏是概览位，不是工作区。预览截取前 6 条，并在页脚标注「预览前 6 条 · 共 N 条」与入口按键；整页与分页留在详情页。

**D3 进入编辑的入口复用 `.element-detail-pane` 硬边按键皮肤**
入口按键走 `el-button type="primary"`，皮肤由既有 `components/elementDetailSkin.css` 提供，与详情页按键几何一致；右栏不需要新增皮肤规则。

**D4 文件的删除仍在目录树右键菜单**
右栏不再出现删除键；文件的删除入口保持目录树右键（既有行为），避免预览位出现破坏性操作。

## 模块防火墙自检

- 跨 App import：无（纯前端）
- 跨 App 写库 / ORM：无；右栏不发出任何写请求
- 前端直连数据库：无
- 前端 HTTP 出口：不变（只读经 `modules/element-locator/api.ts` 的 `pages/{id}/items/`）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [右栏看不到全部元素时用户可能以为数据缺失] → 页脚固定标注总条数与「预览前 N 条」，并提供进入编辑入口
- [预览与详情页列口径将来可能分叉] → 两处列定义都在同一模块内，且本条规范要求逐列一致；如列变更须同改
