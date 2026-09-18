## Purpose

定义前端 L2 区域（页头区 / 页面根区）的可见行为契约：页头内的操作按钮必须保留其语义色与主题变体色，页头内容在放不下时只能收敛、不得溢出侵入正文，页头的层叠声明必须实际生效，且每一个 L2 页面根都必须提供工作台主题作用域，使页头按钮与页内共享组件呈现一致的 Doodle Craft 主题外观。

## Requirements

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

### Requirement: L2 page roots reuse the shared page skeleton
前端每个 L2 页面根 SHALL 复用共享骨架类作为唯一页面根容器（`.doc-page`；固定视口页同时带 `.doc-page--fixed`），其主体内容容器 SHALL 复用 `.doc-body`；模块 MUST NOT 以私有类名自建等价于该骨架的根容器或主体容器，私有类只能作为作用域 modifier 与既有样式钩子保留。主体为自由布局画布 / 图形编辑器的页面 MAY 例外使用私有主体容器，但该例外 MUST 同时登记在 `frontend/AGENTS.md` 与本 spec，且 MUST NOT 扩散到非画布页面。

#### Scenario: Case and element pages use the shared skeleton
- **WHEN** 依次打开 `/cases`、`/cases/projects/:projectId`、`/cases/projects/:projectId/files/:fileId`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 与 `/workflow`
- **THEN** 每个页面根元素的 class 同时包含 `doc-page` 与 `doc-page--fixed`，且其主体内容容器包含 `doc-body`

#### Scenario: Visual appearance does not regress
- **WHEN** 对比迁移前后上述 7 个页面
- **THEN** 分隔线、树面板宽度与表格横向滚动行为保持等价，无新增重叠或内容裁剪（纸面点阵已按 `frontend-l3-container` 收敛为暖白实色 + 主区涂鸦）

#### Scenario: Canvas page exception is registered and contained
- **WHEN** 检查 `/workflow/prototypes/:prototypeId` 的主体容器
- **THEN** 它是 `.wb-body` 且该例外在 `frontend/AGENTS.md` 与本 spec 中均有登记；其余模块页面主体仍为 `.doc-body`

### Requirement: L2 page header comes from a single shared component
所有 L2 页头 SHALL 由 `shared/components/WorkbenchHeader.vue` 提供；系统 MUST NOT 保留第二套页头共享组件。

#### Scenario: Report detail pages match the report list header
- **WHEN** 依次打开 `/reports`、`/reports/{runId}`、`/reports/cases/{resultType}`、`/reports/task/{taskId}`
- **THEN** 四个页面都渲染 `.wb-header`，且页头高度同为 `var(--app-topbar-h)`

#### Scenario: No second header component remains
- **WHEN** 在 `frontend/src` 中检索页头共享件的引用
- **THEN** 只有 `WorkbenchHeader` 被引用，`PageHeader.vue` 已删除且无残留 import

### Requirement: Header and content share one horizontal inset
L2 页头与其下方内容的水平内边距 SHALL 取自同一设计令牌 `--app-space-lg`（24px）；页面 MUST NOT 出现页头内容与主体内容左边缘不一致的取值。

#### Scenario: Left edges align across pages
- **WHEN** 依次打开 `/dashboard`、`/devices`、`/inspector`、`/reports`、`/ai-assistant/agents`、`/cases`、`/elements`、`/workflow`
- **THEN** 页头品牌区左边缘与主体内容左边缘对齐（浏览器实测差值不超过 1px）

### Requirement: No L2 declaration without a consumer
L2 相关的共享件与页面 MUST NOT 保留零消费方的声明：`WorkbenchHeader` 不得声明无人传值的 prop 及其回退分支；页面不得保留无 CSS 规则消费的标记类；模块常量不得存在零 import 的导出。

#### Scenario: Header has no dead prop
- **WHEN** 检查 `WorkbenchHeader.vue` 的 props 与模板分支
- **THEN** 不存在 `mark` prop 与 emoji 回退分支，图标只通过 `icon` 指定

#### Scenario: Report page header config has a consumer
- **WHEN** 检查 `report-generator/constants.ts` 的 `PAGE_HEADER`
- **THEN** 该常量被 `report-generator/index.vue` 消费，列表页模板不再硬编码标题、副标题与图标名

#### Scenario: No dead marker class
- **WHEN** 在 report-generator 的三个详情页检索 `detail-page`
- **THEN** 该标记类不再出现（它没有任何 CSS 规则消费）

### Requirement: Module page root class names are module-prefixed and globally unique

每个模块的页面根 modifier 类名 MUST 带该模块前缀（如 `case-` / `locator-` / `ai-`），且 MUST 在全仓唯一 —— 系统 SHALL NOT 出现两个模块使用同名页根类的情况。孪生组件（同角色的两份实现）的私有类名 MUST 采用同一规格来源（令牌或共享选择器），SHALL NOT 各自维护分叉的字面量规格。

#### Scenario: No page root class is shared across modules

- **WHEN** 静态检索全仓 `modules/**` 中出现的页根 modifier 类名
- **THEN** 每个类名只出现在一个模块内
- **AND** `project-list-page` / `project-workspace` 不再被两个模块同时使用

#### Scenario: Twin components share one spec source

- **WHEN** 对比 `case-manager/components/ProjectTree.vue` 与 `element-locator/components/LocatorTree.vue` 的 `.ex-btn`
- **THEN** 两者的圆角与底色**取自同一令牌**（`--app-radius-sm` / `--paper`），内边距取值一致
- **AND** 不存在一方用字面量、另一方用令牌的分叉（圆角与底色维度）

### Requirement: Subpage navigation lives at the top of doc-body

L2+ 的可见回退（返回芯片与波浪面包屑）MUST 渲染在该页 `.doc-body` 的顶部（加载、错误、空、有数据各态均可见，不得只挂在成功态内容里）；系统 SHALL NOT 把它放进 `.wb-header`。页头仍由唯一共享件 `WorkbenchHeader` 提供，且这些带面包屑的子页上页头 MUST 只显示品牌图标、主标题与副标题；`#actions` 操作按钮 MAY 继续留在页头。导航零件 MUST NOT 成为第二套页头。

#### Scenario: Report detail back control is inside doc-body

- **WHEN** 用户打开 `/reports/{runId}`
- **THEN** 回到列表的控件位于 `.doc-body` 顶部
- **AND** `.wb-header` 内没有「← 返回」或面包屑

#### Scenario: Case and element leaf navigation is inside doc-body

- **WHEN** 用户打开用例文件页或元素文件页
- **THEN** 祖先面包屑或返回芯片位于 `.doc-body` 顶部
- **AND** 页面根仍同时带 `doc-page` 与 `wb-shell`
- **AND** `.wb-header` 仍显示主标题与副标题

#### Scenario: Header remains the single shared header

- **WHEN** 在 `frontend/src` 检索页头共享件
- **THEN** 只有 `WorkbenchHeader` 被页面引用为页头
- **AND** 不存在第二套 `PageHeader` 或独立顶栏导航壳

#### Scenario: Locator project workbench matches the same placement

- **WHEN** 用户打开 `/elements/projects/:code`
- **THEN** 返回芯片与面包屑在 `.doc-body` 内
- **AND** `.wb-header` 内没有 `.wb-crumbs`
