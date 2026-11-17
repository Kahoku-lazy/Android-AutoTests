# 任务：BUG 表对齐设备表的列结构

## 1. 列定义与表头

- [x] 1.1 `constants.ts` 的 `BUG_TABLE_COLUMNS` 改为 6 列：删除 `created_at`、每列加 `icon`、`bug_no` 宽度加到 190
- [x] 1.2 `index.vue` 用 `v-for` 生成六个 `#header-<prop>` 插槽，渲染「图标 + 列名」；实测表头为 `🐞BUG 编号 / 🏷分类 / 📝标题 / 🔗关联任务 / 🚦状态 / 💬操作`

## 2. 首列身份单元

- [x] 2.1 新增 `components/BugIdentityCell.vue`：图标圆（🐞）+ `BUG 编号`（主）+ `formatBugTime`（副），props 只接 `bug`
- [x] 2.2 `index.vue` 的 `#cell-bug_no` 改为调用该组件，删除内联 `code.bug-no` 与 `#cell-created_at` 插槽

## 3. 表纸与列线

- [x] 3.1 `index.vue` 的 `AppTable` 关闭 `border`；实测 `el-table--border` 类不存在，无竖直列线
- [x] 3.2 `index.style.css` 增加 `.bug-workbench :deep(.sketch-sheet){ box-shadow: none }`；实测表纸 `box-shadow: none`、描边仍为 `1px solid rgb(201,202,204)`、圆角不变
- [x] 3.3 清理失效的 `.bug-no` / `.bug-time` 样式（抽屉用的是自己 scoped 的样式，未受影响）

## 4. 验证

- [x] 4.1 `npx vue-tsc --noEmit`、`npx eslint src/modules/bug-manager`、`npx prettier --check "src/modules/bug-manager/**/*.{vue,ts,css}"` 全部通过
- [x] 4.2 `npm run lint:styles`：bug-manager 零告警（全仓仍因 `modules/task-list/**` 既有 G5 悬空引用为红，与本变更无关）
- [x] 4.3 `node tests/run.mjs module bug-manager`：2 文件 / 10 用例全绿
- [x] 4.4 真实前端验收 `/bugs`：六个表头带图标、首列图标圆 + 编号 + 时间、无列线、表纸 `box-shadow: none`；`/reports` 探针仍为 `4px 4px 0 rgb(124,111,131)`；截图 `temps/shot-bugs-table.png`、`temps/shot-bugs-page2.png`
