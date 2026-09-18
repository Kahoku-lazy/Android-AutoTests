## Why

全局 `frontend/src/style.css` 给每个表格单元格上了不透明底色并带 `!important`，导致任何把选中态画在行（`tr`）上的实现都被永久遮盖 —— `device-inspector` 的元素面板与结构面板的选中行高亮**实际完全不渲染**，属功能可见性缺陷。同一文件又把行分隔线画成 `var(--app-border-light)`（解析为 `#ffffff`），在白色纸面上不可见却占据 1px；共享层与 `device-pool` 再各自叠加一套表头与线型，使同一套 `AppTable` 在不同模块读起来不像同一套语言。

## What Changes

- 新增 L4 表格**行状态共享契约**：选中行统一由 `AppTable` 的 `row-class-name` 返回 `is-selected`，共享规则把底色画在 `> td.el-table__cell` 上并带 `!important`（对齐全仓唯一可用的既有写法 `element-locator/components/PageElementsWorkbench.vue:326`）
- 在 `tokens.css` 登记行选中底色组件令牌（`--comp-table-row-accent` 派生 `--comp-table-row-selected-bg`），模块可覆写强调色而不复制表达式
- 迁移三处行选中实现到该契约并删除各自私有规则：`device-inspector/PageElementsPanel.vue`（`pep-row--selected`）、`device-inspector/StructureAnalysisPanel.vue`（`sap-row--selected`）、`element-locator/PageElementsWorkbench.vue`（`page-row--active`）
- 把「表格不画可见网格线」写成**语义正确的声明**：全局 `td` 下边框由白色改为 `transparent`（保持 1px 占位，视觉零变化），共享层两条被全局 `!important` 覆盖的死声明按同一口径处理/删除
- 统一表头排版为单一来源：`device-pool` 移除 `16px / 800` 覆盖与 7 色分栏底线、行间彩色虚线、列间白色分隔线，回到全局 `--app-size-xs` / 700 / uppercase 与共享表纸口径
- **BREAKING**：无。纯前端视觉与共享样式契约，不涉及接口、路由、鉴权或数据

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.1 / §3.3 / §3.4（P0-1）与 §八·批次 A
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 1 · `fix-l4-table-render`
- 表格角色与表纸口径：`openspec/specs/frontend-l4-data-surface/spec.md`、`openspec/changes/adopt-subpages-doodle-p0/specs/frontend-doodle-sketch-table/spec.md`
- 主题约束：`frontend/AGENTS.md`、`.agents/skills/doodle-craft/references/components.md`
- 说明：`dev_docs/` 下无对应 PRD/ARCH/UI 编号文档，本变更属视觉一致性与渲染正确性修复，不改业务接口

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`：新增两条要求 —— 「表格行状态必须可见」（行状态底色画在单元格上、唯一类名 `is-selected`）与「表格不画可见网格线且表头排版单一来源」

## Impact

- 共享层：`frontend/src/shared/styles/tokens.css`（新增 2 条组件令牌）、`frontend/src/shared/styles/workbench-theme.css`（新增行选中共享规则、清理被覆盖的死声明）
- 全局层：`frontend/src/style.css`（表格 + 表头的网格线/底线声明）
- 模块层：`frontend/src/modules/device-inspector/components/PageElementsPanel.vue`、`frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue`、`frontend/src/modules/element-locator/components/PageElementsWorkbench.vue`、`frontend/src/modules/device-pool/DevicePoolView.style.css`
- 观感变化：`/devices` 表格（表头字号回 12px、去除彩色分栏底线与彩色虚线行线）；`/inspector` 两个面板的选中行由「不可见」变为「可见」。其余表格为视觉零变化
- 测试范围：`cd frontend && npm run typecheck`、`npm run lint:styles`、`npx vite build --mode development`，以及四个页面的浏览器目视回归
- 不影响：`AppTable` 的列生成/分页/校验能力、接口与数据、表格以外的组件