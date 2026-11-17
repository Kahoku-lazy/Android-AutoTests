# 设计：BUG 表对齐设备表的列结构

## Context

现状（`/bugs`）：`AppTable` 渲染 7 列，`:border="true"` 画列线，列头纯文字；首列 `<code class="bug-no">`；「创建时间」另有独立列；操作列是 `DoodleBtn`（已是墨色描边 + 位移硬影）；表纸 `accent="var(--c-runner)"` 带桃色硬影。表头底色是本页特有的柠黄调（`color-mix(--c-dashboard 22%)`），行底色也偏黄。

约束：

- `bug-manager/AGENTS.md` 红线：不得自造第二套卡片 / 表格 / 抽屉皮肤 → 只能给共享 `AppTable` 加列结构与页面作用域样式。
- `frontend-doodle-sketch-table` 刚在上一单写了「设备页是硬阴影的登记例外」；扩到 BUG 页必须把这个例外改写成登记页清单，不能悄悄加第二处覆盖。
- 共享 `.sketch-sheet` 仍有 8 处消费方，任何共享层改动都会波及。

## Goals / Non-Goals

**Goals**：列头图标、首列身份单元、去列线、去硬影；其余（筛选、分页、抽屉、按键）零改动。

**Non-Goals**：不动分类 Tab / 状态下拉 / 关键字 / 显示行数 / 分页位置；不动表头柠檬黄底与行底色；不动按钮语言（继续用 `DoodleBtn`，不引入设备页的 `.act-pill`）。

## Decisions

### D1 身份单元吃掉「创建时间」列：7 列 → 6 列

首列 = 图标圆 + `BUG-0057`（主）+ `2026-11-17 14:45`（副），并移除独立「创建时间」列。

理由：设备表首列的副行放的是**没有专门列**的辅助标识（序列号 / 地址）。BUG 表里能与编号并列、且不必再占一列的就是时间；两处都显示同一时间会让表格多一列、读起来像两个口径。

*代价*：少一个可单独排序/扫读的时间列。若要保留，只需把副行换成其它字段并恢复该列 —— 改动集中在 `BUG_TABLE_COLUMNS`。

### D2 图标圆里放 emoji 🐞，不新增 SVG 图标

共享图标库里没有 bug 图标（页头 `icon: "bug"` 走的是 lucide CDN，表格单元格里不方便再用）。空态与页头已经用 🐞，首列沿用同一符号，省掉一个新资源。

### D3 关掉 `border`，不新增替代线

`:border="true"` 画的是竖直列线，与 `frontend-l4-data-surface`「不画可见列线」相悖，也让表看起来像 Excel。关掉后行分隔仍由页面既有的 `border-bottom: 1px` 与斑马/行底色承担。

### D4 去影写在 `.bug-workbench` 作用域

```css
.bug-workbench :deep(.sketch-sheet) {
  box-shadow: none;
}
```

与设备页同构：只在本页去影，共享声明不动。同时把「无影页清单」登记进 `frontend-doodle-sketch-table`，登记为设备页 + BUG 页。

### D5 列宽跟着身份单元调

`bug_no` 从 118 加宽到 190（图标圆 28px + 两行文本），其余列宽不动；`title` 仍是 `minWidth: 260` 的弹性列，表宽变化由它吸收。

## Risks / Trade-offs

- [少一个创建时间列，扫读时间要往首列副行看] → 副行用等宽小字、与主行左对齐；宽度足够时不换行。
- [去列线后长表格的分列感变弱] → 已有行底色与表头底色区分；标题列左对齐、状态居中，列边界仍可读。
- [去影后桃色强调消失] → 表纸描边仍是共享 1px 灰；KPI 卡与分布图仍带 `--c-runner`，模块色没丢。

## Migration Plan

纯前端、无数据迁移。回退 = 还原 `BUG_TABLE_COLUMNS`（7 列 + 无 icon）、恢复 `:border="true"`、删掉去影那一行。三处互不依赖。

## Open Questions

无。
