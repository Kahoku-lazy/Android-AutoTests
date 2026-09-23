## Context

- **现状链路**：`SnapshotListDrawer.vue:51-58`（`el-button size="small" text type="danger" data-testid="snapshot-clear"`）→ 渲染出 `is-text`；`index.vue:225-241` 的页面皮肤选择器 `.inspector-workbench :deep(.el-button:not(.is-text):not(.is-link))` 因此**不命中**它。
- **几何基准**：侧栏 `AppSidebar.style.css:430-446` 的 `.logout-btn`（`background: var(--sidebar-red)`、`2px solid var(--ink)`、`border-radius: 2px`、`color: var(--app-bg-card)`、`box-shadow: 2px 2px 0 0 var(--ink)`、hover `translate(-1px,-1px)` + `3px 3px`）。
- **已有先例**：元素定位文件详情页 `LocatorFileView.vue:171-196` 把同一套几何搬到 `.file-view` 作用域，并给出危险红变体（`background: var(--app-marker-red)`、`color: var(--app-bg-card)`）。
- **令牌**：`--app-marker-red`（共享 `tokens.css:343` = `--color-red-69` = `#f56b6a`）跨模块可用；`--el-color-danger`（`tokens.css:486` = `--color-red-46` = `#b23838`）是 EP 实心 danger 的底色；`--color-ink-79` = `#c9cacc`（浅灰，页面灰键既有取值）；`--color-white` / `--app-bg-card` 为浅色文字。
- **对比度实测（真浏览器计算样式 + WCAG 相对亮度）**：`--app-marker-red` + 白字 = **2.92:1**（参考键与元素定位「删除」键的现取值，低于 4.5:1）；`--app-marker-red` + 墨字 = 5.68:1；`--el-color-danger` + 白字 = **5.97:1**；灰 `--color-ink-79` + 墨字 = 10.11:1。
- **不可用态现状**：抽屉在无快照时用原生 `disabled`（`SnapshotListDrawer.spec.ts:73-85` 已固化「禁用时不弹确认、不发请求」）。

## Goals / Non-Goals

**Goals:**

- 「一键清空」在启用态与不可用态都与设备检查器页的硬边皮肤一致，且危险语义一眼可辨。
- 复用页面作用域既有几何，不新造第二套皮肤。

**Non-Goals:**

- 不改动清空/确认的行为语义（仍原生 `disabled`、仍先确认）。
- 不改动行内删除图标键（text 型图标键按规格保持无底无边）。
- 不改`.action-btn` 工具条按键、共享件与全局主题。
- 不追求与侧栏「退出」键**逐属性**一致（字号 / 内边距仍取本页口径）。

## Decisions

**D1 去掉 `text`，让按键回到页面皮肤既有选择器，而不是为 text 键开例外。** 依据：页面皮肤之所以排除 text / link 型，是因为本页把 text 型当**图标键**用（规格 `frontend-doodle-button` 明令 text 型图标键 MUST NOT 被套上边框、背景与硬阴影）。「一键清空」是带文字标签的动作键，本就该走皮肤。备选：保留 `text` + 用 `[data-testid="snapshot-clear"]` 单独覆写 → 否决（把测试钩子变成样式钩子，且要为「带标签的 text 键不算图标键」做辩解）。

**D2 底色取 `--el-color-danger`（深危险红 #b23838），不照抄参考键的 `--app-marker-red`（#f56b6a）。** 依据：实测 `--app-marker-red` + 白字仅 **2.92:1**，跌破本 capability 第 25 行与第 97 行都写明的 4.5:1 门槛 —— 参考键与元素定位「删除」键当前都处在这一缺口里。**已与用户确认取深危险红**。备选：① 照抄参考键色值 → 否决（明知低于自家规格）；② 保留浅红改墨字（5.68:1）→ 否决（文字色与参考键及两处先例都不同款）。先例：设备管理页 `DevicePoolView.style.css:131-136` 正是「EP 实心 danger 深红 + 浅色字」这一口径。

**D3 文字用 `--color-white`（浅色）而不是 `--ink`。** 依据：深红底 + 墨字只有 2.78:1；规格 `frontend-doodle-button:25` 已写明深色底按键的文字 SHALL 用主题浅色令牌。与 device-pool 先例同口径。

**D4 不可用态走本页灰键口径（灰底 + 撤位移阴影 + `opacity: 1`），不保留 EP 的浅粉文字。** 依据：本页不可用态的既有表达就是灰底 + 无阴影（`index.vue:273-281`），一个红底禁用的按键会读成「可点」。备选：沿用 EP 的 disabled 危险样式 → 否决（正是用户反馈的观感问题）。

**D5 行为不动。** 依据：本单是样式同步；确认流程与禁用语义已有用例固化，改动会牵到 `device-inspector-page` 的确认要求。备选：把禁用改成 `aria-disabled` + 点击提示 → 否决（本页那条口径写在「工具条按键」下，且会改变既有测试所锁的行为）。

## 模块防火墙自检

- **前端 HTTP 出口**：零改动（清空仍走 `apiClearSnapshots`）。
- **共享件 / 全局主题**：不改。
- **跨模块令牌**：只用共享 `tokens.css` 的 `--app-marker-red` / `--color-ink-79` / `--app-bg-card` / `--ink`。
- **后端**：零改动。

## Risks / Trade-offs

- [危险红规则落到 `.el-button--danger` 会影响同页其它危险实心键] → 已核实本页只有两处 `type="danger"`：清空键（本单覆盖）与行内删除键（text 型，被 `:not(.is-text)` 排除）；`ElMessageBox` 的确认按钮在 body 之外，不在本页作用域。
- [去掉 `text` 后内边距 / 字号与侧栏「退出」键不完全相同] → 几何（边框 / 圆角 / 阴影 / hover 位移）与配色已对齐；字号与内边距仍取本页 12px 口径，与工具条按键一致。若需逐属性对齐，另开一单。
- [既有用例锁的是「禁用时不弹确认」] → 行为未改，用例应保持通过；新增断言只加「不带 text、带 danger」一条（并与行内删除键的 text 型做对照）。
- [视觉上与参考键的红不同款（深一档 #b23838 vs #f56b6a）] → 已与用户确认：参考键的红 + 白字只有 2.92:1，达不到本 capability 自有的 4.5:1 条款，故取深危险红。**参考键（侧栏「退出」）与元素定位「删除」键的 2.92:1 缺口是既有问题，登记待另单处理**，本单不改它们。

## Open Questions

无。
