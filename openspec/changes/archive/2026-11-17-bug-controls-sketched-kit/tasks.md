# 任务：BUG 控制区复用 Sketched UI Kit

## 1. 控制区重排与换肤

- [x] 1.1 `index.vue`：分类 `FilterTabs` 移入控制行并置于搜索框左侧，删除独占一行的分区头
- [x] 1.2 控制行挂 `.sketch-kit`，搜索框与状态下拉包进 `.sketch-field`（**不带字段标题**，用途由占位提示表达）
- [x] 1.3 「同步历史错误」改为**紫色渐变填充键**（`--c-element` 派生渐变 + 墨边 + 位移硬影），并移到工具条右端、与「上一页 / 下一页」同一行；「上一页 / 下一页」为填充态：可点＝浅绿填充（`--app-status-success-bg`）+ 墨边 + 硬影，不可点＝灰填充 + 撤影
- [x] 1.4 删除「共 N 张 BUG 单」提示与其样式
- [x] 1.5 字号与间距统一：工具条三处（显示行数 / 分页文案 / 翻页键）与分类 chip 全部 14px；工具条与表格之间加 `--app-space-md`（16px）下边距
- [x] 1.6 分页常驻：去掉 `.page-nav` 的 `v-if="totalPages > 1"` 与 `.page-info` 的 `v-if`，只有 1 页或 0 条时两键同时置灰仍可见

## 2. 留白与字号

- [x] 2.1 `.bug-table-section` 给左右与底部 `--app-space-md` 内边距，表格不再贴边
- [x] 2.2 数据单元格 `padding: 16px`、表头 `12px 16px`；首列编号 16px、时间 12px、正文 14px
- [x] 2.4 列内字号分两档：标题升到 16px（与首列编号同档）；分类 / 关联任务 / 状态 / 「查看」统一 14px
- [x] 2.5 表纸底色改为**天蓝**纵向渐变：渐变换到 `.sketch-sheet` 上（**10% → 5%**，`--c-workflow` 混 `--paper` 降饱和），表体与单元格改透明让渐变透出；hover 改成叠加 `--ink 6%` 浅罩，保证悬停更重
- [x] 2.3 清理被取代的旧规则（`.filter-hint` / `.page-nav-btn` / `.bug-table-section__header`）

## 3. 实现中追加的必要修正
- [x] 3.1 `AppTable` 加 `table-layout="fixed"`：内边距加大后自动布局会把总宽撑出容器，导致「状态 / 操作」列被裁切
- [x] 3.2 列宽按表头文案与内容重算：BUG 编号 200 / 分类 124 / 关联任务 152 / 状态 118 / 操作 112；表头 `.cell` 加 `nowrap`，避免「关联任务」「状态」折行或被省略
- [x] 3.3 翻页键两态补齐：`.bug-page-nav :deep(.doodle-btn.doodle-btn)` 覆盖成浅绿填充；`:disabled` 落灰底、撤影、边框降为 `--app-border-strong`；hover 仅位移不加新色
- [x] 3.4 环形图中心文字居中：`top` 改成按 `BUG_DISTRIBUTION_HEIGHT` 推导的像素锚点（数字 `H/2-9`、标签 `H/2+12`），补偿 graphic.text 按字形盒顶部定位的偏移；像素量测确认数字中心与圆环中心均为 130.5px

## 4. 验证

- [x] 4.1 `npx vue-tsc --noEmit`、`npx eslint src/modules/bug-manager`（0 error）、`npx prettier --check "src/modules/bug-manager/**/*.{vue,ts,css}"` 通过
- [x] 4.2 `npm run lint:styles`：bug-manager 零告警；虚线仍只由 `sketched-kit.css` 声明
- [x] 4.3 `node tests/run.mjs module bug-manager`：2 文件 / 10 用例全绿
- [x] 4.4 真实前端验收 `/bugs`：控制区一行、虚线输入框带字段标题、黄底同步键、虚线翻页键（首页禁用）、无「共 N 张」、单元格 16px 内边距、六列表头完整可读；截图 `temps/shot-bugs-table.png`、`temps/shot-bugs-page2.png`
