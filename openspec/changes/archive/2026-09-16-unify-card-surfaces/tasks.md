# 任务：统一卡片语言

## 1. report-generator 去双壳（CaseBreakdown）

- [x] 1.1 核实 `CaseBreakdown.vue:138` 页根含 `wb-shell`，确认 `.ac-card` 钉板壳本应生效
- [x] 1.2 核实 `.case-group`/`.bug-case-group` 自建实线大圆角壳 + `.el-card` 剥壳规则构成双壳，且 `overflow:hidden` 裁掉图钉
- [x] 1.3 删除 `.case-group` 壳声明与 hover、`.bug-case-group` 壳声明
- [x] 1.4 删除两条 `.case-group :deep(.el-card)` / `.bug-case-group :deep(.el-card)` 剥壳规则
- [x] 1.5 改动前反证 + 改动后断言的 Chromium 计算样式对比（`temps/card-shell-check.mjs`）

## 2. device-pool `DeviceCard` 改共享 AppCard

- [x] 2.0 核实 `DevicePoolView.style.css:152-162` 的本地 nth-child 微倾/hover/reduced-motion 与 AppCard 抢 `transform`，一并收敛到共享机制

- [x] 2.1 核实状态载体：模板第 56–59 行已有 `.status-chip`（文字 + 三角形/菱形几何 + 三态配色），左侧 4px 色条为冗余的 color-only 第二载体 → 移除不丢信息
- [x] 2.2 口径：`aspect-ratio: 2.2/1` 属卡片布局属性、不在"壳"的范围内，按「只碰必须碰的」保留
- [x] 2.3 改用 `AppCard`：移除 `::before` 左侧色条与 `.busy`/`.offline` 的 `--card-accent` 覆写，壳交由 `.ac-card`；保留点击选中、hover、focus-visible、删除入口与横向比例
- [x] 2.4 浏览器断言：钉板壳特征（虚线/近直角/模块色硬阴影/图钉/微倾）+ 状态仍可辨识（chip 三态）+ 比例未变

## 3. device-inspector 3 处：核实判定

- [x] 3.1 `index.vue:207-219` = `.filter-bar`（过滤工具栏）→ 不是可复用数据块
- [x] 3.2 `StructureAnalysisPanel.vue:261-268` = `.sap-sections`（`overflow-y:auto` 滚动区）→ 不是卡片壳
- [x] 3.3 `SnapshotListDrawer.vue:63-68` = `.snap-item`（抽屉内紧凑列表行）→ 不是卡片壳
- [x] 3.4 结论：审计按样式签名误判；三处不改（改了是视觉回归），并修正审计 §3.7 的口径

## 4. 验证与关单

- [x] 4.1 `npm run lint:styles` → 0
- [x] 4.2 `npx vite build --mode development` → 0
- [x] 4.3 归档关单
