## 1. 模块常量与分页接线

- [x] 1.1 新建 `constants.ts`（`PAGE_SIZE_OPTIONS=[8]`、`DEFAULT_PAGE_SIZE=8`、`TABLE_HEADER_HEIGHT_PX=54`、`TABLE_ROW_HEIGHT_PX=64`、`TABLE_MIN_WIDTH_PX=986`、`EMPTY_TEXT.noDevice`）；验证：行数只声明在 constants.ts，页面内无行数字面量 ✅
- [x] 1.2 面板接 `usePagination(activeElements, …)`，`AppTable` 的 `data-source` 改 `pagedItems`；验证：真机 106 行时「第 1 / 14 页 · 共 106 条」、首屏恰好 8 行、第 2 页首行内容变化 ✅
- [x] 1.3 补「回第 1 页」缺口：`watch([activeRole, () => props.elements], () => goPage(1))`；验证：翻页后切换分区 → 「第 1 / 3 页 · 共 20 条」（分区内 20 条）✅
- [x] 1.4 表纸与分页栏：`accent="var(--c-element)"` + `:striped="true"` + 页面作用域 `.sketch-sheet { border-style: solid }`（线型登记）；分页栏照抄设备管理页右半、**不渲染**「显示行数」；验证：真机外框 `solid 2px rgb(30,30,36)` + `rgb(167,139,250) 4px 4px 0 0`、圆角 `2px 6px 2px 4px`，无「显示行数」字样 ✅
      （另修正：`共 N 条` 初版误用全量 `elements.length`，切分区后显示 106 而非 20 → 改为 `activeElements.length`，已真机复核）

## 2. 表格常驻与空表文案

- [x] 2.1 去掉 `AppTable` 的 `v-if`，空态改走 `#empty` 插槽（`EmptyState :text="EMPTY_TEXT.noDevice"`）；验证：无快照时表头 8 列齐备（选择 / 缩略图 / 元素名称 / 标识 / 元素 / 指标 / XPATH / BOUNDS）、表体「未选中设备」、分页「第 1 / 1 页 · 共 0 条」且上下页禁用 ✅
- [x] 2.2 筛选/搜索无匹配落到同一空态；验证：搜索 `zzz-no-such-element-zzz` 后表体仍为「未选中设备」、分页「第 1 / 1 页 · 共 0 条」✅

## 3. 去抓取方式选择（需求 4 前半）

- [x] 3.1 `CaptureForm.vue` 删 `METHODS` 与 `el-radio-group`；`store.ts` 删 `captureMethod`、`capture()` 固定 `'dump'`；验证：真机 `.cap-form .el-radio-group` 计数 0；实际抓取请求体 `{serial: "R5CT62RH88F", method: "dump"}` ✅
- [x] 3.2 未选设备时「获取」仍为灰键 + 点击提示、忙碌态仍用原生 `disabled`；验证：灰键 `aria-disabled="true"`、DOM click 只触发提示不发请求（`captureBodies` 为空）✅

## 4. OCR 展示链路拆除（需求 4 后半）

- [x] 4.1 `store.ts` 删 `matchOcrToElements` / `ocrTexts` / `selectedOcr` / `mergedRows` / `selectOcr` / `ocr_count`+`texts` 映射 / 成功提示 OCR 数字；验证：`grep -in ocr store.ts` 仅剩 1 行说明性注释；`npm run typecheck` 中 store.ts 报错 **4 → 0** ✅
- [x] 4.2 `saveToElements` 改为直接解析 `checkedIds` 的 `'d<下标>'` 键（带类型守卫）；验证：勾 3 行 → `element_ids=[0,1,2]`；第 1 页全选(8) + 第 2 页勾 2 → `element_ids=[0..9]`，无「退化为保存全部」✅
- [x] 4.3 `index.vue` 删 `onOcrClick` / `:ocr-results` / `:selected-ocr` / `@click-ocr` / 页脚 OCR 段 / 副标题「与 OCR」；验证：页脚为「就绪 / 106 元素 / R5CT62RH88F · com.govee.home」✅
- [x] 4.4 `ScreenshotView.vue` 删 `ocrResults`/`selectedOcr` props、`click-ocr` emit、OCR 绘制段、两个 watch 与 `hitTestOcr`；验证：`grep -n "ocrResults|hitTestOcr|click-ocr"` 无命中；历史 OCR 快照仅绘制元素框选 ✅
- [x] 4.5 `SnapshotListDrawer.vue` 行内去掉「· OCR N」（`METHOD_LABELS` 保留 `ocr` 兜底历史快照的方法名）；验证：抽屉行只显示「元素 N」✅

## 5. 变体 A：分区筹码与设备选择控件（需求 3）

- [x] 5.1 `.sap-sections` 改纵向硬边筹码（`button` + `aria-pressed` + 计数徽标）、顶部「全部分区」复位；验证：真机 5 个筹码（全部分区 106 / App头部 20 / 系统状态栏 14 / 内容区 53 / 底部导航 19），未选中 `rgb(137,207,240)`、选中 `rgb(247,201,72)`；键盘聚焦 + Enter 可切换；点「全部分区」恢复 共 106 条 ✅
- [x] 5.2 设备选择触发键换皮（`el-select` 保留、浮层不换皮）；下拉项文案补「在线 / 使用中」；验证：触发键 `rgb(137,207,240)` + 2px 墨边 + 2px 圆角 + 2px 硬阴影；点开 2 项含「· 在线」；选定后触发键显示所选设备、`获取` 转为可用蓝键 ✅
- [x] 5.3 键盘可达自检：`el-select` 内含 `INPUT.el-select__input`（tabIndex 0，Tab 可达），筹码为原生 `button`；验证：DOM 探针确认 `focusables=[INPUT.el-select__input:0]`，筹码 Enter 切换选中态 ✅
      （说明：headless 下对 wrapper 直接按 Enter 不展开下拉，属 Element Plus 内部键盘实现，与本次只换 CSS 无关；Tab 可达性与鼠标/键盘选项选择均已验证）

## 6. 门禁与验收

- [x] 6.1 前端门禁：`npx vite build` **退出码 0**（49.23s）；`npm run typecheck` 30 errors / 4 文件，**device-inspector 0 条**（较变更前少 4 条，无新增）；`npm run lint:styles` **退出码 1** —— 唯一硬门禁失败来自他人未跟踪文件 `ai-assistant/ToolDebugPage.style.css:132` 的悬空 `var(--app-bg)`（全仓唯一引用，非本次引入、按「只清理自己造成的混乱」未改）；本模块零违规、裸色字面量计数未增 ✅（附注）
- [x] 6.2 Playwright 真机走查四条需求（`temps/inspector2_check.cjs` / `inspector2_crosspage.cjs` / `inspector2_final2.cjs`）：表头常驻 + 「未选中设备」+ 0 条禁用 / 8 行翻页 + 共 N 条 / 筹码配色与计数 + 复位 / 无 Dump-OCR 选项 + 页脚抽屉无 OCR + 保存无 `include_ocr` + 抓取 `method=dump`；截图 `temps/shot-inspector2-*.png`；控制台 0 error（仅我主动 abort 保存请求那一次产生 2 条网络 error）✅
- [x] 6.3 用 skill `vue-frontend-check` 逐项过门禁并出三块报告（见关单消息）：§7 强制扫描全跑；本模块无新增 🔴/🟠；既有 1 项 🟠（快照删除无二次确认）与 3 项 🟡 已登记 ✅
- [x] 6.4 `openspec validate rework-inspector-table-and-controls` → `valid: true`；四条需求真机结论与 spec Scenario 一一对应 ✅
