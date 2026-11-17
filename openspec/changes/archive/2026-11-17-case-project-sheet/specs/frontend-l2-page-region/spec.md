## MODIFIED Requirements

### Requirement: Header content never overlaps page content

页头 SHALL 在常规宽度下保持 `var(--app-topbar-h)`（96px）高度并与侧栏 header 底边对齐；标题与副标题 MUST 单行省略号截断；页头 MUST NOT 让自身内容溢出其盒子或覆盖正文内容区。用例管理的项目列表与项目表页头 MUST NOT 渲染功能按钮。这些页面的新建、导入、保存与新增行 MUST 放在正文工具条。

#### Scenario: Long title and subtitle truncate instead of wrapping

- **WHEN** 在 768px–1024px 宽度打开副标题较长的页面（如 `/dashboard`）
- **THEN** 标题与副标题各占一行并以省略号截断，页头高度仍为 96px

#### Scenario: Header with many actions does not overflow

- **WHEN** 在 768px–1024px 宽度打开 `/cases` 或 `/cases/projects/:projectId`
- **THEN** 页头只有图标和标题，高度仍为 96px
- **AND** 新建、导入、保存与新增行不在页头，因此不会把页头撑高或盖住正文

#### Scenario: Alignment with sidebar header survives

- **WHEN** 在 ≥1280px 宽度打开任一工作台页面
- **THEN** 页头高度等于侧栏 header 高度（同为 `var(--app-topbar-h)`），两者底边对齐

### Requirement: Subpage navigation lives at the top of doc-body

L2+ 的可见回退（返回芯片与波浪面包屑）MUST 渲染在该页 `.doc-body` 的顶部（加载、错误、空、有数据各态均可见，不得只挂在成功态内容里）；系统 SHALL NOT 把它放进 `.wb-header`。页头仍由唯一共享件 `WorkbenchHeader` 提供。带面包屑的子页上，页头 MUST 只显示品牌图标、主标题与副标题。用例管理页面的 `#actions` MUST 为空。其它模块的 `#actions` MAY 继续留在页头。导航零件 MUST NOT 成为第二套页头。

#### Scenario: Report detail back control is inside doc-body

- **WHEN** 用户打开 `/tasks/{id}`（原 `/reports/{runId}` 的详情职责已由它承接）
- **THEN** 回到列表的控件位于 `.doc-body` 顶部
- **AND** `.wb-header` 内没有「← 返回」或面包屑

#### Scenario: Case and element leaf navigation is inside doc-body

- **WHEN** 用户打开用例项目表 `/cases/projects/:projectId`
- **THEN** 祖先面包屑或返回芯片位于 `.doc-body` 顶部
- **AND** 页面根仍同时带 `doc-page` 与 `wb-shell`
- **AND** `.wb-header` 仍显示主标题与副标题
- **AND** `.wb-header` 内没有功能按钮

#### Scenario: Header remains the single shared header

- **WHEN** 在 `frontend/src` 检索页头共享件
- **THEN** 只有 `WorkbenchHeader` 被页面引用为页头
- **AND** 不存在第二套 `PageHeader` 或独立顶栏导航壳

#### Scenario: Locator project workbench matches the same placement

- **WHEN** 用户打开 `/cases/projects/:projectId`
- **THEN** 返回芯片与面包屑在 `.doc-body` 内
- **AND** `.wb-header` 内没有 `.wb-crumbs`
- **AND** 导入与保存按钮位于正文工具条，不在 `.wb-header`
