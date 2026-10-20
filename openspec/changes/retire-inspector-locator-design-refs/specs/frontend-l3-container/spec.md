## MODIFIED Requirements

### Requirement: Paper surfaces carry no module-drawn dot texture
L3 内容容器（`.doc-body`）与页面根（`.doc-page`）的纸面 SHALL 为暖白实色；系统 MUST NOT 在 L0 或 `.doc-body` 上再叠点阵 / 横线本纹理，稀疏装饰 MUST 只由 `shared/components/PaperDoodles.vue` 提供。

#### Scenario: No dot texture on any module page surface
- **WHEN** 依次打开 `/dashboard`、`/cases/projects/:id`、`/workflow` 与 `/serial-log`
- **THEN** 这些页面的 `.doc-page` / `.doc-body` 计算样式中不含点阵 `radial-gradient`，视觉上为纯暖白纸面 + 主区稀疏涂鸦

#### Scenario: Doodle layer remains the only source of decoration
- **WHEN** 检查任一工作台页面的主区
- **THEN** 纸面装饰只来自 `.paper-doodles` 图层（`pointer-events:none`），页面根与 `.doc-body` 无自绘纹理

### Requirement: Content container horizontal inset equals the page header inset
`.doc-body` 的水平内边距 SHALL 与 `.wb-header` 同值（`var(--app-space-lg)`，24px），使页头品牌区左边缘与主体内容左边缘对齐；模块 MUST NOT 为对齐而保留自己的 `.doc-body` 水平内边距覆写。

#### Scenario: Left edges align without module override
- **WHEN** 在浏览器中测量 `/dashboard`、`/reports`、`/reports/{runId}`、`/cases` 与 `/workflow` 的页头品牌区左边缘与首个内容块左边缘
- **THEN** 两处差值为 0（同取 24px），且这些页面的模块 `<style scoped>` 中没有为对齐而写的 `.doc-body` 水平内边距覆写
