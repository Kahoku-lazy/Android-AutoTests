## Why

设备检查器上一轮在途改动（设备选择触发键改白底、元素表每页 8 行改 7 行、行选中改双击数据格）**只带了一个 `device-inspector-page` delta**，落在其它 capability 里的同一句话没有同步；另有一处横向滚动机制描述自实现转向后一直未回写。结果是：3 组 live 规格互相矛盾（两份 spec 对同一件事各说一套），1 处 spec 与实现不符。规格互相矛盾时“以 spec 为准”的验收无法执行——审查者无法判定哪一份是权威。本变更只做规格收敛（外加由收敛后口径直接导出的 2 行代码修正），不改任何既有实现行为。

## What Changes

- `frontend-l4-data-surface`「Single pagination implementation」：`Fixed page size still comes from module constants` 场景**去掉写死的每页行数**，改为只约束“单一取值 + 取值与默认行数同源 + 只在模块 `constants.ts` 登记”。跨模块 capability 不再钉具体数字，具体行数仍由 `device-inspector-page` 钉住——消除本次漂移的复发点
- `frontend-l4-data-surface`「Table row state stays visible」：`Selected row is highlighted` 场景的触发由“点击一行”改为“某行处于选中态”，把手势从该 capability 解耦（该 requirement 的实质是行状态底色的**画法**，与手势无关）
- `frontend-doodle-button`「Device-inspector keys adopt the hard-edge skin」：把**设备选择触发键**从“工具条可用性天蓝 / 灰”这一配色口径中移出，改为其外观由 `device-inspector-page` 定义（白底、无阴影、墨线边框）；保留“由页面作用域统一覆写”与硬边几何
- `device-inspector-page`「元素表横向滚动可用与首列冻结」：承载者由“外层容器横向滚动”澄清为**元素表自身的横向滚动容器承载，外层容器只负责定高**（与已归档实现一致），三项不变量（拖拽平移 / 首列冻结 / 冻结列不透明）不变
- `device-inspector-page`「元素表列宽与间距集中登记」：登记口径按刻度分层精确化——**不在 T0 间距刻度（4 / 8 / 16 / 24 / 32 / 48）上的取值**登记为模块 `--insp-*` 令牌，**落在 T0 刻度上的取值**引用共享 `--app-space-*` 令牌；场景补上 `padding: 0 8px` 这一裸值样例
- 由上一项直接导出的代码修正（2 行，无行为变化）：`StructureAnalysisPanel.vue` 的 `.sap-label-hit` 与 `.sap-name-cell` 内 `padding: 0 8px` → `padding: 0 var(--app-space-sm)`，与该文件其它规则（`.sap-sections` / `.sap-chip` 已用 `var(--app-space-sm)`）一致
- **BREAKING**：无（全部是把规格写回既有实现 / 澄清口径；唯一代码改动是等值令牌替换）

## 明确移出本变更范围

- `SavedPagePicker.vue` 的 `border-radius: 999px`（`npm run lint:styles` 当前唯一红灯，违反 `frontend-l0-design-tokens`「可见盒子的圆角取自不对称规格令牌」）：属**代码修**，不属规格漂移；建议就地改为 `var(--app-radius-pill)` 后另行验收（本变更的门禁任务以此为前置条件）
- 已保存页面回看不显示已存 `alias`（后端 `get_page_full` 已返回该字段，`store.viewSavedPage` 未映射）：需要**新增**一条可验收要求并改代码，与本次“收敛既有矛盾”性质不同，另开变更
- `purge-inspector-dead-code`（零消费死代码清退）：并行的另一个变更，本变更不重叠

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 相关归档变更：`2026-09-21-fix-inspector-table-highlight`（白底触发键 / 每页 7 行 / 双击数据格的主规格来源，只带 `device-inspector-page` 一个 delta）、`2026-09-16-polish-inspector-table-and-pagination`（横向滚动机制转向的记录）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 「Single pagination implementation」去掉写死的每页行数、「Table row state stays visible」的行选中触发与手势解耦
- `frontend-doodle-button`: 「Device-inspector keys adopt the hard-edge skin」中设备选择触发键的配色归口
- `device-inspector-page`: 「元素表横向滚动可用与首列冻结」的承载者澄清、「元素表列宽与间距集中登记」的刻度分层口径

## Impact

- 规格 3 份（均为 MODIFIED delta，归档时写回主规格）：`frontend-l4-data-surface`（2 条要求）、`frontend-doodle-button`（1 条要求）、`device-inspector-page`（2 条要求）
- 代码 1 个文件 2 行：`frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue`（等值令牌替换）
- 后端 / 接口 / 路由 / 依赖 / 迁移 / store：零改动
- 观感与行为：零变化（规格收敛不改实现；2 行是等值替换，`--app-space-sm` = 8px）
- 恢复方式：规格与代码均为文本改动，`git revert` 即可；无数据迁移