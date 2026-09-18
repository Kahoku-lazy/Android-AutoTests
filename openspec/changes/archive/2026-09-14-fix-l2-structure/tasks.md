## 1. P5 页面根区收敛到共享骨架

- [x] 1.1 case-manager 三页迁移。验证：三页根元素 class 实测为 `doc-page doc-page--fixed wb-shell project-list-page|project-workspace|case-sheet`，主体含 `doc-body`
- [x] 1.2 element-locator 三页迁移。验证：同上（`project-list-page` / `project-workspace` / `file-view`）
- [x] 1.3 workflow `PrototypeList.vue` 迁移。验证：`/workflow` 根含 `doc-page doc-page--fixed`，主体含 `doc-body`
- [x] 1.4 清理因迁移产生的死声明。验证：`rg 'height: 100%' frontend/src/modules` 在 7 页私有根选择器中 0 命中；私有根规则（`.project-list-page{` 等）全仓 0 命中
- [x] 1.5 逐页复核滚动出口与高度。验证：7 页 1280px 下 `rootH=900`（=视口高，未塌陷）、主体滚动模式与迁移前一致（列表 `auto`、工作台/文件视图 `hidden`）、`[scroll-guard]` 告警 0 条
- [x] 1.6 视觉不回退核对。验证：7 页关键几何实测 —— 页头底边 96、主体左内边距 24、内容左边缘 24、主体滚动模式不变；点阵/分隔线等模块声明原样保留（未做像素级前后截图对照，属语义等价核对）

## 2. P6 页头收敛到单一共享件

- [x] 2.1 `CaseBreakdown.vue` 换 `WorkbenchHeader`。验证：`/reports/cases/pass` 渲染 `.wb-header`，高度 96
- [x] 2.2 `TaskReport.vue` 两个分支一并换。验证：`/reports/task/1` 渲染 `.wb-header`，高度 96（错误态与数据态两个根都含 `wb-shell`）
- [x] 2.3 `ReportDetail.vue` 换 `WorkbenchHeader`。验证：`/reports/1` 渲染 `.wb-header`，高度 96
- [x] 2.4 删除 `PageHeader.vue` 并同步 `frontend/AGENTS.md`。验证：`rg "PageHeader" frontend/src frontend/AGENTS.md` 只剩不相关的 `DevicePageHeader` 类型；AGENTS.md 共享件清单第 8 项已移除、第 7 项计数更新为 19
- [x] 2.5 复核三页首屏间距。验证：三页 `.doc-body` 顶部内边距 16px、首屏内容可见且未被页头遮挡（`headerOverflow=false`）

## 3. P7 清理 L2 死代码

- [x] 3.1 删除 `WorkbenchHeader` 的 `mark` prop、默认值与 `v-else` emoji 回退分支（`.soft-icon*` 属 L0 既有工具类，按 L0 约定不动）。验证：该文件内 `mark` 只剩 `brand-mark`；19 处消费方仍正常渲染图标
- [x] 3.2 删除三个 report 详情页的 `.detail-page` 标记类。验证：`rg "detail-page" frontend/src/modules/report-generator` 0 命中（其余命中是不相关的 `task-detail-page`）
- [x] 3.3 让 `constants.ts` 的 `PAGE_HEADER` 被消费。验证：新增 `REPORT_HEADER_ICON`/`REPORT_HEADER_GRADIENT` 供四页共用，`index.vue` 改读常量；report-generator 新增行中 **0 处**硬编码 title/subtitle/icon 字面量

## 4. P8 水平内边距统一到 var(--app-space-lg)

- [x] 4.1 `style.css` 全局 `.doc-page--fixed .doc-body` 的 `18px` → `var(--app-space-lg)`。验证：`/ai-assistant/agent/1` 与 `/ai-assistant/toolbox/skills/:name` 内容内边距实测 24
- [x] 4.2 `report-generator/index.vue` 的 `20px` → `var(--app-space-lg)`。验证：`/reports` 主体左内边距实测 24
- [x] 4.3 `ai-assistant/index.style.css` 只声明 `padding-bottom`，左右继承全局，4.1 改完即对齐，**无需改动**。验证：`/ai-assistant/agents` 内容内边距实测 24
- [x] 4.4 `device-inspector/index.vue` 的 `.inspector-section` `28px` → `var(--app-space-lg)`。验证：`/inspector` 内容内边距实测 24
- [x] 4.5 `case-manager/CaseFileSheet.vue` 主体 `12px` → `var(--app-space-lg)`。验证：`/cases/projects/:id/files/:fileId` 主体左内边距实测 24
- [x] 4.6 全量左边缘实测：22 路由 × 768/1024/1280 共 66 条，`brandInset` 与内容内边距**全部 = 24**，差值 0。验证：浏览器实测异常 0 条

## 5. 门禁与验收

- [x] 5.1 运行 `cd frontend && npm run typecheck`。验证：退出码 1，共 35 个错误全部位于本次未触碰的文件（`case-manager/components/ProjectTree.vue`、`device-inspector/store.ts`、`tests/dashboard/**`），本变更涉及文件 **0 报错**
- [x] 5.2 用 `vue-frontend-check` 技能过前端门禁（§7 扫描限本变更新增行 102 行）。验证：字号 0、颜色硬编码 0、@click 0、fetch/axios 0、禁项 0；`overflow:hidden` 2 处为工作台/文件视图主体（树与画布自管滚动，calibration §3 允许）；1 处 `gap:14px` 属该行既有值（未改）
- [x] 5.3 22 路由 × 768/1024/1280 浏览器回归：页头高度恒 96、无自身溢出、无整页双滚动条、无跳登录。验证：异常 0 条
- [x] 5.4 全量主题锚点断言：19 个 `WorkbenchHeader` 消费文件的页面根全部含 `wb-shell`（或 `.workflow-workbench`）。验证：19/19 命中
- [x] 5.5 运行 `openspec validate fix-l2-structure --strict`。验证：Change is valid
