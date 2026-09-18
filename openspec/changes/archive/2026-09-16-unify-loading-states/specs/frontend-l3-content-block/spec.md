## ADDED Requirements

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