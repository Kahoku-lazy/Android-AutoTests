## Context

- 上一单 `2026-09-22-raise-element-table-page-size` 把行数定为 12 并已归档；行数的唯一登记处是 `frontend/src/modules/device-inspector/constants.ts:3-5`。
- `openspec/specs/frontend-l4-data-surface/spec.md:46-50` 不钉具体数字，只要求「选项集只登记单一取值且与默认行数相等」；具体行数由 `device-inspector-page` 定义。
- 用户复核真实窗口后给出新目标值 14。

## Goals / Non-Goals

**Goals:**

- 把元素表首屏行数定为 14，规格与实现同步。

**Non-Goals:**

- 不做按容器高度自适应（理由同上一单 D1：会引入第二处行数决策）。
- 不改列宽 / 间距、不改勾选口径、不改后端。

## Decisions

**D1 固定 14 行。** 同上一单 D1：自适应需要 `ResizeObserver` 与行高测量，会让行数不再能从模块常量读出。

**D2 选项集同步为 `[14]`。** `PAGE_SIZE_OPTIONS` 与 `DEFAULT_PAGE_SIZE` 必须一致，否则成两处口径。

**D3 用例改用 40 条元素。** 27 条在 14 行下只有两页（14 + 13），测不到「中间页满页」；40 条给出 14 / 14 / 12 三页，同时覆盖满页与末页残余。

## 模块防火墙自检

- **前端 HTTP 出口**：无新增调用。
- **共享件**：不改 `usePagination` / `AppTable`；只改模块常量与模块内注释。
- **样式**：不动 CSS。

## Risks / Trade-offs

- [14 行约 900px（行高由 48px 缩略图决定），窗口更矮时超出容器] → 表格自身 `height="100%"` 会内部滚动，不溢出屏幕。

## 人工验收

- Agent 无浏览器控制，无法目视确认「14 行是否正好用满结构栏」；该项由用户在本机 `/inspector` 页确认。自动化覆盖「首屏 14 行 + 分页文案 + 翻页 + 末页残余」。
