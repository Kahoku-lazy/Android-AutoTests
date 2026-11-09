## Context

- 报告页分区头由 `.doc-section__title` + 共享 `FilterTabs` 组成；表格用 `AppTable`，状态列渲染 `.badge` + `STATUS_LABEL_MAP`。
- `STATUS_LABEL_MAP` 有两份口径（`api.ts` / `constants.ts`，已登记），都缺 `cancelled`，导致界面上直接显示英文 `cancelled`。

## Goals / Non-Goals

**Goals：**

- 过滤标签、状态标签、表格字体三处收敛；`cancelled` 中文化；工具条间距放松。

**Non-Goals：**

- 不动查询参数、分页、行点击跳转、过滤项数量与统计口径。

## Decisions

### 1. 只覆盖报告页的 FilterTabs，不改共享组件

用 `.report-status-tabs :deep(.filter-tab)` 在报告页作用域内换皮，其它页面（BUG 单等）保持现有胶囊；避免一次改动波及全站。

### 2. `cancelled` 同时补两份映射

模块 AGENTS 规定双口径是已登记收敛项、不得新增第三份；因此两份都加 `cancelled: "已取消"`，徽标类归到 `badge-stopped`（灰）。

### 3. 表格字体走共享皮肤 + 局部字号

表头已由共享 `.ac-table` 定义为 12/600 次要色；这里只把单元格字号统一为 `--app-size-sm`，时间/耗时加等宽数字与次要色。

## 模块防火墙自检

- 只改 `frontend/src/modules/report-generator/**`，未动 `shared/`。

## Risks / Trade-offs

- [过滤标签改为描边卡后与 BUG 页胶囊不一致] → 这是有意的页面级差异；若后续要统一，再抽 `FilterTabs variant`。
- [状态文案变化影响断言] → 已跑 `tests/report-generator` 与 `tests/task-list`（152 用例）通过。
