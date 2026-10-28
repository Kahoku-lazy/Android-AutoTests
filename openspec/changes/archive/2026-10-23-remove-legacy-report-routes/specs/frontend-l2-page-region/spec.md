## MODIFIED Requirements

### Requirement: Every L2 page root provides the workbench theme scope

每一个 L2 页面根 SHALL 携带工作台主题作用域（`.wb-shell`，或既有等价锚点 `.workflow-workbench`），使页头按钮与页内 `AppCard`/`AppTable`/`AppTabs` 呈现 Doodle Craft 主题；系统 MUST NOT 出现同一模块内列表页与详情页使用同一共享组件却外观不一致。

#### Scenario: Report list and report detail share one component appearance

- **WHEN** 用户先打开 `/reports`（列表页），再打开 `/tasks/{id}`（承接报告行点击的任务详情页）
- **AND** 已删除的 `/reports/{runId}` 场景不再参与本断言
- **THEN** 两个页面里的 `AppTable` / `AppCard` 呈现相同的 Doodle Craft 边框、底色与圆角，无 Element Plus 默认外观回退

#### Scenario: Theme scope present on all workbench page roots

- **WHEN** 逐一打开 `/reports`、`/tasks/{id}`、case-manager、element-locator 与 workflow 原型列表的页面
- **THEN** 每个页面根都在带 `.wb-shell`（或 `.workflow-workbench`）的祖先之内，页头按钮与页内卡片均为主题皮肤

### Requirement: L2 page header comes from a single shared component

所有 L2 页头 SHALL 由 `shared/components/WorkbenchHeader.vue` 提供；系统 MUST NOT 保留第二套页头共享组件。

#### Scenario: Report detail pages match the report list header

- **WHEN** 依次打开 `/reports`、`/tasks/{id}`、`/cases`
- **AND** 已删除的 `/reports/{runId}` 与 `/reports/cases/{resultType}` 不再计入本断言
- **THEN** 三个页面都渲染 `.wb-header`，且页头高度同为 `var(--app-topbar-h)`

#### Scenario: No second header component remains

- **WHEN** 在 `frontend/src` 中检索页头共享件的引用
- **THEN** 只有 `WorkbenchHeader` 被引用，`PageHeader.vue` 已删除且无残留 import

### Requirement: Subpage navigation lives at the top of doc-body

L2+ 的可见回退（返回芯片与波浪面包屑）MUST 渲染在该页 `.doc-body` 的顶部（加载、错误、空、有数据各态均可见，不得只挂在成功态内容里）；系统 SHALL NOT 把它放进 `.wb-header`。页头仍由唯一共享件 `WorkbenchHeader` 提供，且这些带面包屑的子页上页头 MUST 只显示品牌图标、主标题与副标题；`#actions` 操作按钮 MAY 继续留在页头。导航零件 MUST NOT 成为第二套页头。

#### Scenario: Report detail back control is inside doc-body

- **WHEN** 用户打开 `/tasks/{id}`（原 `/reports/{runId}` 的详情职责已由它承接）
- **THEN** 回到列表的控件位于 `.doc-body` 顶部
- **AND** `.wb-header` 内没有「← 返回」或面包屑

#### Scenario: Case and element leaf navigation is inside doc-body

- **WHEN** 用户打开用例文件页
- **THEN** 祖先面包屑或返回芯片位于 `.doc-body` 顶部
- **AND** 页面根仍同时带 `doc-page` 与 `wb-shell`
- **AND** `.wb-header` 仍显示主标题与副标题

#### Scenario: Header remains the single shared header

- **WHEN** 在 `frontend/src` 检索页头共享件
- **THEN** 只有 `WorkbenchHeader` 被页面引用为页头
- **AND** 不存在第二套 `PageHeader` 或独立顶栏导航壳

#### Scenario: Locator project workbench matches the same placement

- **WHEN** 用户打开任一带目录树的项目工作台（如 `/cases/projects/:projectId`）
- **THEN** 返回芯片与面包屑在 `.doc-body` 内
- **AND** `.wb-header` 内没有 `.wb-crumbs`
