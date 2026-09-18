# frontend-l3-container Specification

## Purpose
定义 L3 内容容器的可见行为与边界：全站纸面不得再由模块自绘点阵，`.doc-body` 的水平内边距必须与页头同值，容器级样式覆写必须经模块 modifier 限定，并明确画布类页面主体是唯一登记例外。

## Requirements

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

### Requirement: 共享骨架块不得无作用域重定义

`.doc-section` 及其 BEM 部分（`__header` / `__title` / `__label`）的皮肤 SHALL 由全局样式唯一定义。模块确需差异时 MUST 通过任一登记方式限定作用域：`.<模块根类> .doc-section…`，或 BEM modifier `.doc-section--<变体>`（该 modifier 与 `.doc-section` 同时挂在同一元素上）。覆写 MUST NOT 重复声明全局已提供的同名属性（背景 / 描边 / 圆角 / 阴影 / 内边距 / 标题字号与字重）。系统 SHALL NOT 以**裸** `.doc-section` / `.doc-section__*` 选择器覆写该骨架块，SHALL NOT 用行内 `style` 覆写其内边距。

#### Scenario: No bare section override remains

- **WHEN** 在 `frontend/src/modules` 的 `<style>` 块与 `.css` 文件中检索行首即 `.doc-section`（**不含** `--` 修饰符）或 `.doc-section__` 的选择器
- **THEN** 命中数为 `0`
- **AND** 保留的变体只以 `.<模块根类> .doc-section…` 或 `.doc-section--<变体>` 两种形式出现

#### Scenario: Section skin is single-sourced

- **WHEN** 比较 `/reports` 与 `/ai-assistant/evaluator` 的 `.doc-section` 计算样式
- **THEN** 背景、描边宽度与颜色、圆角、阴影、内边距同源（同为墨色实线描边，而非 `1px` 近白线）
- **AND** 标题字号同为全局 `--app-size-md`

#### Scenario: No inline padding override on sections

- **WHEN** 检索模板中对 `.doc-section` 的 `style="padding…"` 覆写
- **THEN** 命中数为 `0`
- **AND** 需要贴边布局的分区改用 `.<模块根类> .<分区类>` 的类选择器表达

#### Scenario: Module-specific decoration keeps its scope

- **WHEN** 检查 `/reports` 分区标题的手绘波浪下划线
- **THEN** 该装饰以 `.report-workbench .doc-section__title::after` 形式声明
- **AND** 不影响其他模块的分区标题
