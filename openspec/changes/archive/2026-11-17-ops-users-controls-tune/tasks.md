# 任务：控制区页码行 14px + 去重复计数

- [x] 1.1 `index.vue` 删除第一行右侧的「共 N 个账号」
- [x] 1.2 `index.style.css`：`.ops-page-info` 改为 `--app-size-sm`
- [x] 1.3 `index.style.css`：`.ops-controls :deep(.filter-tab)` 提到 `--app-size-sm`（共享件不动）
- [x] 1.4 实跑 computed：页码文案 14px、筛选标签 14px、搜索框 14px、翻页键 14px；页面不再出现「共 N 个账号」
- [x] 1.5 `npx vitest run tests/ops-console` 全绿；`npm run typecheck`、`npm run lint:styles` 无新增问题
