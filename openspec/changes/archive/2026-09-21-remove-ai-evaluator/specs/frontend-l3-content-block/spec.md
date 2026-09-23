## MODIFIED Requirements

### Requirement: Page-level sections use the skeleton block
位于页头之下、承载整段页面内容且带自有标题或说明的**顶层分区块** SHALL 使用骨架块 `.doc-section`（标题走 `.doc-section__title`）；系统 MUST NOT 用 `AppCard` 充当顶层分区块。本要求适用于以「分区」组织内容的页面；以工作区分栏组织内容、不设分区的页面（如 `/inspector`，主体为模块私有 `.inspector-section` + 分栏 `.workspace`）不要求引入 `.doc-section`。

#### Scenario: Section-organized pages render section blocks
- **WHEN** 依次打开 `/dashboard`、`/reports`、`/ai-assistant/agents` 与 `/ai-assistant/knowledge`
- **THEN** 页头之下的顶层分区块是 `.doc-section`，`AppCard`（`.ac-card`）只出现在这些分区**内部**

#### Scenario: Workspace-organized page needs no section block
- **WHEN** 打开 `/inspector`
- **THEN** 页面主体为模块私有 `.inspector-section` + 分栏 `.workspace`，不出现 `.doc-section`，且不因此判为违规

#### Scenario: Report detail pages use a data block, not a section
- **WHEN** 打开 `/reports/{runId}` 与 `/reports/task/{taskId}`
- **THEN** 页面主体是单个数据块（`.ac-card` 表格卡），不额外套一层 `.doc-section`
