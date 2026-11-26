## MODIFIED Requirements

### Requirement: Cards and grids reuse shared parts

可复用数据块（图表卡 / 表格卡 / 指标卡 / 认证卡 / 条目卡）MUST 使用 shared 卡片零件（`AppCard` / `KpiCard` / `SketchCard`）；卡片网格 MAY 由模块自建（`grid-template-columns`），SHALL NOT 为此抽出共享网格组件，也 SHALL NOT 另建与 shared 卡壳视觉不一致的私有默认卡样式。

#### Scenario: Metric row reuses the shared KPI card

- **WHEN** 页面渲染指标行
- **THEN** 卡片来自 `shared/components/KpiCard.vue` 或其薄包装
- **AND** 不出现模块私有的清新风统计卡默认样式

#### Scenario: Module-owned grid is allowed

- **WHEN** 页面需要卡片网格布局
- **THEN** 网格由模块样式自建，不要求抽共享网格组件
- **AND** 卡片外观仍来自 shared 零件，主题锚点仍在页面根上
