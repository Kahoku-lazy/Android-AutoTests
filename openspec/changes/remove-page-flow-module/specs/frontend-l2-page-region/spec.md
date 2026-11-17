## MODIFIED Requirements

### Requirement: Header content never overlaps page content

页头 SHALL 在常规宽度下保持 `var(--app-topbar-h)`（96px）高度并与侧栏 header 底边对齐；标题与副标题 MUST 单行省略号截断；动作区放不下时 MUST 换行并由页头增高容纳，页头 MUST NOT 让自身内容溢出其盒子或覆盖正文内容区。

#### Scenario: Long title and subtitle truncate instead of wrapping

- **WHEN** 在 768px–1024px 宽度打开副标题较长的页面（如 `/dashboard`）
- **THEN** 标题与副标题各占一行并以省略号截断，页头高度仍为 96px

#### Scenario: Header with many actions does not overflow

- **WHEN** 在 768px–1024px 宽度打开动作区元素较多的页头（如用例文件工作台 `/cases/projects/:projectId/files/:fileId`，含重命名 / 保存 / 新建行）
- **THEN** 页头不产生自身溢出（内容高 ≤ 页头高），必要时页头增高把正文下推，正文首屏内容不被遮挡

#### Scenario: Alignment with sidebar header survives

- **WHEN** 在 ≥1280px 宽度打开任一工作台页面
- **THEN** 页头高度等于侧栏 header 高度（同为 `var(--app-topbar-h)`），两者底边对齐

### Requirement: Every L2 page root provides the workbench theme scope

每一个 L2 页面根 SHALL 携带工作台主题作用域（`.wb-shell`），使页头按钮与页内 `AppCard`/`AppTable`/`AppTabs` 呈现 Doodle Craft 主题；系统 MUST NOT 出现同一模块内列表页与详情页使用同一共享组件却外观不一致。

#### Scenario: Report list and report detail share one component appearance

- **WHEN** 用户先打开 `/reports`（列表页），再打开 `/tasks/{id}`（承接报告行点击的任务详情页）
- **AND** 已删除的 `/reports/{runId}` 场景不再参与本断言
- **THEN** 两个页面里的 `AppTable` / `AppCard` 呈现相同的 Doodle Craft 边框、底色与圆角，无 Element Plus 默认外观回退

#### Scenario: Theme scope present on all workbench page roots

- **WHEN** 逐一打开 `/reports`、`/tasks/{id}`、case-manager、device-pool 与 serial-log 的页面
- **THEN** 每个页面根都在带 `.wb-shell` 的祖先之内，页头按钮与页内卡片均为主题皮肤

### Requirement: L2 page roots reuse the shared page skeleton

前端每个 L2 页面根 SHALL 复用共享骨架类作为唯一页面根容器（`.doc-page`；固定视口页同时带 `.doc-page--fixed`），其主体内容容器 SHALL 复用 `.doc-body`；模块 MUST NOT 以私有类名自建等价于该骨架的根容器或主体容器，私有类只能作为作用域 modifier 与既有样式钩子保留。页面流画布已退役，MUST NOT 再保留画布类页面的私有主体容器例外。

#### Scenario: Case and element pages use the shared skeleton

- **WHEN** 依次打开 `/cases`、`/cases/projects/:projectId`、`/cases/projects/:projectId/files/:fileId` 与 `/serial-log`
- **THEN** 每个页面根元素的 class 同时包含 `doc-page` 与 `doc-page--fixed`，且其主体内容容器包含 `doc-body`

#### Scenario: Canvas page exception is registered and contained

<!-- 场景名沿自变更前：画布例外已随页面流退役撤销，本场景改为守住「例外零残留」 -->

- **WHEN** 检查全仓模块页面的主体容器
- **THEN** 所有模块页面主体均为 `.doc-body`，不存在第二个非 `.doc-body` 的模块页面主体容器
- **AND** 画布例外在 `frontend/AGENTS.md` 与 `frontend-l3-container` 中的登记已同步清除

#### Scenario: Visual appearance does not regress

- **WHEN** 对比迁移前后上述页面
- **THEN** 分隔线、树面板宽度与表格横向滚动行为保持等价，无新增重叠或内容裁剪（纸面点阵已按 `frontend-l3-container` 收敛为暖白实色 + 主区涂鸦）

### Requirement: Header and content share one horizontal inset

L2 页头与其下方内容的水平内边距 SHALL 取自同一设计令牌 `--app-space-lg`（24px）；页面 MUST NOT 出现页头内容与主体内容左边缘不一致的取值。

#### Scenario: Left edges align across pages

- **WHEN** 依次打开 `/dashboard`、`/devices`、`/reports`、`/ai-assistant/agents`、`/cases` 与 `/serial-log`
- **THEN** 页头品牌区左边缘与主体内容左边缘对齐（浏览器实测差值不超过 1px）
