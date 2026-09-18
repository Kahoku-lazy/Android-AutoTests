## 1. 令牌与表纸皮肤

- [x] 1.1 在 `frontend/src/shared/styles/tokens.css` 登记本轮缺口 `--comp-crumb-*` / `--comp-sheet-*` / 对话框纸面补缺（值指向已有颜色原子，不改 `--ink`）；验证：`cd frontend && npm run lint:styles` 通过，无新增未登记纯色
- [x] 1.2 为 `AppTable` 增加表纸皮肤（`accent` → 虚线纸 + 模块色硬阴影，表体不旋转），样式落 `workbench-theme.css`；验证：不存在新的 `SketchTable.vue`，`cd frontend && npm run typecheck` 本文件无新增错误
- [x] 1.3 若全局 `.el-dialog` 纸面缺硬阴影/虚线，只在 `style.css` 用已登记 `--comp-*` 补齐；验证：检索无第二处 dialog 边框/圆角皮肤文件

## 2. L2 面包屑零件

- [x] 2.1 新增共享 `WorkbenchCrumbs`（返回芯片 + 波浪面包屑），祖先可点、当前项马克笔且不可点；验证：单测覆盖渲染与点击，`prefers-reduced-motion` 下无依赖倾斜的可交互暗示
- [x] 2.2 `WorkbenchHeader` 增加 `#nav` 槽（不新增第二套页头）；验证：无 `PageHeader` 引用，页头仍 `.wb-header`
- [x] 2.3 更新 `frontend/AGENTS.md` L2 共享件说明与 `doodle-craft/references/components.md` 面包屑/表纸规格；验证：文档与实现口径一致

## 3. 设备管理 + 报告表纸

- [x] 3.1 `device-pool/index.vue` 表格视图去掉 `el-card`，`AppTable` 使用 `--c-device` 表纸；验证：DOM 无该表外套 `el-card`，横向滚动与分页仍可用
- [x] 3.2 报告列表 `report-generator/index.vue` 的 `AppTable` 使用 `--c-report` 表纸；验证：与设备表纸规格同源、阴影色不同
- [x] 3.3 设备局域网连接 / 断开确认弹层色值改令牌引用，保持 `el-dialog`；验证：无自建 backdrop，`close-on-click-modal` 策略不变

## 4. 导航模版接线

- [x] 4.1 报告 `ReportDetail` / `TaskReport` / `CaseBreakdown`：回退挪入页头 `#nav`，去掉 `.doc-body` 顶栏返回；验证：回列表不新开标签，窄屏页头增高不盖正文
- [x] 4.2 元素定位 `ProjectWorkspace` / `LocatorFileView` 与用例 `ProjectWorkspace` / `CaseFileSheet`：页头接入 Hub→台→叶面包屑；验证：祖先路由正确，叶子当前项不可点
- [x] 4.3 AI `TaskDetailPage` / `SkillViewerPage` / `AgentDetail`：页头回退到对应子项（agents / toolbox / agents），删除正文 `.back-btn`；验证：四子项仍只由侧栏切换，页内无第二套顶 Tab

## 5. 门禁

- [x] 5.1 `cd frontend && npm run typecheck` 与相关 vitest（Crumbs / AppTable / 设备或报告列表若有单测）；验证：本变更文件无新增失败
- [x] 5.2 按 `vue-frontend-check` 过本变更涉及 Vue/CSS；验证：布局裁剪 / 字号 / 硬编码色无新增违规
- [ ] 5.3 目视：`/devices` 表、`/reports` 表与详情回退、元素/用例三级回退、AI 深链回退；验证：L0/L1 未改、无双滚动条、无 `[scroll-guard]` 新告警
