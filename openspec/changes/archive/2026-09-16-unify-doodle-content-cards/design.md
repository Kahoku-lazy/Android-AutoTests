## Context

- 现状：`AgentRouteCard.vue`、`TaskBoard.vue` 内 `.task-card` 为模块私有实线圆角卡；操作混用自定义 button 与 `el-button` / `ConfirmButton`。
- 目标 DNA：`temps/hand-drawn-doodle-sidebar.html` deco-card（Tape Strip）、sticky.do、`.btn` 三色。
- 原型：`temps/prototype-doodle-content-cards.html`。
- 已落地 `KpiCard` 只覆盖指标，不承担内容列表卡。动机见 `proposal.md`。

## Goals / Non-Goals

**Goals:**

- 共享 `DoodleNote`（note / sticky）+ `DoodleBtn`（danger / teal / yellow）
- AI 助手两处改为薄包装；删除确认仍用 `ConfirmButton`
- 文档与规格同步，便于其它模块后续复用

**Non-Goals:**

- 不改 `KpiCard` / `AppCard` / 页头 `wb-btn`
- 不批量换皮设备卡、用例卡、报告条目（共享件就绪即可跟，本轮不做）
- 不改后端任务/助手 API
- 不把「蓝色」做成冷蓝 `#0066ff`

## Decisions

### 1. 新建内容卡，不扩 KpiCard

- **选择**：`DoodleNote.vue` 独立于 `KpiCard`。
- **理由**：指标卡与内容/任务卡信息结构不同；扩 KpiCard 会破坏已归档 KPI 契约。
- **备选**：只改 AI 私有 CSS —— 其它模块无法复用。

### 2. 双变体而不是两个组件

- **选择**：`variant="note" | "sticky"`，sticky 再加 `status`（ok / run / fail / wait）映射底色与阴影色。
- **理由**：同一壳、插槽放业务内容；状态多彩不复制组件。
- **备选**：`DoodleSticky.vue` 与 `DoodleTapeCard.vue` 分文件 —— 短期清晰、长期双套阴影/胶带逻辑。

### 3. 按钮独立组件

- **选择**：`DoodleBtn.vue`，`tone` 映射模版 Primary/Teal/Highlight。
- **理由**：卡内外都可复用；页头 `wb-btn` 保持工作台顶栏契约。
- **删除**：`ConfirmButton` 保留确认流，默认插槽或外观接到 `DoodleBtn` danger，避免再包一层 EP danger。

### 4. 本轮消费方

- **选择**：仅 `AgentRouteCard` + `TaskBoard` 条目。
- **理由**：用户指定的两处 DOM；共享件 API 按通用插槽设计（title / default / actions）。

## 模块防火墙自检

- 纯前端 `frontend/`；无跨 App ORM/写操作；仪表盘与后端契约不变。
- 无新后端依赖。

## Risks / Trade-offs

- [卡片网格倾角] 相邻卡微倾可能重叠 → 网格 gap 保持现有 `var(--app-space-md)`，overflow 可见胶带。
- [ConfirmButton + DoodleBtn] 二次确认样式可能仍带 EP → 实现时只换触发按钮外观，对话框走现有 EP。
- [字号 11px] 徽章沿用现有 `xs` 档；按钮用 13px 避免低于门禁。

## Migration Plan

1. 落地共享两组件 + 单测。
2. 改 AI 助手两处调用。
3. 同步技能文档。
4. 回滚：还原三个 Vue 文件即可。

## Open Questions

（无；方案 B 与原型已确认。其它模块换皮另开 change。）
