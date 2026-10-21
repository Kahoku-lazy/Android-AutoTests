## 1. 筛选条结构

- [x] 1.1 `index.vue` 用共享 `FilterTabs` 替换 `AppTabs`：分区头右侧渲染四个带 `count` 的筛选项，删除四个 `el-tab-pane` 与重复的 `AppCard + AppTable`，只保留一张表。验证：`rg "AppTabs|el-tab-pane|report-tabs" frontend/src/modules/report-generator/index.vue` 无匹配，页面只有一张 `.report-table`。
- [x] 1.2 用 `STATUS_KEYS` / `STATUS_TAB_LABELS` 生成筛选项，`statusCounts` 按 completed+success / failed / stopped 分组；`filteredRuns` 与计数共用 `isCompletedRun`。验证：`rg "全部 \(" frontend/src/modules/report-generator/index.vue` 无匹配，计数口径与行过滤一致。
- [x] 1.3 删除 `.report-tabs` 全部样式，调整 `.report-table-section .doc-section__header` 内边距与对齐，让标题与筛选条同排、窄屏换行。验证：`rg "report-tabs" frontend/src` 无匹配。

## 2. 文档与常量注释

- [x] 2.1 `constants.ts` 的「状态筛选 Tabs」注释改为筛选项 + 计数由页面计算。验证：注释不再描述「label 拼接计数」。

## 3. 验证与关单

- [x] 3.1 `cd frontend; npx vue-tsc --noEmit` 与 `npx vite build` 通过，`npx prettier --check "src/modules/report-generator/index.vue"` 通过。
- [x] 3.2 报告相关单测通过：`npx vitest run tests/report-generator`。
- [x] 3.3 真实页面验收（Playwright，1650×944，`/api/reports` mock 12 条）：分区头右侧出现「全部 12 / 已完成 1 / 失败 11 / 已停止 0」；切到「失败」后页面仍只有一张报告表、行全部为失败态；`.doc-body` 为唯一纵向滚动容器、无页签内层滚动。截图：`temps/visual-check/reports-after.png`、`reports-section-after.png`、`reports-failed-after.png`。
- [x] 3.4 `openspec validate "2026-10-21-report-status-filter-bar" --strict` 通过，归档后 `report-ai-task-list` 主 spec 含新要求。
