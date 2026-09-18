## Context

- 表格皮肤分三层叠加：全局 `frontend/src/style.css:95-111` 定义 `.el-table` 基础皮肤；共享 `frontend/src/shared/styles/workbench-theme.css:129-156` 在其上叠加 `.ac-table` / `.sketch-sheet`；模块再用 `:deep()` 覆写。CSS 层叠中 `!important` 优先于特异性，因此全局带 `!important` 的声明实际压过共享与模块的同类非 `!important` 声明。
- 实测结论（本次改动前）：
  - `workbench-theme.css:133` 的 `.ac-table th { border-bottom: 1px solid var(--app-border-light) }` 与 `:136` 的 `.ac-table td { border-bottom: 1px solid var(--app-border-lighter) }` 均被全局 `!important` 覆盖 —— 属**死声明**，真正生效的是全局「th 2px 墨线 / td 1px 白线」。
  - `style.css:108` 的 `.el-table td { background: var(--app-bg-card) !important }` 使任何写在 `tr` 上的底色不可见。
  - 全仓唯一可用的行选中写法是 `element-locator/components/PageElementsWorkbench.vue:326` 的 `:deep(.page-row--active > td.el-table__cell) { background: … !important }`；`device-pool/index.vue:160` 也在用 `row-class-name` 产出状态行类。
  - `shared/components/AppTable.vue:20,128` 已内置 `rowClassName` prop 并透传给 `el-table:row-class-name`，无需扩展组件即可产出共享行状态类。
- 用户在本次变更前已确认：纸面风格**不画行网格线**，保留不可见效果，只把声明改成语义正确的写法。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- `/inspector` 两个面板的行选中态可见
- 全仓行选中态收敛为唯一共享类名与唯一共享规则
- 表格网格线口径唯一：无可见行/列网格线，且声明语义正确
- 表头排版单一来源（`--app-size-xs` / 700 / uppercase）

**Non-Goals**

- 不重构 `AppTable` 的列生成、分页、表单校验能力
- 不改表格以外组件的外观
- 不为表格新增第二个封装组件
- 不清理 `device-pool` 的状态色条（`row-online` / `row-busy`）与表头居中/内边距等非字号几何

## Decisions

**D1 行状态底色画在单元格（`td`）而非行（`tr`）上**
理由：全局单元格底色带 `!important`，`tr` 底色必被遮盖；且全仓唯一可用实现已用 `td` 承载。
备选：去掉全局 `td` 底色的 `!important` —— 否决。会波及 20 个页面，并可能让 Element Plus 默认底色回流，回归面远大于收益。

**D2 唯一类名 `is-selected`，并兼容 Element Plus `current-row`**
理由：`row-class-name` 已是 `AppTable` 的公开能力，三处站点只需改返回的类名字面量，改动面最小。
备选：为每个模块保留私有类名、只补一条 `> td` 规则 —— 否决。会留下三套同类语义，与「唯一真相源」冲突。

**D3 行状态底色用组件令牌，而非在各处硬编码 `color-mix`**
理由：`tokens.css` 是颜色与规格的唯一登记处。以 `--comp-table-row-accent`（默认 `--c-element`）派生 `--comp-table-row-selected-bg`，模块只需覆写强调色。
备选：三处各写 `color-mix(in srgb, var(--c-element) 18%, …)` —— 否决，复制表达式即埋下漂移。

**D4 行分隔线写作 `transparent`，而非删除声明**
理由：删除会移除 1px 盒高，行高与表高微变；用户已确认「保留不可见效果」。`transparent` 保持几何不变且语义明确。
备选：直接删掉 `border-bottom` —— 否决，会产生可见的 1px 高度变化。

**D5 `device-pool` 表头回归共享皮肤**
理由：`frontend-doodle-sketch-table` 要求表纸语言共享、禁止模块第二套皮肤；现状 `!important` 的 `16px / 800` 是唯一压过全局的表头覆盖。

## Risks / Trade-offs

- [`/devices` 表格观感变化（表头字号回 12px、移除 7 色分栏底线与彩色虚线行线）] → 属用户已确认的一致性收敛方向；tasks 单列浏览器目视回归项，若与设计预期不符可只回退该模块段落
- [共享规则作用域漏挂，选中态再次失效] → 规则同时覆盖 `.wb-shell` 与 `.workflow-workbench`；tasks 在含表格页面逐一确认
- [透明边框在斑马纹行上可能露底] → 全主题恒为浅色（`html { color-scheme: light }`），且全站表格未启用 `striped`；tasks 含斑马纹确认项
- [行选中令牌与 `--app-bg-card` 的 `color-mix` 组合在纸色底上对比不足] → 令牌以 18% 强调色派生，与既有可用实现的观感一致；tasks 含选中态可辨识度确认

## Migration Plan

1. 先登记令牌与共享规则（不改变现有生效样式，可独立验证）
2. 迁移三处行选中实现（改类名 + 删私有规则）
3. 收敛网格线声明（全局 + 共享死声明 + `device-pool`）
4. 统一表头排版（移除 `device-pool` 覆盖）
5. 回滚策略：纯样式变更，回滚即 `git revert` 对应提交；无数据、接口与路由迁移

## Open Questions

（无）