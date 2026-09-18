## ADDED Requirements

### Requirement: L2 page roots reuse the shared page skeleton
前端每个 L2 页面根 SHALL 复用共享骨架类作为唯一页面根容器（`.doc-page`；固定视口页同时带 `.doc-page--fixed`），其主体内容容器 SHALL 复用 `.doc-body`；模块 MUST NOT 以私有类名自建等价于该骨架的根容器或主体容器，私有类只能作为作用域 modifier 与既有样式钩子保留。

#### Scenario: Case and element pages use the shared skeleton
- **WHEN** 依次打开 `/cases`、`/cases/projects/:projectId`、`/cases/projects/:projectId/files/:fileId`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 与 `/workflow`
- **THEN** 每个页面根元素的 class 同时包含 `doc-page` 与 `doc-page--fixed`，且其主体内容容器包含 `doc-body`

#### Scenario: Visual appearance does not regress
- **WHEN** 对比迁移前后上述 7 个页面
- **THEN** 点阵底纹、分隔线、树面板宽度与表格横向滚动行为保持等价，无新增重叠或内容裁剪

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
