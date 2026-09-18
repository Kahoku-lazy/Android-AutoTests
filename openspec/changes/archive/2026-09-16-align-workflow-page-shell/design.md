## Context

- `workflow/index.vue:381` 的页根是 `<div class="doc-page workflow-workbench">` —— 全仓 20 个页根中唯一缺 `.doc-page--fixed` 与 `.wb-shell`（同模块 `PrototypeList.vue:69` 为 `doc-page doc-page--fixed wb-shell proto-list-page`）。
- 共享样式 `workbench-theme.css:5-9` 的选择器是 `.wb-shell, .workflow-workbench`，但 `--ac-font` / `--ac-ink` **只**在 `modules/workflow/tokens.css` 的 `.workflow-workbench` 内声明 → 对其余 20 个 `wb-shell` 页根而言两条声明在 computed-value 阶段失效，回落为继承值（因 `body` 已设 `font-family` / `color`，当前"恰好"看不出问题，属静默失效）。
- `workbench-theme.css:91` 的 `.wb-shell .ac-card .ac-card__pin { box-shadow: 1px 2px 0 0 var(--ac-pin-shadow) }` 同理：`--ac-pin-shadow` 只在 `.workflow-workbench` 声明 → dashboard / report-generator / ai-assistant 的 `AppCard` 图钉（共 15 处消费）得到 `box-shadow: none`。**这是可观察的跨模块渲染差异**。
- `workflow/tokens.css` 内 `--ac-accent` 声明两次（第 19 行 `var(--c-workflow)`（注释：工作流天蓝）、第 36 行 `var(--c-dashboard)`）→ 后者生效；因 `AppCard` 会内联注入 `--ac-accent`（`AppCard.vue:60`），当前无可见影响，属潜伏缺陷。
- `workflow/index.vue:481,484` 的 `height: 100%` / `overflow: hidden` 被 `App.vue:67-72` 的 `.main-content__body :deep(.doc-page)` 编译为 `.main-content__body .doc-page`（特异性 0,2,0）覆盖为 `height:auto; overflow:visible` → 两条声明失效（`style.css:163-165` 已明文说明此现象）。页面实际高度由 flex 链（`flex:1; min-height:0`）给出，滚动由 `.wb-body` 内层容器承担。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- workflow 两个页根都满足 `frontend-l2-page-region` 的骨架与主题作用域要求
- 共享皮肤不再依赖任何模块作用域令牌；`AppCard` 图钉硬阴影在各模块一致可见
- `--ac-accent` 只声明一次且与模块色登记一致
- 归零消费方的模块令牌与失效声明不残留

**Non-Goals**

- 不改 `workflow/index.vue` 已登记的 `.wb-body` 画布容器例外（`frontend-l2-page-region` 明文允许）
- 不重构 workflow 自建的 `.wf-btn` / `.mini` / `.btn` 四套按钮皮肤（变更 15）
- 不清退 `workflow/tokens.css` 其余零消费令牌（变更 14）
- 不改 workflow 的节点与浮层几何、圆角字面量（变更 10）

## Decisions

**D1 共享皮肤改用共享/主 token，而不是把 `--ac-font` / `--ac-ink` 提升到 `:root`**
理由：`--ac-font` / `--ac-ink` 只是 `--app-font` / `--ink` 的同值转发，本身无模块语义；提升到 `:root` 会违反「模块令牌作用域保持在模块页面根类」（禁止提升为全局），而改用共享 token 是从根上消除依赖。
备选：把两条令牌移入 `tokens.css` 的 `:root` —— 否决（同名令牌出现在全局与模块两处，语义混淆）。

**D2 图钉硬阴影登记为 `:root` 的共享组件令牌 `--comp-ac-card-pin-shadow`**
理由：`.ac-card` 是共享组件 `AppCard` 的根类，其图钉阴影属"通用组件配色"，按 `tokens.css` 既有命名口径（`--comp-<组件>-<场景>`）应落在 `:root`；`tokens.css` 已有 `--comp-kpi-pin-shadow` 可作先例。
备选：直接在 `workbench-theme.css` 写 `var(--ac-pin-shadow, var(--color-ink-05-a18))` 兜底 —— 否决：兜底掩盖了跨模块作用域问题，且把字面量色源写进共享皮肤。

**D3 页根补 `.doc-page--fixed` 与 `.wb-shell` 一并做**
理由：`frontend-l2-page-region` 要求每个 L2 页根复用骨架并提供工作台主题作用域；两者是同一条要求的两半，分开做会让页面处于"半合规"状态。
风险与边界：`.wb-shell` 的 `box-sizing` 规则对 workflow 后代**已有等价覆盖**（`workbench-theme.css` 的选择器同时含 `.workflow-workbench *`），故无布局变化；`.wb-shell` 的字体/颜色规则在本变更 D1 后与 `body` 同值。

**D4 删除失效声明 `height:100%` / `overflow:hidden`**
理由：两条已被 `App.vue` 高特异性规则覆盖，保留会误导维护者以为滚动由它们承担（`style.css:163-165` 已把这种写法列为"失效声明"）。页面高度由 `display:flex; flex-direction:column` + `min-height:0` 与外壳 flex 链给出，删除后行为不变。
备选：保留并加注释 —— 否决：项目已有专门清理失效声明的先例。

## Risks / Trade-offs

- [补 `.wb-shell` 后 workflow 编辑器页首次获得共享皮肤，可能出现未预期的样式命中] → 该页当前无 `.ac-card / .ac-tabs / .ac-table / .sketch-sheet / .wb-btn` 元素（唯一例外是本次要加 `wb-btn` 的两个对话框按钮）；tasks 含对本页 class 与共享皮肤选择器的交叉核对
- [删除 `height:100%` 后若特异性分析有误会导致页面高度塌陷] → 已核实 `App.vue:67-72` 的 `:deep(.doc-page)` 编译为 (0,2,0) 高于 `.workflow-workbench` 的 (0,1,0)；tasks 含构建与浏览器断言，若异常则回退该两条
- [图钉阴影改为共享令牌后，workflow 若将来使用 `AppCard` 会失去"天蓝图钉影"] → 图钉影色本就是中性墨色（`--color-ink-05-a18`），不承载模块色语义；模块色由 `--ac-accent` 承担

## Migration Plan

1. 先在 `tokens.css` 登记共享图钉令牌，再改 `workbench-theme.css`，最后清理 `workflow/tokens.css` 与页根
2. 回滚策略：纯样式与 class 改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）