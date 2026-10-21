## 上下文

仪表盘四个章节头使用同一套 `.chapter-head` + `.chip-row` 结构。「平台运营」右侧是设备/智能体/任务/工作流四枚 chip；「AI 用量」右侧是角色·累计与角色·今日两枚 chip，数据由 `DashboardView.logic.ts` 的 `roleBreakdown` 从 `ai_usage.by_role` 计算。「测试资产」右侧也有一枚「用例 N」chip，使用相同的 `.chip`/`.chip--teal` 样式，本次不在删除范围。

## 目标 / 非目标

- 目标：删除截图标记的两条章节头 chip 行，并清掉只为角色 chip 存在的前端计算与样式。
- 非目标：不改统计接口与 `by_role` 字段，不改 KPI 卡，不删除「测试资产」用例 chip，不改章节顺序与视觉主题。

## 决策

- 直接删除两段 chip DOM，而不是加 `v-if` 隐藏。数据与展示都不再需要，保留隐藏节点只会留下死结构。
- `roleBreakdown`、`ROLE_LABELS` 与返回类型中的 `roleBreakdown` 一并删除；它们没有其它消费者。`ai_usage.by_role` 仍保留在接口与 DTO 中，避免破坏既有契约。
- 删除失去唯一消费者的 `.chip--yellow`、`.chip--rose`、`.chip--violet` 修饰类；保留 `.chip-row`、`.chip`、`.chip--teal` 供「测试资产」用例 chip 使用，保留此前已无消费者的 `.chip--pink` 以缩小本次 diff。
- 900px 媒体查询中的 `.chip-row` 规则保留，因为测试资产章节仍在使用。

## 风险 / 权衡

- 章节头右侧变为空白，`chapter-head` 的左右分栏仍成立（左侧自适应），不会把标题挤变形；需浏览器确认窄屏堆叠。
- 分角色 Token 不再出现在仪表盘首屏，需要该信息时仍可通过接口或智能体页查看。

## 迁移计划

- 仅前端展示层删除，无数据迁移；回滚即还原 `index.vue`、`DashboardView.logic.ts`、`DashboardView.style.css` 与对应单测。

## 开放问题

- 无。
