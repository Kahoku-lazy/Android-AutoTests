## ADDED Requirements

### Requirement: Subpage navigation lives in the L2 header

L2+ 的可见回退（返回芯片与波浪面包屑）MUST 渲染在 `WorkbenchHeader` 页头区内；系统 SHALL NOT 在 `.doc-body` 顶部再放一套与页头重复的返回条或顶栏 Tab。页头仍由唯一共享件 `WorkbenchHeader` 提供，导航零件 MUST NOT 成为第二套页头。

#### Scenario: Report detail back control is inside the header

- **WHEN** 用户打开 `/reports/{runId}`
- **THEN** 回到列表的控件位于 `.wb-header` 内
- **AND** `.doc-body` 顶部不再单独放「← 返回列表」条

#### Scenario: Case and element leaf navigation is inside the header

- **WHEN** 用户打开用例文件页或元素文件页
- **THEN** 祖先面包屑或返回芯片位于 `.wb-header` 内
- **AND** 页面根仍同时带 `doc-page` 与 `wb-shell`

#### Scenario: Header remains the single shared header

- **WHEN** 在 `frontend/src` 检索页头共享件
- **THEN** 只有 `WorkbenchHeader` 被页面引用为页头
- **AND** 不存在第二套 `PageHeader` 或独立顶栏导航壳
