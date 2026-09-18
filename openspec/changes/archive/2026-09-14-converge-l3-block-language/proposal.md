## Why

L3 块层缺一条可判定的选择判据，且现有两处口径**互相冲突**：`frontend/AGENTS.md` 的 AppCard 判据写「把一组内容框成『块』就用它」（等于「块就用 AppCard」），而 2026-09-14 的裁决口径是「页面级分区用 `.doc-section`、可复用数据块用 AppCard」。实测 9 个文件 58 处 `.doc-section` 与 8 个文件 AppCard **并不存在真实冲突**（全部是「分区 ⊃ 数据块」的合法嵌套，或认证卡 / 条目卡），真正的问题是**判据缺失 + 文档口径冲突**——后续页面只能靠模仿，容易各写各的。

## What Changes

- 在 spec 中登记块语言判据：**页面级分区**（页头之下承载整段内容、含自有标题 / 说明的顶层块）→ 骨架块 `.doc-section`；**可复用数据块**（图表卡 / 表格卡 / 指标卡 / 认证卡 / 条目卡）→ 组件块 `AppCard`；二者组合形态为「`.doc-section` 分区内嵌 AppCard 数据块」
- 修正 `frontend/AGENTS.md` 中冲突的一句话判据：由「把一组内容框成『块』就用它」改为按**角色**二分的判据，并保留「单条数据的卡片（设备卡 / 任务卡）用模块私有组件」
- 登记 `AppCard` 的使用前提：外观仅在工作台外壳 `.wb-shell` / `.workflow-workbench` 内生效，脱离即退化为 Element Plus 默认 → 用它做块时页面根必须带主题锚点
- 产出**逐页判定表**（11 处顶层块 + 8 个 AppCard 消费方），作为判据落地的证据
- **不改任何代码**：判定表显示现有实现已符合判据，无迁移项（避免为「看起来整齐」而制造可见变化）
- **BREAKING**：无

## 关联文档

- L3 现状复盘：`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L3现状复盘.html`（§二 块 · §五 第 5 条 · §六 步骤 ③）
- 前端口径：`frontend/AGENTS.md`「跨模块共享文件：shared/」的 AppCard 段（判据冲突所在）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档；属口径登记，无接口变更

## Capabilities

### New Capabilities

- `frontend-l3-content-block`: L3 内容块的角色判据与组合规则 —— 页面级分区 / 可复用数据块 / 认证卡 / 条目卡的选型、允许的嵌套形态，以及 AppCard 的主题作用域前提

### Modified Capabilities

（无；L2 / L0 契约的行为要求不变）

## Impact

- 文档：`frontend/AGENTS.md`（AppCard 段的一句话判据）
- spec：新增 `openspec/specs/frontend-l3-content-block/spec.md`
- 代码：**无**（判定表证明现有 9 文件 58 处 `.doc-section` 与 8 文件 AppCard 已合规）
- 验证：`rg` 顶层块分布与判定表逐条对齐 + `npm run typecheck` + 构建（基线确认）+ `vue-frontend-check`
- 不影响：路由、API、鉴权、样式与页面观感
