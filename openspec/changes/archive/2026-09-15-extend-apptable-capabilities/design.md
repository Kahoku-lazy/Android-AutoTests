## Context

`AppTable` 现为 97 行的扁平列映射器（`elColumns` computed，仅一级 `el-table-column` + `#cell-<prop>` 插槽）；3 处例外各自需要的额外能力见 proposal。3 处的实际用法：`PageElementsPanel` 有 `dump` / `OCR` 两级表头 + 40px 自定义表头复选框列 + `height="100%"` + `header-cell-style` + `@row-click`；`StructureAnalysisPanel` 7 列扁平 + `height` + `@row-click`；`PageElementsWorkbench` 用 `tableRef.value?.$el` 取 DOM 做 `scrollIntoView`，并用 `setCurrentRow` 同步选中。

## Goals / Non-Goals

**Goals:**

- 让 `AppTable` 覆盖分组表头 / 自定义表头 / 底层实例 / 属性透传，使 3 处例外可以退役
- 迁移后三表的外观与交互保持（列宽、行点击、选中高亮、表高）

**Non-Goals:**

- 不为三表新增共享表格组件或新的表格变体
- 不改 `AppTable` 既有 props / 插槽的语义与默认值
- 不改三表的列集合、列宽与业务逻辑（只换渲染载体）
- 不引入 EP 的 `type="selection"` 选择列（三表用的是自定义复选框 + 自管选中集合，保持原语义）

## Decisions

**D1 · 用渲染函数生成列 VNode，而不是在模板里递归**

分组表头需要嵌套 `el-table-column`，模板递归要额外拆一个递归子组件；用 `h(ElTableColumn, ...)` 的 `buildColumns` 递归既支持任意层级、又不新增文件。模板侧用 `<component :is="col" />` 渲染生成好的 VNode（Vue 3 支持的用法），并加注释说明意图。

**D2 · 列 VNode 的 `key` 取 `col.key ?? prop ?? \`col-${index}\``，而不是 `col.prop`**

选择列这类「无 `prop`」的列在旧实现里 `:key="col.prop"` 会得到 `undefined` 并触发重复 key。新实现给每列稳定 key；同时允许消费者显式传 `key`。

**D3 · 表头插槽命名沿用 `#header-<prop>`，与既有 `#cell-<prop>` 对称**

选择列的复选框放在表头，需要一个按列名定位的表头插槽；与现有 `cell-<prop>` 命名保持同一构词法，消费者无需记两套规则。

**D4 · 透传用 `inheritAttrs: false` + `v-bind="$attrs"`，不逐个声明 props**

`height` / `header-cell-style` / `@row-click` / `row-key` 等 EP 原生属性逐个声明会不断膨胀；透传让消费者直接用 EP 的 API。已声明的 props（`rowClassName` / `tableLayout` 等）仍由显式绑定优先。

**D5 · 暴露的是 `tableRef` 而非铺开 `scrollTo` / `setCurrentRow`**

铺开方法会随 EP 版本漂移；暴露底层实例让消费者直接用 EP API，代价是调用处要写 `tableRef.value?.tableRef?.$el`（两段同名，已在注释说明）。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无（`ElTableColumn` / `TableInstance` 均来自既有 element-plus）

## Risks / Trade-offs

- [渲染函数生成的列 VNode 若 `key` 不稳定会导致列复用时插槽错位] → key 取 `col.key ?? prop ?? col-<index>`，并在迁移后核对列内容
- [`v-bind="$attrs"` 会把父级 `class` / `style` 也带给 `el-table`，与内置 `class="ac-table"` 合并] → Vue 的 class/style 合并语义安全；迁移后核对 `.ac-table` 主题样式仍生效
- [暴露底层实例让消费方绕过封装] → 这是有意为之（spec 已把「底层实例取用」列为 `AppTable` 应覆盖的能力），并在 design 登记
- [三表迁移涉及模板大改，易漏列或漏事件] → 逐表迁移后跑 `vue-tsc` + `git diff` 逐行核对，并留三档宽度浏览器核验项

## Migration Plan

- 无数据迁移；回滚为 revert 本变更提交
- 顺序：先扩 `AppTable`（4 个既有消费方不受影响）→ 逐表迁移（PageElementsPanel → StructureAnalysisPanel → PageElementsWorkbench）→ 每步跑 typecheck
