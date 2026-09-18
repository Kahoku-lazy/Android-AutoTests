## Why

修一类**静默失效**与一类**零引用残留**：① `element-locator/components/PageElementsWorkbench.vue` 用裸 `stripe` 而 `AppTable` 的 prop 是 `striped`（默认 `false`），该属性被当作未声明 attr 丢弃，导致这张表**斑马纹静默不渲染**（同模块其余 4 处均正确用 `:striped`）；② 两个组件全仓**零引用**：`ai-assistant/components/AgentModelConfig.vue`（78 行）、`workflow/components/WorkflowFileBrowser.vue`（550 行）。本变更不改变 spec 级行为，故 `skip_specs`。

## What Changes

- `PageElementsWorkbench.vue` 的裸 `stripe` → `:striped="true"`（对齐既有正确写法），恢复斑马纹
- 删除 `AgentModelConfig.vue` 与 `WorkflowFileBrowser.vue`
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §十 与 §八·批次 D
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 3 · `purge-frontend-dead-code`
- 既有要求：`openspec/specs/frontend-l0-design-tokens/spec.md`「无引用样式文件不得留在源码树」

## Capabilities

（无 spec delta —— `.openspec.yaml` 置 `skip_specs: true`）

## Impact

- `frontend/src/modules/element-locator/components/PageElementsWorkbench.vue`（1 行）
- 删除 `frontend/src/modules/ai-assistant/components/AgentModelConfig.vue`、`frontend/src/modules/workflow/components/WorkflowFileBrowser.vue`（恢复方式：`git show HEAD:<path>`）
- 观感变化：element-locator 页面元素表首次出现斑马纹
- 不影响：`AppTable` 的 `striped → ep stripe` 映射契约、其余模块表格、接口与数据

## 明确移出本变更范围（本轮实测确认，作为后续输入）

- `report-generator/constants.ts` 的 **17 个零引用导出**（`TABLE_COLUMNS` / `CHART_CANVAS_HEIGHT` / `FILTER_DEBOUNCE` / `STATUS_BADGE_CLASS` 等）：本项目**不使用分号**，需要按"下一个顶层 `export` / 注释块起始"为界删除，而不是按 `;` 判定。本轮首次尝试因终止条件错误损毁了该文件，已 `git checkout` 完整恢复（29 导出 / 162 行与 HEAD 一致）。该清退与下述令牌/死 CSS 一并另开批次
- 94 个已声明未引用令牌、逐条死 CSS 规则（`.dot-board` / `.fw-desc` / `.label-with-help` 等）
- `dashboard` / `report-generator` 的模块令牌文件化（含页根统一，来自变更 13 的发现）
- `--case-*` 色相（blue vs teal）等设计选择 → 待确认