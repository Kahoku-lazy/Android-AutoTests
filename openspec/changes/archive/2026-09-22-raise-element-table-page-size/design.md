## Context

- 行数的唯一登记处是 `frontend/src/modules/device-inspector/constants.ts:4-5`（`PAGE_SIZE_OPTIONS = [7]`、`DEFAULT_PAGE_SIZE = 7`）；面板在 `StructureAnalysisPanel.vue:62-65` 取用。
- 表格容器定高：`StructureAnalysisPanel.css:88-94` 的 `.sap-table-body` 为 `flex: 1; min-height: 0`，表格传 `height="100%"`；行数填不满容器时，余下部分就是可见空白。
- 共享 `usePagination` 只按 `pageSize` 切片，不感知容器高度（`shared/composables/usePagination.ts:31-43`）。
- `openspec/specs/frontend-l4-data-surface/spec.md:46-50` 明确不钉具体行数：`PAGE_SIZE_OPTIONS` 只须登记单一取值且与默认行数相等，具体行数由 `device-inspector-page` 定义 —— 因此本单只动 `device-inspector-page` 与模块常量。
- 页面不提供「显示行数」选择器，选项集当前是登记值而非可选项。

## Goals / Non-Goals

**Goals:**

- 让元素表在常见窗口高度下把结构栏的空白用起来（每页 12 行）。
- 保持行数的唯一真相源（模块 `constants.ts`），规格与代码同步。

**Non-Goals:**

- 不做「按容器高度自适应行数」。
- 不改列宽 / 间距、不改表格定高策略、不恢复「显示行数」选择器。
- 不改后端与分层数据口径。

## Decisions

**D1 固定 12 行，不按容器高度自适应。** 用户诉求是「把这些空白用起来」，12 是用户给定的目标值；自适应需要 `ResizeObserver` 与行高测量，会让「每页行数」不再能从模块常量读出，并引入第二处行数决策。备选：自适应 → 否决（超出诉求，且与 `frontend-l4-data-surface` 的「行数来自模块常量」相冲突）。

**D2 选项集同步为 `[12]`，仍然只有一项。** `PAGE_SIZE_OPTIONS` 与 `DEFAULT_PAGE_SIZE` 若不一致就成两处口径；页面不渲染选择器，选项集只作为登记值存在。

**D3 行数变多不改变勾选口径。** 表头全选仍只作用于当前页所示行，跨页勾选仍由 store 全量持有；变的只是「当前页」有多少行。

**D4 用例断言分页文案与首屏行数，不依赖 Element Plus。** 单测环境（`vite.config.js:14-29`）不为 `el-*` 注册按需组件，也是本仓既有做法：stub 掉表格与 `el-*`，断言面板自身渲染的分页文案（「第 1 / 3 页 · 共 27 条」）与表格收到的行数（12）。这样测的是本单真正改动的「行数接线」，而不是 Element Plus 的渲染。

## 模块防火墙自检

- **前端 HTTP 出口**：无新增调用，不改 `api.ts`。
- **共享件**：不改 `usePagination` / `AppTable`；只改模块常量与模块内注释。
- **样式**：不动 CSS，列宽与间距规格保持原样。

## Risks / Trade-offs

- [窗口较矮时 12 行超出容器高度] → 表格自身 `height="100%"` 会内部滚动，不会溢出屏幕；既有「空表留在可视区域内」的要求不受影响。
- [12 行约 800px（行高由 48px 缩略图决定），更矮的窗口下仍会留少量空白] → 属窗口尺寸差异，不引入自适应机制。
- [规格里的分页示例随行数变化] → delta 已同步为「12 行一页、27 行 3 页」。

## 人工验收

- Agent 无浏览器控制，无法目视「12 行正好用满结构栏」；该项由用户在本机 `/inspector` 页目视确认（每页行数、分页文案与翻页）。自动化侧以挂载面板的用例覆盖「首屏 12 行 + 分页文案」。
