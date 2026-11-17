# 任务：模型配置页常驻翻页 + 去掉无用横条

- [x] 1.1 `constants.ts` 新增 `OPS_MODEL_PAGE_SIZE = 10`
- [x] 1.2 `model-configs.vue`：`page` / `totalPages` / `pagedConfigs` / `goPage`，表格数据改 `pagedConfigs`
- [x] 1.3 `model-configs.vue`：控制区两行（搜索 + 新建 / 页码文案 + 常驻翻页），计数下沉到页码文案
- [x] 1.4 `model-configs.vue`：关键字变化回第 1 页；`load()` 后页码夹回末页；`.ops-section` 间距 16px
- [x] 1.5 `table.style.css`：隐藏 `el-scrollbar__wrap` 的无用横向溢出
- [x] 1.6 实跑：12 条 → 第 1 页 10 行、第 2 页 2 行；首页「上一页」置灰、末页「下一页」置灰；正文与 chip 均 14px；横条消失
- [x] 1.7 `npx vitest run tests/ops-console` 全绿；`npm run typecheck`、`npm run lint:styles` 无新增问题
