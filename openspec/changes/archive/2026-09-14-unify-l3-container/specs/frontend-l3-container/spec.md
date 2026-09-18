## Purpose

定义 L3 内容容器的可见行为与边界：全站纸面不得再由模块自绘点阵，`.doc-body` 的水平内边距必须与页头同值，容器级样式覆写必须经模块 modifier 限定，并明确画布类页面主体是唯一登记例外。

## ADDED Requirements

### Requirement: Paper surfaces carry no module-drawn dot texture
L3 内容容器（`.doc-body`）与页面根（`.doc-page`）的纸面 SHALL 为暖白实色；系统 MUST NOT 在 L0 或 `.doc-body` 上再叠点阵 / 横线本纹理，稀疏装饰 MUST 只由 `shared/components/PaperDoodles.vue` 提供。

#### Scenario: No dot texture on any module page surface
- **WHEN** 依次打开 `/dashboard`、`/inspector`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 与 `/cases/projects/:id`
- **THEN** 这些页面的 `.doc-page` / `.doc-body` 计算样式中不含点阵 `radial-gradient`，视觉上为纯暖白纸面 + 主区稀疏涂鸦

#### Scenario: Doodle layer remains the only source of decoration
- **WHEN** 检查任一工作台页面的主区
- **THEN** 纸面装饰只来自 `.paper-doodles` 图层（`pointer-events:none`），页面根与 `.doc-body` 无自绘纹理

### Requirement: Content container horizontal inset equals the page header inset
`.doc-body` 的水平内边距 SHALL 与 `.wb-header` 同值（`var(--app-space-lg)`，24px），使页头品牌区左边缘与主体内容左边缘对齐；模块 MUST NOT 为对齐而保留自己的 `.doc-body` 水平内边距覆写。

#### Scenario: Left edges align without module override
- **WHEN** 在浏览器中测量 `/dashboard`、`/reports`、`/reports/{runId}`、`/inspector` 与 `/elements` 的页头品牌区左边缘与首个内容块左边缘
- **THEN** 两处差值为 0（同取 24px），且这些页面的模块 `<style scoped>` 中没有为对齐而写的 `.doc-body` 水平内边距覆写

### Requirement: Container overrides are scoped by a module modifier
模块需要覆写 L3 容器样式时 SHALL 使用 `.<模块modifier> .doc-body` 形式限定作用域；系统 MUST NOT 新增裸 `.doc-body` / `.doc-page` 覆写。

#### Scenario: No bare container override remains
- **WHEN** 在 `frontend/src/modules` 的 `<style>` 块中检索裸选择器 `.doc-body {`（行首即 `.doc-body`）
- **THEN** 命中数为 0；所有保留的容器覆写都以 `.<模块modifier> .doc-body` 出现

### Requirement: Canvas-like page is a registered container exception
主体为自由布局画布 / 图形编辑器的页面 MAY 不使用 `.doc-body`，但 MUST 被登记为例外（`frontend/AGENTS.md` 与本 spec 同时登记），且该例外 MUST NOT 扩散到非画布页面。

#### Scenario: Workflow canvas page is the only exception
- **WHEN** 检查 `/workflow/prototypes/:prototypeId` 的主体容器
- **THEN** 它是 `.wb-body`（登记例外），且全仓不存在第二个非 `.doc-body` 的模块页面主体容器
