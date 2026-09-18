## Why

上一轮 `rework-inspector-view` 把检查器收敛为单一结构视图并给表格加了勾选，但用户实测后又提出四条显示问题：

1. **无数据时看不到表格**：`StructureAnalysisPanel.vue` 用 `v-if="elements.length"` 包住整张 `AppTable`，没有快照时连表头与列一起消失，只剩一块空态；用户要求表格常驻、空表提示「未选中设备」。
2. **元素表没有分页**：55+ 行的元素表在窄栏里一路滚到底；用户要求参考设备管理页的表格设计，固定 8 行一页并给上一页 / 下一页。
3. **页面分区与设备选择框是过渡形态**：分区仍是纯文本行、设备选择仍是 280px 原生下拉，都没纳入本页已落地的硬边按键皮肤。
4. **Dump/OCR 双方式已无意义**：「仅 OCR」获取方式与「保存到元素定位不写 OCR」互相矛盾，而 OCR 展示链路（手机屏幕框选、页脚与快照列表计数、合并行）在新流程里已无产出。

评审稿：`temps/inspector-redesign-proto.html`（用户已选定变体 **A · 硬边筹码**）。

## What Changes

- **表格常驻**：元素表格始终渲染表头与 8 列；无数据时表体提示统一为「未选中设备」（不再用整块空态替换表格）。
- **固定 8 行分页**：接入共享 `usePagination`，固定 8 行、**不渲染「显示行数」选择器**，显示「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页；上一页 / 下一页常驻（无可翻页时禁用，与设备管理页只在多页时渲染的口径有意不同）；切换分区 / 筛选 / 搜索 MUST 回到第 1 页。
- **表纸沿用共享 `AppTable`**：`accent="var(--c-element)"`（本模块色）+ 表纸线型登记为**实线**，最小高度 = 表头 54 + 8 × 行高。
- **BREAKING（体验层面）去掉抓取方式选择**：工具条不再有「仅 Dump / 仅 OCR」，获取恒以 `dump` 发起。
- **BREAKING（规格层面）OCR 展示链路整体拆除**：手机屏幕 OCR 框选、页脚「N OCR」、快照列表 OCR 计数、`ocrTexts` / `selectedOcr` / `mergedRows`（OCR 合并行）与 `shared/ocrMatch` 的本模块消费全部移除；勾选保存的 `element_ids` 改为直接解析 `checkedIds` 的 `d<下标>` 键。据此 `device-inspector-page` 的「保存到元素定位不写入页面级 OCR」其「检查器侧 OCR 展示 SHALL 保留」条款失效，由新要求「检查器只保留 Dump 链路」承接。
- **需求 3 变体 A 落地**：页面分区改为纵向硬边按键列（未选中天蓝 `--c-workflow` / 选中柠黄 `--c-dashboard` + 元素计数徽标 + 「全部分区」复位项）；设备选择改为硬边触发键 + 纸面下拉（保留 Element Plus `el-select` 的键盘与可达性，仅由页面作用域换皮，见 design.md D6）。
- **明确不做**：不改三栏布局顺序（变体 C 被否）、不改后端与 API 契约（`capture` 的 `method` 入参保留，只是前端不再发 `ocr`）、不改路由、不动设备管理页、不删 `shared/ocrMatch.ts` 与其单测、不新建第二套表格或分页实现。

## 关联文档

- `temps/inspector-redesign-proto.html`：本次评审通过稿（信息架构表 + 变体 A/B/C 可点原型 + P0/P1/P2 + 去重结论），变体 A 已选定。
- `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`：7 端点契约真相源；本次**不改**契约（前端不再发 `method=ocr`，后端入参与 `di_snapshots.ocr_json` 落库不变）。
- `openspec/specs/device-inspector-page/spec.md`：本页能力主 spec，本次经 delta 修改（新增 / 修改 / 移除-承接）。
- `openspec/specs/frontend-l4-data-surface/spec.md`、`frontend-doodle-button/spec.md`、`frontend-doodle-sketch-table/spec.md`：分页消费方、按键肤色、表纸承载页三处同步登记。
- `openspec/changes/archive/2026-09-16-rework-inspector-view/`：上一轮变更（三栏布局 / 按键蓝灰 / 勾选保存 / OCR 落库下线），本次在其基础上继续。
- `dev_docs/ARCH_PRD/PRD-03-设备检查器.md` **不存在**（PRD-00 仍引用该编号），故本次不引用 PRD-03。

## Capabilities

### New Capabilities

（无。本页能力上轮已建立，本次全部为增量。）

### Modified Capabilities

- `device-inspector-page`：新增「抓取方式恒为 Dump」「元素表格常驻与固定 8 行分页」「页面分区筹码与设备选择控件」三条要求；修改「按键可用性以颜色与提示表达」（补设备选择控件的硬边形态）与「元素表格勾选驱动筛减保存」（补分页下的全选口径与跨页勾选）；移除「保存到元素定位不写入页面级 OCR」，并由新增的「检查器只保留 Dump 链路」承接其不落库条款与新的不展示条款。
- `frontend-l4-data-surface`：「Single pagination implementation」的消费方清单补 `device-inspector`。
- `frontend-doodle-button`：「Device-inspector keys adopt the hard-edge skin」补页面分区筹码（切换类：未选中天蓝 / 选中柠黄）的口径。
- `frontend-doodle-sketch-table`：「Sketch table is AppTable paper skin」补设备检查器承载页（模块色 `--c-element`、线型登记为实线）。

## Impact

- 前端页面：`frontend/src/modules/device-inspector/`
  - 新增：`constants.ts`（`PAGE_SIZE_OPTIONS=[8]` / `DEFAULT_PAGE_SIZE=8` / 表头与行高常量 / 表格最小宽 / 空表文案唯一来源）
  - 修改：`index.vue`（去 OCR 触点、设备计数文案）、`store.ts`（去 `captureMethod` / OCR 状态与合并行、`saveToElements` 改直接解析勾选键、`viewSavedPage` 去 OCR 映射）、`components/StructureAnalysisPanel.vue`（表格常驻 + 分页栏 + 分区筹码）、`components/CaptureForm.vue`（去方式选择、设备选择框换皮）、`components/ScreenshotView.vue`（去 OCR 框选与命中测试）、`components/SnapshotListDrawer.vue`（去 OCR 计数与 ocr/both 方法标签）
- 共享件：`shared/ocrMatch.ts` 与其单测**保留**（本模块不再消费，零改动）；`AppTable` / `usePagination` / `EmptyState` / `FilterTabs` / `tokens.css` 只消费不修改
- 后端：**无改动**（无迁移、无契约变更）
- 规格：4 份 delta（见上）
- 测试：`frontend/tests/` 无 device-inspector 用例；验收走 `npm run lint:styles` / `npx vite build` / `npm run typecheck`（报错文件集不得新增）+ Playwright 真机走查四条需求
