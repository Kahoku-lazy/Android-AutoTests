## Context

- 漂移根因：`2026-09-21-fix-inspector-table-highlight` 只带了 `device-inspector-page` 一个 delta，而同一句话在 `frontend-l4-data-surface`（每页 8 行、行选中手势）与 `frontend-doodle-button`（设备选择触发键配色）里各有一份副本；该变更的 design.md 风险段已自述「主规格里『固定 8 行』与『触发键天蓝底』在归档前仍是旧文」，但只替换了自己那一份。
- 另有一处更早的过期描述：`device-inspector-page`「元素表横向滚动可用与首列冻结」仍写「由外层容器横向滚动」，而实现已在 `2026-09-16-polish-inspector-table-and-pagination` 的 tasks 5.2/5.3 中途从「sticky 自绘 + 外层滚动」改为「EP `fixed` + 元素表自身滚动容器承载，外层只定高」。
- 待核对的现状（本变更的输入）：`frontend-l4-data-surface/spec.md:46-49`（8 行 / `PAGE_SIZE_OPTIONS=[8]`）、`:93-97`（点击一行）、`frontend-doodle-button/spec.md:85`（触发键按可用性配色）、`device-inspector-page/spec.md:297`（外层容器）、`:316`（间距一律 `--insp-*`）。
- 约束：`device-inspector-page` 已于 2026-09-21 改为 7 行、白底触发键、双击数据格，代码与之一致；本变更**不回退**这些已交付口径。
- 约束：`frontend-l0-design-tokens` 已有「同一值的字面量声明恰好出现一次」取向；`device-inspector/tokens.css` 头注释自述「只登记不在 T0 刻度（4/8/16/24/32/48）上的值」。

## Goals / Non-Goals

**Goals:**

- 消除 3 组 live 规格互相矛盾，使「以 spec 为准」的验收可执行
- 把行数、手势、触发键外观各自归口到**唯一** capability
- 让 `device-inspector-page` 的间距登记口径与模块自身惯例一致，且可被静态检索判定
- 给本次漂移的复发点加一条可执行的检索校验（防复发）

**Non-Goals:**

- 不改任何已交付外观与行为（唯一代码改动是 8px → `var(--app-space-sm)` 的等值替换）
- 不修 `SavedPagePicker.vue` 的 `999px` 圆角（属代码违规，另作前置修复）
- 不新增「已保存页面回看显示 alias」的要求（属新增需求，另开变更）
- 不动 `purge-inspector-dead-code` 的任何内容

## Decisions

**D1 `frontend-l4-data-surface` 去掉写死的每页行数，而不是把 8 改成 7**
理由：同一数字在两份 capability 里各登记一次，正是本次漂移的复发点。跨模块 capability 只约束「选项集来自模块 `constants.ts`、只登记单一取值、该取值与默认行数相等」；具体行数由拥有该页面的 `device-inspector-page`「元素表格常驻与固定 7 行分页」钉住。
备选：把 l4 的 8 直接改成 7 → 否决：下次调行数仍要改两处，同步只能靠人记，等于保留病根。

**D2 `frontend-l4-data-surface` 的行选中场景去掉手势词**
理由：该 requirement 的实质是行状态底色的**画法**（画在 `> td.el-table__cell` 上、带 `!important`、唯一类名 `is-selected`），与「单击还是双击」正交。把手势写进 L4，等于让每次调手势都制造一次伪漂移。
备选：把 l4 的「点击一行」改成「双击数据格」→ 否决：把手势固化到第二个位置，同一问题换个方向复发。

**D3 设备选择触发键的配色归口到 `device-inspector-page`**
理由：触发键是「始终可用的白底控件」，本就不属于「工具条按键可用性天蓝 / 灰」这套分配；两个 capability 同时定义同一外观必然再次分叉。`frontend-doodle-button` 保留它真正负责的两件事：硬边几何、由页面作用域覆写。
备选：把 `device-inspector-page` 的白底改回天蓝 → 否决：与已交付实现及用户已确认外观冲突（该外观已由 2026-09-21 变更加入主规格）。

**D4 横滚承载者写成「元素表自身的横向滚动容器」**
理由：实现（EP `fixed` 冻结前 3 列 + el-table 内部 `.el-scrollbar__wrap` 承载横滚 + 外层 `.sap-table-body` 只定高）已是归档记录在案的最终方案；用户可见行为（拖拽平移、首列冻结、冻结列不透明）三项不变量不变。spec 原文的「外层容器」来自被否决的 sticky 自绘方案。
备选：改代码回到「外层容器滚动」→ 否决：会让 EP `fixed` 与拖拽目标互斥（归档 tasks 5.3 已记录该踩坑：sticky 无法穿透 el-table 自身 overflow 容器）。

**D5 间距登记按 T0 刻度分层**
理由：模块 `tokens.css` 头注释已自述「只登记不在 T0 刻度上的值」；spec 原文只说「来自 `--insp-*`」与实现惯例不一致，也使 `StructureAnalysisPanel.vue` 里新出现的裸 `padding: 0 8px` 处于「按原文违规、按惯例合规」的模糊地带。写清分层后，该类裸值变成可判定违规。
备选：为 8px 新增一个 `--insp-*` 令牌 → 否决：会在 T0 刻度上造出与 `--app-space-sm` 同值的第二真相源，与 l0 的「同一值单一登记」取向相悖。

**D6 由 D5 导出的 2 行代码修正并入本变更**
理由：若只改 spec 不改代码，归档后主规格立刻与代码不符——正是本变更要消除的病。改动为等值令牌替换（`0 8px` → `0 var(--app-space-sm)`），零行为变化；且该文件其它规则（`.sap-sections` / `.sap-chip`）已使用 `var(--app-space-sm)`，改后内部一致。
备选：把 2 行另开一个代码变更 → 否决：会让规格与代码在两个变更之间处于不一致状态，且该改动小到不值得单独走一遍流程。

## 模块防火墙自检

- 跨 App import：零新增、零改动（3 份规格 + 1 个前端组件内的等值令牌替换）
- 跨 App import service/runner/consumer/state_machine：不涉及
- INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无后端改动）
- 前端不直连数据库 / 仪表盘只读：不涉及
- HTTP 出口：不变（无请求改动）
- 共享层与令牌：不动 `shared/**`、不动 `shared/styles/tokens.css` 与模块 `tokens.css`；只改消费处引用
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [l4 去掉具体数字后「每页几行」在跨模块层面失去约束] → 具体数字仍由 `device-inspector-page`「元素表格常驻与固定 7 行分页」钉住；l4 只守「单一来源 + 单值 + 与默认行数同源」
- [「主规格被手改、delta 只覆盖部分 capability」的病复发] → tasks 增加全仓规格一致性检索（「每页 8 行」/`PAGE_SIZE_OPTIONS=[8]`/l4 的「点击一行」/doodle-button 的触发键配色句/「外层容器横向滚动」），命中必须为 0；归档时逐份核对 3 个 capability 的合并结果
- [2 行代码改动与在途编辑冲突] → `StructureAnalysisPanel.vue` 正处于在途编辑中（本次复核期间 mtime 多次变化）；apply 前确认文件稳定，改动仅落在两处 `padding` 声明
- [门禁无法判定] → `npm run lint:styles` 当前因 `SavedPagePicker.vue` 的 `999px`（G13）红灯；该处须先改为 `var(--app-radius-pill)`，已在 tasks 登记为前置条件
- [D1 削弱了 l4 场景的可验收性] → 该场景改为可静态判定：「`PAGE_SIZE_OPTIONS` 只登记单一取值」「该取值 = 默认行数」「页面内无行数字面量」三条均可检索/断言

## Migration Plan

1. 写回 3 份 delta → `openspec validate align-inspector-spec-drift --strict` 通过
2. 改 2 行代码（等值令牌替换）
3. 门禁：全仓规格一致性检索 → `npm run lint:styles`（前置修 999px）→ `npx vite build`
4. 归档：把 3 份 delta 写入对应主规格后，逐份核对无重复 requirement、无残留旧文
5. 回滚：全部为文本改动，`git revert` 即可；无数据迁移、无部署顺序

## Open Questions

（无）
