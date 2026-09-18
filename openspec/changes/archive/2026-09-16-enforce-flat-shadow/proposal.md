## Why

设计语言要求阴影**扁平硬偏移**（模糊半径为 0），但全仓仍有 **8 处**带模糊半径的投影，模糊从 1px 到 48px 不等：`ai-assistant` 2 处（头像卡 8px、保存按钮 hover 14px 光晕）、`device-inspector` 4 处（截图图钉 1px、屏幕图 24px、两个放大预览 32px）、`workflow` 2 处（API 节点 8px 外发光、元素选择浮层 48px 投影）。这些光晕与"纸面 + 马克笔硬偏移"的语言直接冲突，也让同一类浮层在不同模块的层次表意不一致；其中 `AgentBasicInfo.vue` 的 `--avatar-shadow` 还是该模块唯一的裸 `rgba()` 字面量。`frontend-l0-design-tokens` 目前只约束颜色/字号/令牌归属，未登记阴影规格，故本变更同时把「阴影必须扁平」立为可测规格，避免后续回归。

## What Changes

- 收敛 8 处模糊阴影为扁平硬偏移：优先复用已登记令牌（`var(--app-shadow-sm/md/lg)`），需要保留模块色源时改为 `Npx Npx 0 0 <既有色源>`
- 删除随之成为零消费方的两条自定义属性：`AgentFormFooter.vue` 的 `--nav-save-glow`、`PageFlowNode.vue` 的 `--wf-node-api-glow`
- 删除 `AgentBasicInfo.vue` 的模块私有 `--avatar-shadow`（其值是全模块唯一裸 `rgba()`），改用 `var(--app-shadow-sm)`
- 在 `frontend-l0-design-tokens` 新增要求「阴影规格扁平且不含模糊投影」，覆盖直接声明与经自定义属性间接声明的两类写法，并禁止用外发光（`0 0 <blur>`）作强调
- **BREAKING**：无。纯视觉语言收敛，不涉及接口、路由、鉴权或数据；`device-inspector` 与 `workflow` 的浮层观感会由"柔和投影"变为"硬偏移纸片影"

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §5.4 与 §八·批次 A（P0-3）
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 1 · `enforce-flat-shadow`
- 规格真相源：`openspec/specs/frontend-l0-design-tokens/spec.md`（本变更为其新增阴影要求）
- 主题约束：`.agents/skills/doodle-craft/references/tokens.md`（阴影扁平 0 模糊）、`frontend/AGENTS.md`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增要求「阴影规格扁平且不含模糊投影」

## Impact

- `frontend/src/modules/ai-assistant/components/AgentBasicInfo.vue`（删私有阴影变量，改用 `--app-shadow-sm`）
- `frontend/src/modules/ai-assistant/components/AgentFormFooter.vue`（hover 光晕 → `--app-shadow-lg`，删 `--nav-save-glow`）
- `frontend/src/modules/device-inspector/components/ScreenshotView.css`（图钉影、屏幕影改扁平）
- `frontend/src/modules/device-inspector/components/PageElementsPanel.vue`、`StructureAnalysisPanel.vue`（放大预览影改扁平）
- `frontend/src/modules/workflow/components/vueflow/PageFlowNode.vue`（API 节点外发光 → `--app-shadow-md`，删 `--wf-node-api-glow`）
- `frontend/src/modules/workflow/components/vueflow/PageFlowVueFlow.vue`（元素选择浮层影改扁平）
- 测试范围：`npm run lint:styles`、`npm run typecheck`、`npx vite build --mode development`，以及模糊半径为 0 的静态复核与 Chromium 渲染断言
- 不影响：`AppTable` / `AppCard` / `KpiCard` 等共享件（其阴影本就是扁平令牌）；`device-inspector` 的截图与元素面板布局；`workflow` 的节点与浮层几何（圆角与尺寸留待变更 10）

## 登记为后续变更的输入（本变更不做）

- `PageFlowVueFlow.vue:806` 的 `border-radius: 14px` 对称圆角 → 变更 10 `consolidate-radius-scale`