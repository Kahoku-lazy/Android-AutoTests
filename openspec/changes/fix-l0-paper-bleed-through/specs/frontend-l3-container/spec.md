## MODIFIED Requirements

### Requirement: Paper surfaces carry no module-drawn dot texture

L3 内容容器（`.doc-body`）与页面根（`.doc-page`）在带侧栏工作台上 SHALL 保持背景透明，使 L0 暖白纸面与主区涂鸦透出；系统 MUST NOT 在这些表面上再画不透明 `--paper` / 暖白实色，也 MUST NOT 再叠点阵 / 横线本纹理。稀疏装饰 MUST 只由主区涂鸦层提供。内容块（分区卡片、筛选栏、表格、树、画布）MAY 保留自身底色。

#### Scenario: No dot texture on any module page surface

- **WHEN** 依次打开 `/dashboard`、`/inspector`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 与 `/cases/projects/:id`
- **THEN** 这些页面的 `.doc-page` / `.doc-body` 计算样式中不含点阵 `radial-gradient`，视觉上为 L0 暖白纸面 + 主区稀疏涂鸦（涂鸦从内容块间隙可见）

#### Scenario: Doodle layer remains the only source of decoration

- **WHEN** 检查任一带侧栏工作台页面的主区
- **THEN** 纸面装饰只来自涂鸦图层（不拦截指针），页面根与 `.doc-body` 无自绘纹理、无不透明纸面填充

#### Scenario: No opaque paper fill on workbench containers

- **WHEN** 检查 `/inspector`、`/elements`、`/dashboard` 与 `/cases/projects/:id` 的模块样式
- **THEN** 页面根与 `.doc-body` 未声明不透明 `background(-color): var(--paper)`（或等价暖白实色）
- **AND** `.doc-section`、筛选栏、表格等内容块底色仍可保留
