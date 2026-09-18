# frontend-l3-content-block Specification

## Purpose
定义 L3 内容块的角色判据与组合规则，使「页面级分区」与「可复用数据块」各有唯一实现，避免同一角色在不同页面出现两套皮肤，并明确 AppCard 只有在工作台主题作用域内才呈现预期外观。

## Requirements

### Requirement: Page-level sections use the skeleton block
位于页头之下、承载整段页面内容且带自有标题或说明的**顶层分区块** SHALL 使用骨架块 `.doc-section`（标题走 `.doc-section__title`）；系统 MUST NOT 用 `AppCard` 充当顶层分区块。本要求适用于以「分区」组织内容的页面；以工作区分栏组织内容、不设分区的页面（如 `/inspector`，主体为模块私有 `.inspector-section` + 分栏 `.workspace`）不要求引入 `.doc-section`。

#### Scenario: Section-organized pages render section blocks
- **WHEN** 依次打开 `/dashboard`、`/reports`、`/ai-assistant/agents` 与 `/ai-assistant/evaluator`
- **THEN** 页头之下的顶层分区块是 `.doc-section`，`AppCard`（`.ac-card`）只出现在这些分区**内部**

#### Scenario: Workspace-organized page needs no section block
- **WHEN** 打开 `/inspector`
- **THEN** 页面主体为模块私有 `.inspector-section` + 分栏 `.workspace`，不出现 `.doc-section`，且不因此判为违规

#### Scenario: Report detail pages use a data block, not a section
- **WHEN** 打开 `/reports/{runId}` 与 `/reports/task/{taskId}`
- **THEN** 页面主体是单个数据块（`.ac-card` 表格卡），不额外套一层 `.doc-section`

### Requirement: Reusable data blocks use AppCard inside the theme scope
图表卡 · 表格卡 · 指标卡 · 认证卡 · 条目卡等**可复用数据块** SHALL 使用 `AppCard`；使用它的页面 MUST 位于工作台主题作用域（`.wb-shell` 或 `.workflow-workbench`）之内，否则其外观退化为 Element Plus 默认。`AppCard` 默认外观 SHALL 为 Hand-Drawn Doodle 钉板壳（虚线描边、近直角、硬偏移色阴影、可选图钉），SHALL NOT 再以实线大圆角 + 彩色顶条为默认。登录页（`/login`）认证输入区为例外：外壳是 Meeting doodle，表单字段扁平铺在钉板内，SHALL NOT 再嵌套 `AppCard`。

#### Scenario: Data blocks render the workbench skin
- **WHEN** 打开 `/reports`（图表卡 / 表格卡）、`/reports/{runId}`（表格卡）与 `/ai-assistant/knowledge`（状态卡 / 分组卡）
- **THEN** 这些块渲染 Doodle 钉板皮肤（`.ac-card` 虚线边与硬阴影），无 Element Plus 默认外观回退

#### Scenario: Auth card stays AppCard on the login view
- **WHEN** 打开 `/login` 且显示登录或注册输入区
- **THEN** 认证字段直接位于 Meeting doodle 内（扁平 `.auth-panel`）
- **AND** 不出现嵌套的 `.ac-card` / `el-card` 作为表单外壳

#### Scenario: Dashboard trend cards use AppCard
- **WHEN** 打开 `/dashboard` 的趋势数据区
- **THEN** 趋势块使用 `AppCard`，不出现裸 `el-card` 作为趋势外壳

### Requirement: Nested composition is bounded
块允许的组合形态为「`.doc-section` 分区内嵌 `AppCard` 数据块」以及「`AppCard` 数据块内嵌 `KpiCard` / 图表 / 表格」；系统 MUST NOT 用 `.doc-section` 包裹单条数据卡，也 MUST NOT 用 `AppCard` 包裹 `.doc-section`。

#### Scenario: Report list composes section then data block
- **WHEN** 检查 `/reports` 的「数据图表」与「测试报告」分区
- **THEN** 每个分区是 `.doc-section`，其内部的图表 / 表格卡是 `.ac-card`；不存在 `AppCard` 包 `.doc-section` 的反向嵌套

### Requirement: The criterion is registered where pages are authored
块语言判据 SHALL 同时登记在本 spec 与 `frontend/AGENTS.md`；`frontend/AGENTS.md` MUST NOT 保留与判据冲突的表述（如『把一组内容框成块就用 AppCard』）。

#### Scenario: AGENTS states the two-role criterion
- **WHEN** 检索 `frontend/AGENTS.md` 的 AppCard 段
- **THEN** 判据按「页面级分区 → `.doc-section`」与「可复用数据块 → AppCard」两分表述，且不再出现「块就用 AppCard」这类单口径说法

### Requirement: 三态渲染有唯一实现

可加载内容区（页面主体、列表、区块、表格）在首屏异步取数期间 SHALL 渲染**加载态**，取数失败 SHALL 渲染**错误态**，取数成功但为空 SHALL 渲染**空态**。加载期间 SHALL NOT 渲染空态（假空态）：判定空态的数据为空与"尚未取数完成" MUST 用加载态区分。三态 MUST 使用共享件：骨架用 `SkeletonCard`、错误用 `ErrorState`、空用 `EmptyState`；系统 SHALL NOT 为骨架另建模块私有的 shimmer/占位实现，也 SHALL NOT 以 Element Plus `el-alert` 顶替错误态。原地异步操作 MAY 使用 `v-loading` 遮罩；表格加载 MUST 通过 `AppTable` 的 `loading` 属性。

#### Scenario: Loading never renders as empty

- **WHEN** 打开 `/cases/projects/:projectId` 或 `/elements/projects/:code` 且树数据仍在加载
- **THEN** 该区域渲染共享 `SkeletonCard` 骨架
- **AND** 不出现"暂无目录或文件"一类空态

#### Scenario: Block skeletons use the shared card

- **WHEN** 静态检索各模块的首屏加载实现
- **THEN** 区块/列表级骨架使用 `SkeletonCard`
- **AND** 不再出现模块私有的 `__loading` 容器样式或裸 `el-skeleton`

#### Scenario: Error state uses the shared pattern

- **WHEN** 任一异步区取数失败
- **THEN** 渲染共享 `ErrorState` 并提供重试入口
- **AND** 全仓不存在 `el-alert` 顶替错误态的用法

#### Scenario: Overlay loading stays Element Plus

- **WHEN** 弹窗、抽屉或面板内执行原地异步操作（保存、加载子内容）
- **THEN** 允许使用 `v-loading` 遮罩，不要求改用骨架
- **AND** 表格加载仍通过 `AppTable` 的 `loading` 属性
