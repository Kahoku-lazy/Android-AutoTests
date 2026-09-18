## Why

前端 L5 覆盖层存在两类现行违规：8 处浏览器原生 `confirm()` 旁路（集中在 workflow 模块，含 Pinia store 内 1 处），以及 4 处自建 backdrop / modal（`LoginErrorOverlay`、workflow 目录对话框、device-inspector 两个缩略图放大浮层）。它们与 `frontend/AGENTS.md`「L5 覆盖层统一走 EP，禁止自建 backdrop / modal」直接冲突，并与既有共享件（`ConfirmButton` / `el-dialog`）形成同层双实现。实测**不需要新增任何零件**即可收敛。

## What Changes

- 8 处 `window.confirm()` / `confirm()` 改为 `ElMessageBox.confirm()`（异步确认），涉及 6 个文件；`stores/libraryStore.ts` 的 store 内弹框一并收敛
- `views/components/LoginErrorOverlay.vue` 由自建全屏 modal 改为 `el-dialog` 薄封装，保留 `visible` / `message` / `@close` 对外契约
- `modules/workflow/index.vue` 的 `.wf-modal-backdrop` / `.wf-modal`（目录 / 页面流创建）改为 `el-dialog`，保留 autofocus / Enter 提交 / 名称必填行为
- `device-inspector` 的 `.pep-enlarge-mask`（`PageElementsPanel.vue`）与 `.sap-enlarge-mask`（`StructureAnalysisPanel.vue`）两个缩略图放大浮层改为 `el-dialog`，与既有 `StepScreenshotPanel.vue` 的 EP 预览口径一致
- 删除上述 4 处的自建遮罩 CSS（`position: fixed; inset: 0` + 自绘遮罩色）与手写 ESC 监听
- **不新增共享组件**：按既有共享件（`el-dialog` / `ElMessageBox`）替换，不抽第三套零件
- **非目标（本次明确不改，并登记原因）**：`ScreenshotView.vue` 的 canvas 边界框叠加层与 `PageScreenshotOverlay.vue` 的 svg 圈选层（均为在流内叠加，不是 modal）；3 处右键菜单（`.wf-ctx` / `.node-menu` / `.edge-menu`）；`PageFlowVueFlow.vue` 的光标锚定 `.el-picker` 选择器
- **BREAKING**：无。对外 API / 路由 / 后端契约不变；对话框外观由 `style.css` 既有 `.el-dialog` 全局皮肤提供，视觉为有意统一

## 关联文档

- 无 PRD / ARCH 编号文档对应：本变更属前端 L5 覆盖层实现收敛，不改业务需求与后端契约；`dev_docs/文档编号对照表.md` 不存在
- 规范依据：`frontend/AGENTS.md`「布局区域与归属」L5 行与规则 3（L5 覆盖层统一走 EP，禁止自建 backdrop / modal）
- 现状基线：`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L4-L5现状复盘.html` §四 / §五

## Capabilities

### New Capabilities

- `frontend-l5-overlay`: 前端 L5 覆盖层的实现口径与边界——阻塞层统一走 Element Plus、禁止浏览器原生对话框、同类场景唯一实现，并界定非 modal 浮层（右键菜单 / 画布叠加层 / 光标锚定 popover）不属于本能力

### Modified Capabilities

（无；`openspec/specs/` 下无既有 L5 覆盖层能力）

## Impact

- 前端 workflow（7 文件）：`stores/libraryStore.ts`、`components/WorkflowFileBrowser.vue`、`components/WorkflowDirTree.vue`、`components/vueflow/NodeContextMenu.vue`、`components/vueflow/EdgeContextMenu.vue`、`components/vueflow/PageFlowVueFlow.vue`、`index.vue`
- 前端 device-inspector（2 文件）：`components/PageElementsPanel.vue`、`components/StructureAnalysisPanel.vue`
- 前端 views（1 文件）：`components/LoginErrorOverlay.vue`
- 报告修正：`报告-前端区域层级与L4-L5现状复盘.html`（§五 把 canvas / svg 叠加层与右键菜单误归为「自建浮层」，需按实测更正）
- 测试与门禁：`cd frontend && npm run typecheck`、`npm run build:check`；`vue-frontend-check` 过改动文件；`rg` 复核指令原地命中应为 0
- 不影响：后端 API、鉴权、路由表、`openspec/specs/` 既有能力、L0–L4 层实现
