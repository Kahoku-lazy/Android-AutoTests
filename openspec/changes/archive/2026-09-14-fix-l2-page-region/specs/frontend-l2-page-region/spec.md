## Purpose

定义前端 L2 区域（页头区 / 页面根区）的可见行为契约：页头内的操作按钮必须保留其语义色与主题变体色，页头内容在放不下时只能收敛、不得溢出侵入正文，页头的层叠声明必须实际生效，且每一个 L2 页面根都必须提供工作台主题作用域，使页头按钮与页内共享组件呈现一致的 Doodle Craft 主题外观。

## ADDED Requirements

### Requirement: Header action buttons keep their semantic colors
页头（`.wb-header`）内的按钮 SHALL 保留其语义色与主题变体色：`type="primary"` 呈现主色（`var(--c-dashboard)`）、`type="success"` 呈现成功色（`var(--c-device)`）、`type="danger"` 呈现危险色（`var(--app-status-danger)`）、`wb-btn--sunset` 呈现其变体色；系统 MUST NOT 把页头内的按钮统一压成白底而丢失语义区分。

#### Scenario: Page header primary button shows the spec color
- **WHEN** 用户打开页头带 `type="primary"` 按钮的页面（如 `/cases`）
- **THEN** 该按钮呈现 `var(--c-dashboard)` 底色与墨色边框，与正文里的 primary 按钮同色

#### Scenario: Page header variant button shows the variant color
- **WHEN** 用户打开仪表盘 `/dashboard`
- **THEN** 页头「刷新」按钮呈现 `wb-btn--sunset` 的 sunset 底色，而非白底

#### Scenario: Page header default button stays default
- **WHEN** 用户打开 `/devices` 或 `/inspector`
- **THEN** 无类型、无变体的页头按钮仍呈现默认皮肤（`var(--app-bg-card)` 底色 + `var(--ink)` 边框）

#### Scenario: Hover keeps the button's own color family
- **WHEN** 用户把指针移到页头内任一按钮上
- **THEN** 该按钮的 hover 底色属于其自身语义/变体色系（无类型 → `var(--c-dashboard)`、danger → `var(--app-btn-hover-danger)`），不被统一改成同一种底色

### Requirement: Header content never overlaps page content
页头 SHALL 在常规宽度下保持 `var(--app-topbar-h)`（96px）高度并与侧栏 header 底边对齐；标题与副标题 MUST 单行省略号截断；动作区放不下时 MUST 换行并由页头增高容纳，页头 MUST NOT 让自身内容溢出其盒子或覆盖正文内容区。

#### Scenario: Long title and subtitle truncate instead of wrapping
- **WHEN** 在 768px–1024px 宽度打开副标题较长的页面（如 `/dashboard`）
- **THEN** 标题与副标题各占一行并以省略号截断，页头高度仍为 96px

#### Scenario: Header with many actions does not overflow
- **WHEN** 在 768px–1024px 宽度打开动作区元素最多的页头（如 `/workflow/prototypes/:prototypeId`，含返回/导入/导出/覆盖开关/保存/状态）
- **THEN** 页头不产生自身溢出（内容高 ≤ 页头高），必要时页头增高把正文下推，正文首屏内容不被遮挡

#### Scenario: Alignment with sidebar header survives
- **WHEN** 在 ≥1280px 宽度打开任一工作台页面
- **THEN** 页头高度等于侧栏 header 高度（同为 `var(--app-topbar-h)`），两者底边对齐

### Requirement: Header stacking declaration is effective
页头的层叠控制 MUST 实际生效：`.wb-header` 的计算样式 `position` MUST NOT 为 `static`，其 `z-index` MUST 参与层叠；系统 MUST NOT 保留对 static 元素无效的层叠声明。

#### Scenario: Computed position participates in stacking
- **WHEN** 在浏览器中检查任一工作台页面 `.wb-header` 的计算样式
- **THEN** `position` 为 `relative`、`z-index` 为 `10`，页头绘制在正文内容之上

### Requirement: Every L2 page root provides the workbench theme scope
每一个 L2 页面根 SHALL 携带工作台主题作用域（`.wb-shell`，或既有等价锚点 `.workflow-workbench`），使页头按钮与页内 `AppCard`/`AppTable`/`AppTabs` 呈现 Doodle Craft 主题；系统 MUST NOT 出现同一模块内列表页与详情页使用同一共享组件却外观不一致。

#### Scenario: Report list and report detail share one component appearance
- **WHEN** 用户先打开 `/reports`（列表页），再打开 `/reports/{runId}`（详情页）
- **THEN** 两个页面里的 `AppTable` / `AppCard` 呈现相同的 Doodle Craft 边框、底色与圆角，无 Element Plus 默认外观回退

#### Scenario: Theme scope present on all workbench page roots
- **WHEN** 逐一打开 report-generator 详情、case-manager、element-locator 与 workflow 原型列表的页面
- **THEN** 每个页面根都在带 `.wb-shell`（或 `.workflow-workbench`）的祖先之内，页头按钮与页内卡片均为主题皮肤

### Requirement: L0 and L1 contracts unchanged
本变更 MUST NOT 改变 L0「视口固定 + 内层滚动」策略与 L1 主区结构：页面根仍是 `.main-content__body` 的直接子元素，滚动仍发生在既有滚动容器内，`keep-alive` 的 `:max="5"` 与 `:key="route.path"` 保持不变。

#### Scenario: Scroll guard reports no new warning
- **WHEN** 开发环境打开任一内容超过一屏的工作台页面
- **THEN** 控制台无新增 `[scroll-guard]` 告警，且未出现整页双滚动条

#### Scenario: Page root contract preserved
- **WHEN** 检查变更后各页面 DOM
- **THEN** 页面根仍为 `.main-content__body` 的直接子元素，页面缓存仍按 `route.path` 生效
