## 1. store 口径改造（单一视图 / 自动分区 / 勾选行键）

- [x] 1.1 删除 `store.ts` 的 `viewMode` 状态、其导出与两处赋值（`applySnapshot` / `analyzeSnapshot`）；验证：`grep -n "viewMode" frontend/src/modules/device-inspector` 无命中 ✅（残留命中仅在 device-pool / ai-assistant 各自模块）。
- [x] 1.2 `analyzeSnapshot()` 与 `viewSavedPage()` 写入 `analysis.elements` 时补 `_idx` 与 `_rowKey = 'd' + _idx`；验证：浏览器里勾选 3 行后保存请求体 `element_ids=[0,1,2]`（temps/inspector-save-report.json）✅。
- [x] 1.3 抽出筛选/搜索 helper `applyFilters(els)` 并新增 `filteredAnalysisElements`；顺带删除随元素列表下线的死计算 `filteredElements` / `filteredRows`（原任务写的是保留 filteredElements，实际两个都已无消费方，删除以免留死代码）；验证：结构表格筛选/搜索生效、`npm run typecheck` 报错文件集与变更前一致（仅 tests/dashboard、store.ts、ProjectTree.vue）✅。
- [x] 1.4 `viewSavedPage()` 用映射后的元素构造 `analysis = { is_webview: false, sections: [], elements }`；验证：浏览器打开已保存页面 → 表格 5 行、分区列「暂无分区数据」、指标列 `—` ✅。
- [x] 1.5 `viewSnapshot()` 在 `applySnapshot()` 之后追加 `await analyzeSnapshot()`；验证：抽屉选快照后自动出现 4 个分区（App头部 8 / 系统状态栏 19 / 内容区 24 / 系统导航栏 4）与 55 行表格，无需再点按键 ✅。
- [x] 1.6 在 `store.ts` 导出 `KEY_DISABLED_MESSAGE` 与 `notifyKeyUnavailable()`；验证：`index.vue` 与 `CaptureForm.vue` 两处调用该方法，仓内无第二份同文案字面量 ✅。

## 2. 结构面板：选择列 + 空分区兜底

- [x] 2.1 `StructureAnalysisPanel.vue` 增加 `_select` 列（表头全选 + 每行复选框），复用 `store.checkedIds` / `store.toggleCheck()`；验证：浏览器点复选框不触发行选中，勾选态计数 1 → 3 ✅。
- [x] 2.2 `allChecked` 判定与 `toggleAll` 只作用于当前所示行；验证：勾选 3 行后表头全选框未误选其余行（勾选计数 3，全选后为 55）✅。
- [x] 2.3 结构面板骨架**常驻**（不再由 `sections.length` / `elements.length` 决定整块显隐）：分区列无数据时列内显示「暂无分区数据」，表格无数据时列内显示「暂无元素数据 / 获取 Dump 快照后显示页面元素」；验证：无快照时左列分区空态与右列表格空态同时在位（temps/shot-inspector-default.png）✅。
      （原任务写的是「整块渲染条件由 sections.length 改为 elements.length」——实测该写法在无快照时会让分区列整块消失，与需求 1「默认显示所有内容」冲突，故改为骨架常驻。）

## 3. 页面布局与按键（index.vue / CaptureForm.vue）

- [x] 3.1 删除 `PageElementsPanel` 的引用与「结构分析」「返回元素列表」两个按键；验证：工具条只剩「获取 / 历史快照 / 已保存页面 / 保存到元素定位」，两个切换键选择器命中 0 ✅。
- [x] 3.2 三栏布局：`.workspace` 改 `minmax(0, 2.4fr) minmax(0, 1fr)`（左 = 结构面板、右 = 手机屏幕）；验证：1600px 下 页面分区 x=284 / 表格 x=548 / 手机 x=1203（左→中→右）；1100px 下手机落到下一行 y=657，堆叠顺序 分区→表格→手机（temps/shot-inspector-narrow.png）✅。
- [x] 3.3 `.filter-bar` 去掉 `v-if="store.snapshot"`，元素计数改用 `filteredAnalysisElements` / `analysis.elements`；验证：无快照时筛选栏与 8 个筛选项可见，计数为「55/55 元素」✅。
- [x] 3.4 按键底色按可用性分配（可用 `--c-workflow` rgb(137,207,240) / 不可用 `--color-ink-79` rgb(201,202,204) 且 opacity 1、box-shadow none），灰键 `aria-disabled` + click 守卫，删除 `.action-btn--primary` 墨黑底，hover 规则排除灰键；验证：真实 DOM click 灰键弹出「按键不可用，请先选择设备」且不打开弹窗、不发请求 ✅。
- [x] 3.5 「保存到元素定位」可用条件收紧为 `!!store.snapshot?.snapshot_id`；验证：已保存页面回看（无 snapshot_id）时该键灰底并提示，不打开弹窗 ✅。
- [x] 3.6 删除 `components/PageElementsPanel.vue`；验证：`grep -rn "PageElementsPanel" frontend/src` 无命中（仅一处注释已改写），构建通过 ✅。
- [x] 3.7 前端门禁：`npm run lint:styles` 退出码 0；`npx vite build` 退出码 0（built in 2m56s）；`npm run typecheck` 报错文件集与变更前一致（无新增）✅。
- [x] 3.8 用 skill `vue-frontend-check` 逐项过校验门禁：静态扫描 + 浏览器（Playwright 真实走查）三块报告见本次关单记录；缺陷均为既有项（快照删除无二次确认 🟠 等），无本次引入的 🔴/🟠 ✅。

## 4. OCR 落库下线（前端开关 + 后端入参 + 存量清理）

- [x] 4.1 `SaveToElementsDialog.vue` 删除「OCR 数据」`el-switch` 与 `includeOcr` 状态（含 `watch` 重置）；验证：浏览器打开弹窗 `el-switch` 计数 0、弹窗文案不含「OCR 数据」✅。
- [x] 4.2 `store.ts` 的 `saveToElements()` 删除 `include_ocr`、`hasOcrChecked` 与类型声明；验证：拦截到的请求体为 `{page_label, folder_path, element_ids:[0,1,2]}`，无 `include_ocr` ✅。
- [x] 4.3 `views.py` 删 `include_ocr` 读取与传参、`api.py` 删形参并恒传 `ocr_json=None`（docstring 同步）；验证：`manage.py check` 通过、`ruff check/format` 通过、`grep -rn include_ocr apps/` 无命中 ✅。
- [x] 4.4 新增 `apps/element_locator/migrations/0014_clear_page_ocr_json.py`（逐行判断后置空，`reverse=noop`）；验证：`makemigrations --check --dry-run` 无缺失；`migrate` 应用 OK；`NON_EMPTY_AFTER 0`（本机 `el_pages` 迁移前非空 0 行，备份写入 temps/el_pages_ocr_backup.json）✅。
- [x] 4.5 后端门禁：`python manage.py check` ✅ · `python -m ruff check/format --check apps/device_inspector apps/element_locator` ✅ · `pytest -m "unit or integration"` **281 passed, 46 deselected** ✅（首次运行在受限沙箱下出现的 7 failed/11 errors 属 PermissionError 类沙箱artifact，放宽后再跑全绿）。
- [x] 4.6 同步 `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`（删 `include_ocr` 行 + 补「页面级 OCR 不再随保存写入」说明）；验证：`grep -rn include_ocr dev_docs/` 无命中 ✅。

## 5. 需求验收

- [x] 5.1 需求 1：无快照下打开 `/inspector` → 工具条 / 筛选栏（8 项）/ 页面分区（标题+空态）/ 元素表格（空态）/ 手机屏幕 五块同时在位；截图 temps/shot-inspector-default.png ✅。
- [x] 5.2 需求 2：未选设备时「获取」与无快照时「保存到元素定位」均为灰底 rgb(201,202,204)、opacity 1、无位移阴影，真实点击弹出「按键不可用，请先选择设备」；载入快照后「获取/历史快照/已保存页面/保存到元素定位」为天蓝 rgb(137,207,240) ✅。
- [x] 5.3 需求 3：三栏顺序 页面分区（最左 x=284）→ 元素表格（x=548）→ 手机屏幕（x=1203）；点分区切换表格行数生效；截图 temps/shot-inspector-checked.png ✅。
- [x] 5.4 需求 4：元素列表页与两个切换键不存在；勾选 3 行后保存请求体 `element_ids=[0,1,2]`（拦截并中止，未写真库，避免污染元素定位数据）；未勾选时仍提示先勾选（既有守卫未改）✅。
- [x] 5.5 OCR 落库下线：保存弹窗无 OCR 开关、请求体无 `include_ocr`、`GET /api/inspector/pages/{id}` 对应数据迁移已置空；「仅 OCR」展示链路（手机屏幕 OCR 框选、页脚 OCR 计数、快照列表 OCR 计数）未改动 ✅。
- [x] 5.6 前端门禁复跑 + skill `vue-frontend-check` 记录（见 3.8）✅。
