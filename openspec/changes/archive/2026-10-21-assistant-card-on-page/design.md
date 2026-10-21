## 上下文

平台小助手页 `index.vue` 当前结构是 `section.doc-section.duty-section` 包住区块标题行 + `AgentRouteCard` 网格。`.doc-section` 提供白底、2.5px 墨边、阴影与全宽内边距，而内部只有一张 `width: fit-content` 的线路卡，导致右侧大面积白色空白。`index.style.css` 的 `.duty-section` 与 `.filter-count` 只被这一页使用。

## 目标 / 非目标

- 目标：去掉 `.doc-section` 外框与重复的区块标题/计数行，线路卡直接贴页面背景，卡片宽度约 300px。
- 非目标：不改页面页头、不改线路卡内部头像/两行身份/配置按钮结构，不改任务清单页的 `.doc-section` 区块，不改接口。

## 决策

- 直接把 `ErrorState` 与 `.route-card-grid` 放到 `.ai-workbench .doc-body` 下，不再包 `section`。`doc-body` 已有 flex 列布局、间距与滚动，足够承载单卡。
- 删除 `index.style.css` 的 `.duty-section` 与 `.filter-count`；`.ai-workbench .doc-section__header` 保留，因为任务清单页的 `TaskBoard` 仍在同一 `ai-workbench` 下使用它。
- 卡片宽度由 `width: fit-content` 改为 `width: 300px; max-width: 100%`；网格列宽从 `minmax(min(100%, 220px), max-content)` 调到 `minmax(min(100%, 300px), max-content)`，保证桌面 300px、窄屏收缩。
- 不用 `max-width: 300px` 的容器包卡片：直接给卡片定宽，少一层 DOM，空白自然消失。

## 风险 / 权衡

- 卡片变宽后文字区更空，但头像仍按两行文字高度测量，不会错位；超长名称仍按既有省略规则处理。
- 去掉区块标题后，页面只剩页头「平台小助手」，层级更扁；这是产品要求，页头 URL 与标题仍可识别当前页。

## 迁移计划

- 纯前端布局改动，无数据迁移；回滚即恢复 `index.vue` 的 section/标题行与卡片宽度。

## 开放问题

- 无。
