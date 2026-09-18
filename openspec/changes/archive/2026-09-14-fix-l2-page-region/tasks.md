## 1. 页头按钮语义色恢复（P1）

- [x] 1.1 改写 `frontend/src/shared/components/WorkbenchHeader.vue` 的按钮皮肤：`:deep(.el-button)` 只保留 `border-radius` / `padding` / `font-weight` / `font-family` / `border-width: 2.5px` / `transition` / `box-shadow` 七个几何属性（`!important` 仅留在这层），删除 `background` / `color` / `border` 三条颜色类 `!important`；同时删除 `:deep(.el-button:hover)` 的 `background` 强制。验证：浏览器实测页头 primary 恢复为 `rgb(247,201,72)`（`--c-dashboard`）
- [x] 1.2 修 `frontend/src/shared/styles/motion.css` 的 `.wb-btn--sunset`：在原有 `--el-button-*` 自定义属性之外，用 `var()` 转发声明 `background` / `border-color` / `color` 与 hover 三件套，并补注释说明「变体必须直接声明颜色，否则被基础皮肤盖住」。验证：`/dashboard` 页头「刷新」按钮实测 `rgb(240,192,144)`、hover `rgb(245,205,160)`
- [x] 1.3 逐页核对语义色：primary / success / danger / 无类型默认。验证：浏览器实测 `rgb(247,201,72)` / `rgb(107,203,119)`（`--c-device`）/ `rgb(255,224,219)`（`--app-status-danger-bg`）/ `rgb(255,255,255)`（`--app-bg-card`）
- [x] 1.4 核对 hover 未被统一：页头内不再有统一的 hover 底色强制（原 `.wb-header :deep(.el-button:hover)` 已删）；无类型按钮 hover 走 `--c-dashboard`、变体按钮 hover 走自身变体色。验证：浏览器实测 sunset hover = `rgb(245,205,160)`，非统一黄

## 2. 页头不溢出与层叠生效（P2 / P3）

- [x] 2.1 `.wb-header` 改 `height` → `min-height: var(--app-topbar-h, 96px)`，并补 `position: relative` 使既有 `z-index: 10` 生效（附注释）。验证：浏览器实测 computed `position: relative`、`z-index: 10`，1440px 下 `clientHeight` = 96
- [x] 2.2 `.brand-title` / `brand-sub` 加 `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`。验证：768px 下标题与长副标题各占一行（标题 `font-size` 32px、盒高 41.3px 含 -0.5° 微旋转）且 `scrollWidth > clientWidth` 触发省略号
- [x] 2.3 保留 `.header-actions` 的 `flex-wrap: wrap`（不新增 `nowrap`，否则窄屏变成横向溢出且 `min-height` 永不触发），由 `min-height` 兜住增高。验证：768px 下 workflow 页头 6 项动作换行 → 页头 96→134px、`scrollHeight ≤ clientHeight`（自身无溢出）、正文被下推且 `noOverlap` 为真
- [x] 2.4 三档宽度逐页回归：22 条路由 × 768 / 1024 / 1280。验证：所有渲染出 `.wb-header` 的页面页头高度均为 96px、`headerOverflows` 全为 false、`pageScrolls` 全为 false、无跳转到 `/login`（report 详情 3 页用 `PageHeader`，本就不含 `.wb-header`，属预期）

## 3. L2 主题作用域补齐（P4）

- [x] 3.1 report-generator 4 处页面根补 `wb-shell`：`CaseBreakdown.vue`、`TaskReport.vue`（错误态与数据态两个根）、`ReportDetail.vue`。验证：`rg 'class="doc-page' frontend/src/modules/report-generator` 每个页面根均含 `wb-shell`
- [x] 3.2 case-manager 3 处页面根补 `wb-shell`：`ProjectList.vue` / `ProjectWorkspace.vue` / `CaseFileSheet.vue`。验证：三个页面根 class 均含 `wb-shell`（应用级实测根元素为 `div.project-list-page wb-shell` 等）
- [x] 3.3 element-locator 3 处页面根补 `wb-shell`：`ProjectList.vue` / `ProjectWorkspace.vue` / `LocatorFileView.vue`。验证：三个页面根 class 均含 `wb-shell`
- [x] 3.4 workflow `PrototypeList.vue` 页面根补 `wb-shell`（`workflow/index.vue` 已有 `.workflow-workbench` 等价锚点，未改）。验证：`/workflow` 与 `/workflow/prototypes/:prototypeId` 均在主题锚点内
- [x] 3.5 消费方 ↔ 锚点清单断言：16 个 `WorkbenchHeader` 消费文件逐一核对页面根。验证：16/16 命中 `wb-shell` 或 `workflow-workbench`，无遗漏
- [x] 3.6 目视回归 case-manager + element-locator 6 个页面（补 `wb-shell` 会启用 `box-sizing: border-box` 与主题字体）。验证：同一 DOM 下移除 `wb-shell` 做 A/B，6 个页面几何差异 0、`box-sizing` 差异 0、字体差异 0（应用级实测，API 打桩为 500，空/错态下未渲染数据型内容，数据路径未覆盖）

## 4. 门禁与验收

- [x] 4.1 运行 `cd frontend && npm run typecheck`。验证：退出码 1，报错全部位于本次未触碰的文件（`case-manager/components/ProjectTree.vue`、`device-inspector/store.ts`、`tests/dashboard/**`），本变更 12 个文件零 TS 报错
- [x] 4.2 用 `vue-frontend-check` 技能过前端门禁（含 calibration §7 强制扫描）。验证：仅扫本变更新增行——字号 0 命中、硬编码颜色 0 命中（自查发现并修正了 sunset 变体的硬编码声明）、禁项 0 命中、协议/逻辑类 0 命中；`overflow: hidden` 2 处为标题/副标题省略号（calibration §3：不在承载表单/主操作的滚动容器上）
- [x] 4.3 对比 `/reports` 与 `/reports/{runId}` 同一 `AppCard` 皮肤。验证：浏览器实测修复后列表页根与详情页根的 `ac-card` 完全一致（边框/底色/圆角/阴影），移除 `wb-shell` 后详情页退化为 `0px/透明/0px/无阴影` —— 证明正是本次补锚点消除了差异
- [x] 4.4 开发环境打开 dashboard 与固定视口工作台页。验证：`/dashboard`、`/cases`、`/devices`、`/workflow`、`/elements/projects/android` 在 768 / 1280 两档下 `[scroll-guard]` 告警 0 条、`pageScrolls` 全为 false、主区容器仍是唯一滚动出口
- [x] 4.5 运行 `openspec validate fix-l2-page-region --strict`。验证：Change is valid（退出码 0）
