# 任务：Agent 配置页常驻翻页 + 间距

- [x] 1.1 `constants.ts` 新增 `OPS_AGENT_PAGE_SIZE = 10`
- [x] 1.2 `agents.vue`：`page` / `totalPages` / `pagedAgents` / `goPage`，表格数据改 `pagedAgents`
- [x] 1.3 `agents.vue`：控制区两行（新建配置 / 页码文案 + 常驻翻页），引入 `index.style.css`
- [x] 1.4 `agents.vue`：`.ops-section` 间距 8px → `--app-space-md`（16px）
- [x] 1.5 `load()` 后把页码夹回末页，删掉已无消费方的 `.ops-count`
- [x] 1.6 实跑：12 条数据 → 第 1 页 10 行、第 2 页 2 行；首页「上一页」置灰、末页「下一页」置灰；按键到表头间距 69px
- [x] 1.7 `npx vitest run tests/ops-console` 31 用例全绿；`npm run typecheck`、`npm run lint:styles` 无新增问题
