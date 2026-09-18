## Why

共享骨架块 `.doc-section` 的皮肤被两处以**裸选择器**重定义，且与全局规则**同权重 (0,2,0)**，谁生效取决于样式注入顺序：`ai-assistant/EvaluatorTab.vue:581` 用 `1px solid var(--ai-bg-subtle)` 替换全局的 2.5px 墨线，使**评测中心的粗墨纸边实际消失**；`report-generator/index.vue:375-380` 重复声明了全局已提供的背景/描边/圆角/阴影并把标题放大到 24px（全局 16px）。另有两处行内 `style="padding:0"` / `"padding:14px 16px 0"` 覆写分区内边距，以及 `ai-assistant/index.style.css:39` 一处裸 `.doc-section__header` 重定义。结果是同一骨架块在不同模块读到不同的皮肤。

## What Changes

- `report-generator/index.vue`：删除重复全局属性的模块级 `.doc-section` 皮肤，只保留本页真实差异（标题的手绘波浪下划线）并以 `.report-workbench` 限定作用域；把两处行内 padding 覆写改为作用域内类选择器
- `ai-assistant/EvaluatorTab.vue`：删除裸 `.doc-section` / `.doc-section__title` 重定义，恢复全局 2.5px 墨色纸边与统一标题字号
- `ai-assistant/index.style.css`：`.doc-section__header` 的覆写改为 `.ai-workbench` 作用域，且只保留真实差异（`align-items: baseline` / `flex-shrink: 0`）
- 顺带修掉 `report-generator` 里 `.doc-tag` 的 `1.5px solid var(--app-border-light)`（白底白框 → 标签描边不可见）：该重定义整体删除，改用全局 `.doc-tag` 皮肤
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §4.4 与 §八·批次 B
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 2 · `converge-content-section-container`
- 既有要求：`openspec/specs/frontend-l3-container/spec.md`「Container overrides are scoped by a module modifier」（本变更把同一原则覆盖到 `.doc-section`）；`openspec/specs/frontend-l3-content-block/spec.md` 定义 `.doc-section` 的角色与全局皮肤

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l3-container`：新增要求「共享骨架块不得无作用域重定义」

## Impact

- `frontend/src/modules/report-generator/index.vue`（样式层 + 两处模板行内 style）
- `frontend/src/modules/ai-assistant/EvaluatorTab.vue`（删除两条裸重定义）
- `frontend/src/modules/ai-assistant/index.style.css`（header 覆写加作用域）
- 观感变化：`/reports` 分区标题由 24px 回到全局 16px、分区内边距回到全局值、`doc-tag` 描边变为可见墨线；`doc-section` 的波浪下划线装饰保留；`/ai-assistant/evaluator` 恢复 2.5px 墨色纸边
- 不影响：`dashboard` 的 `.doc-section--board` 私有 modifier（已合规）、`AppCard` / `AppTable` 皮肤、接口与数据

## 登记为后续变更的输入（本变更不做）

- `report-generator` 的 `.detail-tabs` 重写 `AppTabs` 皮肤、`!important` 收敛 → 变更 8 / 15
- `EvaluatorTab` 的 81 处行内 style 与圆角字面量 → 变更 10 / 15