# 已知缺口与已退役写法（别照抄）

两张**反面清单**：上面是现存缺陷（对齐代码时核出的，按默认口径做新页面时不要复制这些行为）；下面是已退役 / 代码里已不存在的写法（历史文档出现过，别再照抄）。

> 缺口要修需单独立项（走 openspec），修完回来删掉对应行。

## 一、已知缺口登记

| # | 缺口 | 实际影响 | 位置 |
|:--:|------|----------|------|
| 1 | 骨架屏 shimmer 的两级灰令牌取到**同一个值** | 加载骨架是纯灰块，没有流动光效 | `--comp-skeleton-shimmer-base` / `-faint` |
| 2 | 侧栏 `prefers-reduced-motion` 只关 transition、**未置 `transform: none`** | 系统开"减少动效"时侧栏卡片仍会歪斜 / 抖动 | `AppSidebar.style.css` |
| 3 | `ErrorState` 无 `role="alert"` | 读屏软件不播报"加载失败" | `patterns/ErrorState.vue` |
| 4 | `FilterTabs` 无 `role="tab"` / `aria-pressed` | 键盘与读屏无法识别成一组互斥选项 | `FilterTabs.vue` |
| 5 | 多处动 `transform` 但**无减动效降级**：`.wb-shell .el-card` hover 位移 · `.ac-tabs` · `wb-btn` · 输入框 focus 环 · `ErrorState` 按钮 · `FilterTabs` | 开"减少动效"时这些位移动效仍会播 | 见各文件（`motion.css` / `workbench-theme.css` / `style.css`）|

## 二、已退役 / 不存在（别再照抄）

| 旧写法 | 现状 |
|--------|------|
| `.card` 拍立得卡片、`.card-info` 纸艺卡片 | **代码里已无实现**；现役是 `AppCard` / `SketchCard` / `KpiCard` / `DoodleNote` |
| 按钮"11px 字" | 违反最小 12px 硬规则；字号取 `--app-size-*` |
| 表格 `1px dashed` 行分隔线 | 现行规范**不画网格线**，用 `transparent` 占位 |
| 弹窗标题"Caveat 20px" | 无此字体也无此声明；标题排版走 EP 默认 + `--el-font-family` |
| `FilterTabs` 激活底 `#fff` + `2px` 墨框 | 实际是底 `--app-bg-subtle` + `1px` 墨框 |
| 面包屑挂 `WorkbenchHeader` 的 `#nav` 槽 | 页头没有 `#nav` 槽；面包屑放 `.doc-body` 顶部 |
| 分页"只显示页码 + 箭头" | 实际文案「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页 |
| 纸面"点阵纸纹" | 已作废：暖白实色 + 主区稀疏涂鸦 |
