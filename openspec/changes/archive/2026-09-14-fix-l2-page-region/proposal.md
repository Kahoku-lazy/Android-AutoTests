## Why

前端 L2 区域（页头区 / 页面根区）存在 4 处实现与规范背离，且后果都是**静默**的：页头内所有按钮被组件自身的 `!important` 压成白底，primary/danger/success 与 `wb-btn--sunset` 的规范语义色全部失效；页头定高 96px 且动作区可换行、无溢出兜底，窄视口下内容会盖到正文；`z-index: 10` 落在 static 元素上从未生效；另有 11 个 L2 页面根缺工作台主题作用域，使这些页面的页头按钮与 `AppCard/AppTable/AppTabs` 一起退化成 Element Plus 默认外观（同一模块的列表页与详情页外观不一致）。这些缺陷都不报错、不告警，只能靠逐页目视发现，因此需要在本层收敛并固化成行为契约。

## What Changes

- **页头按钮语义色恢复**：`WorkbenchHeader.vue` 的 `:deep(.el-button)` 只保留几何属性（圆角 / 内边距 / 字重 / 边框宽度 / 字体 / 过渡），删除 `background` / `color` / `border` 上的 `!important` 强制，使 primary（`var(--c-dashboard)`）、success（`var(--c-device)`）、danger（`var(--app-status-danger)`）与默认白底墨框各自回到规范值。
- **`wb-btn--sunset` 变体修复**：`motion.css` 的变体规则改为直接声明 `background` / `border-color` / `color`，不再只写 Element Plus 自定义属性（那些属性会被基础皮肤 `.wb-shell .wb-btn.el-button` 的显式 `background` 覆盖）；仪表盘页头「刷新」按钮实际呈现 sunset 橙。
- **页头不再溢出侵入正文**：标题/副标题单行省略号截断，动作区不换行且按钮不收缩（`.brand-text` 承担压缩），页头由固定 `height` 改为 `min-height: var(--app-topbar-h)`；常规宽度仍为 96px，与侧栏 header 保持底边对齐。
- **页头层叠声明实际生效**：为 `.wb-header` 补 `position: relative`，使既有 `z-index: 10` 不再是死声明。
- **L2 主题作用域补齐**：为 11 个 L2 页面根补 `wb-shell`（report-generator 详情 4 处、case-manager 3 处、element-locator 3 处、workflow 原型列表 1 处），使页头按钮与页内 `AppCard/AppTable/AppTabs` 呈现 Doodle Craft 主题。
- **BREAKING**：无。纯前端视觉与布局行为，不涉及接口、路由表、鉴权与数据。
- 不改变 L0「视口固定 + 内层滚动」策略与 L1 主区结构；不统一 L2 容器命名、不废弃 `PageHeader`、不动点阵纹理与页头左内边距（属已知项，不在本次范围）。

## 关联文档

- `frontend/AGENTS.md`：L0–L5 区域模型与归属、「L1 只读」契约，以及 `WorkbenchHeader` / `AppCard` / `AppTable` 的使用注意
- `openspec/specs/frontend-l0-paper-doodle/spec.md`：同域前置能力（L0 纸面底色与滚动策略），本变更不改其任何行为
- `.agents/skills/doodle-craft/references/components.md` §一.1 Button：按钮规范色与几何（primary = `var(--c-dashboard)`、danger = `var(--app-status-danger)`）
- 同域并行变更：`openspec/changes/align-frontend-motion/`（同样改 `motion.css`，但仅 `.fade-slide-*` 路由过渡块，与本变更的 `.wb-btn--*` 变体块不重叠；两者需约定先后顺序）
- 说明：`dev_docs/文档编号对照表.md` 不存在，`dev_docs/05-开发与测试` 下仅有 API/测试类文档、无 UI 规范编号文档，故本变更不引用编号文档（同 `align-frontend-motion` 的先例）

## Capabilities

### New Capabilities

- `frontend-l2-page-region`: 前端 L2 区域（页头区 / 页面根区）的可见行为契约 —— 页头按钮保留语义色、页头内容不溢出侵入正文、页头层叠声明实际生效、所有 L2 页面根提供工作台主题作用域

### Modified Capabilities

（无；`openspec/specs/` 下无 L2 相关既有能力，L0 能力 `frontend-l0-paper-doodle` 的行为不变）

## Impact

- 前端共享件：`frontend/src/shared/components/WorkbenchHeader.vue`（按钮皮肤、页头布局与层叠）、`frontend/src/shared/styles/motion.css`（`wb-btn--sunset` 变体）
- 前端 L2 页面根（补 `wb-shell`，共 11 处）：
  - `frontend/src/modules/report-generator/{CaseBreakdown,TaskReport,ReportDetail}.vue`（TaskReport 含错误态与数据态两个根）
  - `frontend/src/modules/case-manager/{ProjectList,ProjectWorkspace,CaseFileSheet}.vue`
  - `frontend/src/modules/element-locator/{ProjectList,ProjectWorkspace,LocatorFileView}.vue`
  - `frontend/src/modules/workflow/PrototypeList.vue`
- 测试范围：`frontend/tests/`（现有单测若断言页头或主题作用域需同步）、`cd frontend && npm run typecheck`、`vue-frontend-check` 前端门禁
- 不影响：后端 `apps/`、API 契约与响应信封、鉴权、路由表、L0/L1 骨架、各模块业务数据流
