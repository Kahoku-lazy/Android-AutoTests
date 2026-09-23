## Context

动机见 `proposal.md`。现状：`WorkbenchCrumbs` 在 `.wb-crumbs` 内按 DOM 顺序先画 `.wb-crumbs__back` 再画 `.wb-crumbs__list`，flex 默认把芯片挤在左侧。页头契约（`frontend-l2-page-region`）禁止把回退放进 `.wb-header`。用户点选的是元素定位项目工作台的「← 返回项目列表」，该页只是共享件的一个消费方。

## Goals / Non-Goals

**Goals:**

- 在共享件内完成横向排布：祖先链左、返回芯片右。
- 保持现有 props、路由、reduced-motion 与令牌皮肤不变。

**Non-Goals:**

- 不把芯片改到 `WorkbenchHeader` `#actions`。
- 不改各模块 `backTo` / `backLabel` / `items` 数据。
- 不改 Doodle Craft 令牌或芯片视觉皮肤。

## Decisions

### D1：改共享件，不单改 locator 页

- **选择**：只改 `WorkbenchCrumbs.vue` 的模板顺序与 flex 对齐。
- **理由**：所有传入 `backTo` 的页面共用同一零件；单页覆盖会复制布局、与其它子页不一致。
- **备选**：仅在 `ProjectWorkspace.vue` 用绝对定位或额外 wrapper — 否决，范围碎、其它页仍左对齐。

### D2：列表在左、芯片在右，靠 `margin-left: auto` 推到行尾

- **选择**：模板改为先 `.wb-crumbs__list`、后 `.wb-crumbs__back`；芯片 `margin-left: auto`，条 `width: 100%`（已有）。仅芯片时同样靠右。
- **理由**：DOM 顺序与视觉一致（先读祖先再读回退）；`space-between` 在只有芯片时无法保证靠右。
- **备选**：保留芯片在前 + `order` 调视觉 — 否决，Tab 顺序与画面相反。备选把芯片放进页头 — 否决，违反现有 spec。

## 模块防火墙自检

- 跨 App import：不涉及后端。
- 禁止跨 App import service/runner/consumer/state_machine：不涉及。
- INSERT/UPDATE/DELETE 收敛到 api.py：本变更无写库。
- 前端不直连数据库：无新 HTTP。
- 无新跨模块依赖。

## Risks / Trade-offs

- [窄屏换行后芯片可能落到第二行右端] → 保留现有 `flex-wrap`；不引入绝对定位，避免与正文重叠。
- [消费页对「芯片在左」的视觉快照] → 本仓现有 P0 只断言文案与点击；补一条布局断言（芯片在列表之后 / 带靠右样式），不扩页面 E2E。
