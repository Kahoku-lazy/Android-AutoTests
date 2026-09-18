## Context

参考：`temps/hand-drawn-doodle-sidebar.html` `#page-typography` `.panel`。原型：`temps/doodle-appcard-panel-prototype.html`。评审确认：同排 cycle；P0 = AppCard 换皮 + 仪表盘趋势 4 张 + 已用 AppCard 的报告卡自动换皮；ECharts 画布色允许硬编码。

## Goals / Non-Goals

**Goals:**

- AppCard 钉板壳为 L3 数据块唯一默认皮肤
- 同排 cycle accent / tilt（复用 sketchCard helpers）
- 仪表盘趋势去掉裸 el-card
- 文档写明 ECharts 硬编码例外

**Non-Goals:**

- 不改 SketchCard / KpiCard / DeviceCard
- 不改 ECharts option 配色算法
- 不把 `.doc-section` 做成钉板
- P1（知识库、设备池 table-card、登录卡跟皮）本轮可不强制

## Decisions

### 1. 升级 AppCard，不新建第三容器

- **选择**：扩展 `AppCard.vue` props（`tone` / `tilt` / `pin`），主题写在 `workbench-theme.css` + 收敛 `style.css` 顶条。
- **理由**：L3 判据已指定 AppCard；再建 PanelCard 会双实现。

### 2. cycle 由父级注入

- **选择**：父级 `sketchToneAt(i)` / `sketchTiltAt(i)` 传入；仪表盘四张趋势显式 index 0..3。
- **理由**：与 SketchCard 一致，组件无列表上下文。

### 3. ECharts 色板例外

- **选择**：壳用令牌；ECharts option 内字面量色保留，文档登记例外。
- **理由**：用户明确：图表主题独立设计，允许硬编码。

### 4. hover / motion

- **选择**：钉板 hover = 回正 + 硬阴影略抬；收窄 `motion.css` 对 `.wb-shell .el-card` 的模糊抬升，避免与钉板冲突。

## Risks / Trade-offs

- 登录页 AppCard 无 `.wb-shell`：本轮可不跟皮（P1）；若目视突兀再补登录页局部样式。
- 全局 `.el-card` 规则仍在 `style.css`：仪表盘改走 AppCard 后趋势块吃 `.ac-card`；其它裸 el-card 暂保留旧实线，后续另单收敛。
