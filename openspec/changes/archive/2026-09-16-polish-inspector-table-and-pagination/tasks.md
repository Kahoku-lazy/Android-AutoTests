## 1. ① 快照删除二次确认

- [x] 1.1 `SnapshotListDrawer.vue` 的 `onDelete` 接 `ElMessageBox.confirm`（危险态 + 「不可恢复」文案），确认后才调 `store.deleteSnapshot`；取消（reject）直接 return；验证：真机确认框文案为「删除快照 / 删除后该快照与其截图 / 缩略图文件不可恢复 / 取消 / 删除」；点取消 **0 次 DELETE**，点删除 **1 次 DELETE**（请求被 mock 拦截，未真删）✅
- [x] 1.2 重复点击不产生并发删除；验证：确认框为 EP 模态（点击期间阻塞），真机连续操作只产生一次请求 ✅

## 2. ② 共享分页自动夹取

- [x] 2.1 `shared/composables/usePagination.ts` 加 `watch(totalPages, …)` 夹取并补注释；验证：`npm run typecheck` 无新增报错 ✅
- [x] 2.2 真机复核设备管理页：开发调试注入 60 台（12 页）→ 翻到**第 4 页** → 关闭注入（2 台 / 1 页）→ 显示「第 1 / 1 页 · 共 2 台」且表格 2 行非空 ✅（设备页本身没有回页 watch，行为只能来自共享件）
- [x] 2.3 真机复核设备检查器：第 3 页 → 切分区 / 搜索 → 页码有效且表格非空（面板自身的 goPage(1) 保留）✅

## 3. ⑤ 悬空令牌修复

- [x] 3.1 `ai-assistant/ToolDebugPage.style.css` 的 `var(--app-bg)` → `var(--app-bg-input)`（`.td-input` 是输入框，语义最近）；验证：`grep -rn "var(--app-bg)" frontend/src` 命中 0；`npm run lint:styles` **退出码 0**（原 G5 悬空引用红灯消除）✅

## 4. ④ 列宽与间距集中登记

- [x] 4.1 `constants.ts` 增 `ELEMENT_COLUMN_WIDTHS`（8 列）与由其求和的 `TABLE_MIN_WIDTH_PX`；`ELEMENT_COLUMNS` 改引用；验证：组件内不出现列宽数字字面量，真机列宽仍为 40/66/120/140/120/150/200/150 ✅
- [x] 4.2 新建 `frontend/src/modules/device-inspector/tokens.css`（作用域 `.inspector-workbench`，值 = 原字面量）并在 `main.ts` 与其它模块令牌一起导入；验证：`lint:styles` 批 2/批 3 通过；`--insp-gap-row` 计算值为 10px ✅
- [x] 4.3 把 `.sap-pager` / `.sap-body` / `.sap-chip` / `.sap-webview-hint` / `.sap-sections-title` / `.sap-name-input` / `.sap-enlarge-detail` 与 `index.vue` 工具条 / 筛选栏 / 页脚 / CaptureForm / 抽屉的裸间距改为令牌引用；验证：真机量得分页栏 38px / 下内边距 10px / 行间距 10px / 面板间距 12px / 筹码 6px 与 6px 8px，与登记前逐一相等 ✅

## 5. ③ 拖拽平移与首列冻结

- [x] 5.1 `useTableDragScroll` 提升为 `shared/composables/useTableDragScroll.ts`（支持传入外部滚动容器），`DevicePoolView.logic.ts` 改 import；验证：`grep -rn "device-pool/composables/useTableDragScroll"` 命中 0；`/devices` 表格拖拽平移仍生效 ✅
- [x] 5.2 检查器元素表接同一 composable：拖拽目标为 EP 自身的横向滚动容器 `.el-scrollbar__wrap`（`watchPostEffect` 在数据到位后解析），外层只定高；配套 CSS 给滚动容器 grab/grabbing 光标、拖动时 `pointer-events: none`、滚动条皮肤；验证：真机按住拖动后 `scrollLeft 0 → 180`、容器类名含 `is-dragging is-pan-ready` ✅
- [x] 5.3 首列冻结：前 3 列（选择 / 缩略图 / 元素名称）用 EP 原生 `fixed: 'left'`（EP 2.x 以单元格 sticky 实现），表格 `table-layout="fixed"` + 内层表格 `min-width = 列宽合计`；验证：容器 `scrollWidth 986 > clientWidth 627`，滚到 `scrollLeft 359` 后冻结三列 x 仍为 550/590/656，其余列由 776/916 移到 417/557 ✅
      （踩坑记录：`position: sticky` 自绘方案无法穿透 el-table 自身的 overflow 容器，故改用 EP fixed；`.el-table` 上设 min-width 会让 EP 认为无需滚动，min-width 必须落在内层 `table` 上）
- [x] 5.4 冻结列底色逐状态正确、拖动后不误触行选中、复选框/名称输入仍可操作；验证：普通=白、斑马纹=暖色 tint、选中=`--comp-table-row-selected-bg`（三种底色互不相同且均由 EP fixed 单元格继承）；拖动 180px 后未产生行选中；表格内复选框、名称内联编辑未受影响 ✅

## 6. 门禁与真机验收

- [x] 6.1 `npm run lint:styles` **退出码 0**（全仓绿）；`npx vite build` 退出码 0（1m41s）；`npm run typecheck` 30 errors / 4 文件，**device-inspector 0 条**（较变更前无新增）✅
- [x] 6.2 Playwright 真机走查并截图：删除确认取消 / 确认、页码夹取（设备页 60→2 台）、拖拽平移、首列冻结三态底色 → `temps/polish-report.json`、`temps/shot-polish-*.png`；控制台 0 error / 0 pageerror ✅
- [x] 6.3 用 skill `vue-frontend-check` 过门禁并出三块报告（见关单消息，含 `/devices` 与 `/inspector`）：本轮修掉了既有缺陷 1（🟠 危险删除无确认）并把「间距裸 px」从 🟡 收敛为已登记令牌；无本次引入的 🔴/🟠 ✅
- [x] 6.4 `openspec validate polish-inspector-table-and-pagination` → `valid: true`；真机结论与 spec Scenario 一一对应 ✅
      （实施中修正两处：① `--insp-*` 初版写在 `:root` + `<style scoped>@import`，实测令牌不生效 → 改为按仓库既有惯例在 `main.ts` 导入并作用域到 `.inspector-workbench`，同时避开「`:root` 引入模块私有变量」的既有量规；② 面板是纯 JS SFC，误写 TS 泛型 `ref<HTMLElement | null>()` 会被当成比较表达式，导致运行时 `Cannot create property 'value' on number '0'` → 已去掉泛型。）
