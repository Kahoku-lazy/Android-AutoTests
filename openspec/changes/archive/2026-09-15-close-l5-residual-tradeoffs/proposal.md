## Why

L5 只剩两处登记取舍，且两处都不是缺陷而是**缺判据**：

1. **弹层关闭策略无统一判据**：实测 8 处显式写 `:close-on-click-modal="false"`、其余依赖 EP 默认，`destroy-on-close` 仅 `EvaluatorTab` 一处。接手者拿到一个新弹层无从判断该选哪个，于是继续各写各的。
2. **Pinia store 用模态弹窗询问用户**：`libraryStore.savePageFlowPayload()` 在 `opts.confirmEmptyOverwrite` 为真时直接调用 `ElMessageBox.confirm`（`libraryStore.ts:412`），让状态层耦合 Element Plus 与 DOM。测量口径：全仓 store 文件中 `ElMessageBox` 命中 **1 处**（即此处），改为回调后归零；`ElMessage`（Toast，`device-inspector/store.ts`）不在本变更范围。

## What Changes

**① 弹层关闭策略：定判据 + 补齐 4 处**

- 判据：**含可编辑输入或危险操作确认**的弹层 → `:close-on-click-modal="false"`（防误触丢失未保存输入 / 误确认）；**纯展示 / 预览 / 只读列表选择** → 保持 EP 默认（点遮罩即关）
- 按判据补 `:close-on-click-modal="false"`：`workflow/index.vue`（目录对话框，含输入）· `device-inspector/SaveToElementsDialog.vue`（选择 + 输入）· `ai-assistant/components/TaskBoard.vue`（新建任务表单）· `ai-assistant/EvaluatorTab.vue`（试卷编辑器表单）
- `destroy-on-close` 判据：**内容持有本地状态且每次打开必须重置**时才用；现仅试卷编辑器满足，本变更只登记判据、不新增用法
- 其余 13 处（预览 / 抽屉 / 只读选择 / 危险确认）经核对已符合判据，不动

**② `libraryStore` 解耦 UI：依赖倒置**

- `opts.confirmEmptyOverwrite?: boolean` → `confirmEmptyOverwrite?: (remoteNodes: number) => Promise<boolean>`：store 只负责**询问**，弹窗实现由调用方提供
- 移除 `libraryStore.ts` 的 `import { ElMessageBox } from 'element-plus'`（该文件内唯一用途就是这处确认）
- `workflow/index.vue` 新增 `confirmEmptyOverwriteDialog(remoteNodes)`：沿用原文案与确认参数（`确定` / `取消` / `warning`），把 UI 决策收回视图层
- **BREAKING**：无。行为等价（同样的条件、同样的文案、同样的取消语义）

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md`：新增 2 条需求
- `openspec/changes/archive/2026-09-14-converge-l5-overlay-language/`：该 store 内 `ElMessageBox` 的引入与「登记取舍」出处
- `openspec/changes/archive/2026-09-15-align-l5-overlay-skin-and-binding/`：同层「绑定按状态归属」判据的先例（本变更沿用「先定判据再补齐」的做法）
- `frontend/AGENTS.md` L5 速查 §③/⑤/⑥：判据与缺口的登记处
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端覆盖层与状态层解耦，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l5-overlay`: 新增「Overlay close policy follows input-bearing content」与「Store layer does not ask users via modal dialogs」两条需求（后者只约束**模态询问**；`ElMessage` Toast 不在范围内——`device-inspector/store.ts` 现有 Toast 用法保留，属另一议题）

## Impact

- `frontend/src/modules/workflow/stores/libraryStore.ts` · `frontend/src/modules/workflow/index.vue` · `device-inspector/components/SaveToElementsDialog.vue` · `ai-assistant/components/TaskBoard.vue` · `ai-assistant/EvaluatorTab.vue`
- `openspec/specs/frontend-l5-overlay/spec.md`（归档时更新）· `frontend/AGENTS.md`（L5 速查 §③/⑤/⑥）
- 测试与门禁：`vue-tsc --noEmit`；`vue-frontend-check` 过 5 个改动文件；4 个新增 `false` 的弹层浏览器核验（点遮罩不关、ESC 仍可关）
- 不影响：其余 13 处弹层配置、`ElMessage` / `ElMessageBox` 在**视图层与 composable** 中的既有用法（本变更只禁止 **Pinia store** 依赖 UI 组件）