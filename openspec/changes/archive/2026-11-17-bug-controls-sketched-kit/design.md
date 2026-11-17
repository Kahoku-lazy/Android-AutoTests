# 设计：BUG 控制区复用 Sketched UI Kit

## Context

`shared/styles/sketched-kit.css` 已提供完整的手稿控件分类（输入框四态 + 按钮五态 + `.sketch-field` 字段骨架），规格见 `doodle-craft/references/components/sketched-ui-kit.md`。BUG 页当前是两行控制区（分类 Tab 独占一行）+ 主线实线控件；表格用 Element Plus 默认内边距且贴边。

## Goals / Non-Goals

**Goals**：一行控制区、手稿皮肤、去掉重复计数、表格留白与字号达标。

**Non-Goals**：不动 KPI 与分布图、不动「显示行数」三档、不改筛选/分页/抽屉逻辑、不新写控件皮肤。

## Decisions

### D1 只挂 `.sketch-kit`，不写新控件样式

搜索框、状态下拉、同步键、翻页键都放进挂了 `.sketch-kit` 的控制区里，由 kit 直接给虚线描边与五态。模块内只保留宽度与排布，不再复制边框/阴影/焦点规则。

*替代方案*：在 `index.style.css` 里另写一套虚线输入框——重复实现，且虚线口径必须由白名单样式表声明，模块里写会违反线型白名单。

### D2 分类 chip 用 `FilterTabs` 原样，只挪位置

`FilterTabs` 的选中态样式（本页已用 `:deep` 定制成模块色）保持不变，只是从独占一行移进控制行最左。控制行 `align-items: flex-end`，让没有字段标题的 chip 与输入框底边对齐。

### D3 翻页键换成 `DoodleBtn tone="paper"`

kit 只接管 `.doodle-btn`，所以翻页键必须换成共享 `DoodleBtn` 才吃到描边态，原生 `<button class="page-nav-btn">` 不在 kit 覆盖范围内。禁用态由 `DoodleBtn` 的 `disabled` 走 kit 的淡虚线规则。

### D4 留白用容器内边距 + 单元格内边距两层

分区 `.bug-table-section` 给左右与底部 `--app-space-md`，表格因此不再贴边；单元格 `padding: 16px`、表头 `12px 16px`，行高由首列两行撑到 ~84px。字号：首列编号 16px（`--app-size-md`）、时间 14px（`--app-size-sm`），正文维持 14px。

### D5 删掉「共 N 张 BUG 单」

它与分页文案「共 N 条」是同一口径，两处并存会让读者以为统计不同。

## Risks / Trade-offs

- [控制行里同时有 chip、带标题输入框与按钮，纵向基线不齐] → 用 `align-items: flex-end` 统一底边；窄屏整行换行。
- [字号放大后一行信息变少] → 行高与留白是需求方明确要的；表格本来就在 `.doc-body` 内纵向滚动。
- [翻页键换成 `DoodleBtn` 后尺寸变大] → 与 kit 的 34px 高度统一，属于要的效果。

## Migration Plan

纯前端。回退：把控制区拆回两行、把 `DoodleBtn` 换回原生 button、删掉内边距覆盖即可，改动集中在 `index.vue` 与 `index.style.css`。

## Open Questions

无。
