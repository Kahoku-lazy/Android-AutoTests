## 1. 实现

- [x] 1.1 `index.vue`：删除 `.ai-usage-kpis` 五卡块，替换为 `AppCard.ai-bill`（标题 + 命中率栏 + 当天行 + 总行）；导入 `SkeletonCard` 与 `formatSignificant`，移除仅旧卡使用的 `IconTarget`/`IconZap`。验证：`vue-tsc` 通过。**验证结果**：tsc 0。
- [x] 1.2 `DashboardView.style.css`：新增 `.ai-bill` 系列样式（标题栏 / 命中率栏 / 两列明细 / 1px 分隔线），移除 `.ai-usage-kpis` 网格。验证：`npm run build:check` 通过。**验证结果**：build 22.1s。
- [x] 1.3 数值口径保持：用量 M / 2 位小数、费用三位有效数字、命中率 1 位小数。验证：代码对照 spec 场景。**验证结果**：`toMillions(...).toFixed(2)`、`formatSignificant(...,3)`、`toFixed(1)`。

## 2. 规格

- [x] 2.1 `dashboard-ai-usage` delta：五张 KPI 卡 → 单张「DeepSeek 账单」卡，含 5 个场景。验证：`openspec validate ai-usage-bill-card --strict`。**验证结果**：valid。

## 3. 门禁

- [x] 3.1 `npx vue-tsc --noEmit`、`npm run build:check`、`npx vitest run tests/dashboard`、`npm run lint:styles`、`npm run lint:lines`。验证：全绿。**验证结果**：tsc 0；build 22.1s；62 passed；批 2 通过（批 3 仍 50 处既有）；虚线 0 处。
- [ ] 3.2 目视：账单卡层级、数字精度与右侧 Agent 卡对齐。验证：用户确认。

## 4. 零件卡风格统一

- [x] 4.1 DashboardView.style.css：抽出 .part-card 外壳（2px 墨线、2px 圆角、无阴影无倾斜、顶边 6px 色条、右上角 52px 黄圆）与 .part-card__head / __hero / __row / __cell 结构，账单卡与 Agent 卡共用。验证：build 通过。**验证结果**：见 5.1。
- [x] 4.2 index.vue：Agent 卡由「编号 + 标题 + 2×2 无分隔网格」改为与账单卡相同的「标题栏 + 两行双列单元格（1px 分隔线）」，编号 01/02；账单卡编号 00、色条取 --c-case。验证：结构一致。**验证结果**：已改。
- [x] 4.3 账单卡副标识 DEEPSEEK 加 margin-right: 40px 让开右上角黄圆。验证：渲染检查。**验证结果**：mock 中不再被遮挡。

## 5. 统一后的门禁

- [x] 5.1 
px vue-tsc --noEmit、
pm run build:check、
px vitest run tests/dashboard、
pm run lint:styles、
pm run lint:lines。验证：全绿。**验证结果**：tsc 0；build 通过；62 passed；批 2 通过；虚线 0 处。

- [x] 4.4 角标同色系：.part-card::after 由固定黄改为 color-mix(in srgb, var(--part-accent) 28%, var(--paper))，顶边紫色则角标淡紫、顶边青绿则角标淡青绿。验证：build 19.6s、62 用例通过、虚线 0 处。**验证结果**：全绿。

- [x] 4.5 整体缩小一号：头/主指标/单元格纵向内距 16 → 8、标题 18 → 16、主指标 32 → 24、单元格数值 20 → 16、右上角黄圆 52 → 40、副标识让位 40 → 30。验证：build 24.4s、62 用例通过、批 2 通过、虚线 0 处。**验证结果**：全绿。

- [x] 4.6 宽度与标题栏：账单列 536 → 460、Agent 区上限 860（两列各约 422）；标题栏上下内距 8 → 12（space-sm + space-xs），避免标题被压扁。验证：build 23.2s、62 用例通过、虚线 0 处。**验证结果**：全绿。

- [x] 4.7 阴影统一：去掉零件卡的无阴影设定，改为与上方 KPI 卡同格式的 4px 4px 0 0 var(--part-accent) 硬偏移；hover 抬 1px + 5px 阴影。验证：build 21.3s、62 用例通过、虚线 0 处。**验证结果**：全绿。

- [x] 4.7 去顶边色条 + 浅色渐变阴影：删除 .part-card::before 顶边 6px 色条；阴影改为同色相三层（42% / 20% / 8% 混纸白，偏移 4/8/12px），只在右下；hover 抬 1px + 5/9/13px。验证：build 29.0s、62 用例通过、虚线 0 处。**验证结果**：通过。

- [x] 4.8 淡灰白描边 + 顶中图钉：.part-card 描边由 ink 改为 color-mix(ink 12%, paper)，overflow 改 visible；新增 ::before 12px 图钉（accent 填充 + 2px ink 圈）居中于上边沿。验证：build 18.7s、62 用例通过、虚线 0 处。**验证结果**：通过。

- [x] 4.9 章节板改标准矩形：去掉 ch-ops/ch-ai/ch-asset/ch-trend 的 4 处 rotate；下内距 space-sm(8) → space-lg(24)，给卡片 12px 右下阴影留空间；银灰硬阴影保留。验证：build 18.9s、dashboard 测试通过、批 2 通过、虚线 0 处。**验证结果**：通过。

- [x] 4.10 编号改 SVG 徽标：新增 components/PartNumber.vue（22×22 圆角方框 + 数字文本，颜色取 --part-accent），账单卡显示 00、Agent 卡显示 01/02；标题栏 align-items baseline → center。验证：build 28.7s、62 用例通过、虚线 0 处。**验证结果**：通过。

- [x] 4.11 数值渐变 + 单位黑色：Agent 卡 token 由 toLocaleString 改为 K/M 两档（tokenValue/tokenUnit），费用 formatSignificant 3 位 + 元；.part-card 数值（hero/cell b）使用同色相 90deg 渐变 background-clip:text，单位 em 强制 --app-text-primary 黑字。验证：build 21.4s、62 用例通过、虚线 0 处。**验证结果**：通过。
