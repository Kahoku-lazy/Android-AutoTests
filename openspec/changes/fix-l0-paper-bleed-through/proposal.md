## Why

设备检查器、元素定位等工作台页根（`.doc-page` / `.doc-body`）用不透明 `--paper` 盖住了 `PaperDoodles`，主区看起来只有暖白实色、没有 L0 涂鸦。全局 `.doc-page--fixed` 已要求透明，模块 scoped 声明把涂鸦挡掉了。

## What Changes

- 去掉工作台页根 / `.doc-body` 上多余的不透明 `background(-color): var(--paper)`，让壳层暖白纸面 + 主区涂鸦透出来。
- 明确：L0 纸色只画在 `html`/`body`/`#app`/`.app-shell`；带侧栏工作台的 `.doc-page` / `.doc-body` MUST 保持透明。
- **不改** L3/L4 内容面（`.doc-section`、筛选栏、表格、树、截图画布等）的卡片底色。
- **不改** 登录页（无侧栏、不挂 `PaperDoodles`）的纸面底色。
- 测试报告列表/详情页根本身没有这层纸面；本变更只核对其间隙能否透出涂鸦，不为铺满的白卡片去底。

## 关联文档

- 能力规格：`openspec/specs/frontend-l0-paper-doodle/spec.md`、`openspec/specs/frontend-l3-container/spec.md`
- UI 布局规范：`.agents/skills/doodle-craft/references/layout.md` §4.2（L0 暖白纸面 + 主区涂鸦；禁止 `.doc-page--fixed .doc-body` 再叠第二套纸纹）
- 仓库无 `dev_docs/文档编号对照表.md`；本变更是前端视觉层 bugfix，不改 PRD/ARCH 业务范围。

## Capabilities

### New Capabilities

- （无）不引入新能力域。

### Modified Capabilities

- `frontend-l0-paper-doodle`: 补一条可验收需求：带侧栏工作台的页面根与 `.doc-body` MUST NOT 用不透明纸面盖住涂鸦层。
- `frontend-l3-container`: 把「纸面纯色、禁自绘点阵」收紧为「页根 / `.doc-body` 不得再画一层不透明 `--paper`」，避免与 L0 涂鸦互斥。

## Impact

- 前端：`device-inspector/index.vue`、`element-locator` 三页、`dashboard/DashboardView.style.css`、`case-manager/ProjectWorkspace.vue` 与 `CaseFileSheet.vue` 的 `.doc-body` 纸面声明。
- 核对但不改卡片皮肤：`report-generator` 各页、`device-pool`、`ai-assistant` 页根。
- **不改** API、后端、登录页、`frontend/src/style.css` 的 `#app`/`body` L0 纸面、`App.vue` 壳层。
- 验证：打开检查器 / 元素定位 / 仪表盘 / 用例工作台，主区卡片间隙可见 `PaperDoodles`；交互与滚动不变。
