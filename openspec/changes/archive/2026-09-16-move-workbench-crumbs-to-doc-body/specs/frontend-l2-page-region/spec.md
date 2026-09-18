## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Subpage navigation lives in the L2 header

**Reason**: 页头只保留主/副标题；可见回退改到 `.doc-body` 顶部，避免页头被面包屑撑高、职责混杂。
**Migration**: 按新增需求「Subpage navigation lives at the top of doc-body」把 `WorkbenchCrumbs` 从 `WorkbenchHeader #nav` 挪到 `.doc-body` 顶部；无剩余消费方后删除 `#nav` 槽。
