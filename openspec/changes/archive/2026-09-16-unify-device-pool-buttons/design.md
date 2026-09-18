## Context

动机见 `proposal.md - Why`。方案所需的现状约束（均已读码核实）：

- 侧栏「退出」按钮的几何在 `frontend/src/shared/components/AppSidebar.style.css:439-455`：
  `border: 2px solid var(--ink)`、`border-radius: 2px`、`box-shadow: 2px 2px 0 0 var(--ink)`、
  hover `transform: translate(-1px,-1px)` + `box-shadow: 3px 3px 0 0 var(--ink)`；
  `padding: 4px 12px`、`font-weight: 700`。底色 `--comp-sidebar-red` 是**该按钮专有**的语义色，不作为皮肤的一部分。
- 设备管理页的页根为 `.doc-page .doc-page--fixed .wb-shell .device-workbench`（`index.vue:67`），
  因此 `.device-workbench` 是天然的页面作用域锚点。
- 页内按键分属 5 个文件：`index.vue`（视图切换 / 行数 / 翻页 / 工具条）、
  `components/DeviceCard.vue`（卡片操作）、`components/DeviceActionsCell.vue`（表格操作列）、
  `components/NetworkConnectDialog.vue` 与 `components/DisconnectDialog.vue`（弹窗）；
  另有 2 个共享件 `shared/components/FilterTabs.vue` 与 `shared/components/patterns/ErrorState.vue`。
- 共享件被其它页面使用：`FilterTabs` 3 个页面、`ErrorState` 20+ 文件、`.wb-btn` 11 个文件。
- 冲突声明集中在：`DeviceActionsCell.vue:47-57`（`border-radius: var(--app-radius-pill) !important`、`border-width: 1px !important`）
  与其 58-79 行的 `border-color` / `color` 覆写；`DeviceCard.vue:318-340`（`border: 1.5px solid`、`border-radius`、hover `transform: translate(1px,1px)`、`--ghost` 虚线）。
- 硬约束：`frontend-l0-design-tokens` 要求交互文本与自身背景对比度 MUST ≥ `4.5:1`。

## Goals / Non-Goals

**Goals:**

- 设备管理页内所有按键共享**同一套**硬边几何（2px 墨边 / 2px 近直角 / 零模糊偏移硬阴影 / hover 上移）。
- 按键底色按角色分配，切换类有明确的「未选中 / 选中」二态，且选中态与既有分段控件同口径。
- 把几何声明收敛到**一处**，消除页内 5 套并存外观。

**Non-Goals:**

- 不把该皮肤推广到其它页面，不修改共享件与全局主题。
- 不改按钮文案、点击行为、条件渲染（锁定/释放/删除的出现条件）、禁用逻辑与尺寸量级（`min-height` / `padding` 保持）。
- 不改开关（`el-switch`）、标签（`el-tag` / chip / badge）与表格、卡片外壳。
- 不新增设计令牌。

## Decisions

### D1 皮肤承载在页面作用域，而非共享层

在 `DevicePoolView.style.css` 内新起「统一按键皮肤」一节，选择器一律以 `.device-workbench` 起头。

- 备选 1：改 `workbench-theme.css` 的 `.wb-btn` / 新增全局 `.doodle-btn` — 会波及 11 个以上文件的按键外观，与用户「仅设备管理页」的口径冲突，否决。
- 备选 2：给 `FilterTabs` / `ErrorState` 增加 `variant` 属性 — 需要改 2 个共享件 + 2 处调用点，且为本页单消费者发明新 API，属过度设计，否决。
- 备选 3：给页内每个按钮加统一的类名 — 需改 5 个文件的模板，且弹窗按钮仍要额外覆写全局皮肤，收益低于页面作用域选择器，否决。

### D2 用 `:deep()` + `!important` 覆盖子组件与共享件内的按键

页面 scoped CSS 的 `:deep()` 编译为 `.device-workbench[data-v-页] .el-button`，
既能命中子组件内部节点（子组件根继承父级 scope 属性），也能命中 EP 生成的 `.el-button`。

- 必须带 `!important`：`.wb-shell .wb-btn.el-button` 与子组件既有声明同为 `(0,3,0)` 且部分带 `!important`，
  依赖来源顺序不可靠。
- 与之配套：**删除**子组件中与统一几何冲突的 `!important` 声明（`border-radius`、`border-width`、`border-color`、`color`），
  让页面块成为唯一真相源，而不是靠优先级硬碰。子组件的语义 `background` 保留。

### D3 底色按角色分配，文字统一墨色

| 组 | 未选中 / 常态 | 选中 |
| --- | --- | --- |
| 显示行数、全部设备·在线·使用中、表格·卡片 | `var(--c-workflow)` 天蓝 #89CFF0 | `var(--c-dashboard)` 柠黄 #f7c948 |
| 局域网 | `var(--c-element)` 薰衣草紫 #a78bfa | — |
| 刷新 | `var(--c-device)` 薄荷绿 #6bcb77 | — |
| 分页、操作列、卡片操作、弹窗、重试 | 沿用各自既有语义底色 | — |

文字色统一 `var(--ink)`。计算对比度（sRGB 相对亮度法）：
墨色 × 天蓝 10.6:1、× 柠黄 10.6:1、× 薰衣草紫 6.1:1、× 薄荷绿 8.2:1，均 ≥ 4.5:1。

**例外（实测暴露）**：弹窗内未带 `.is-plain` 的实心 `type="danger"` 按钮底色是
`--el-color-danger` = `--color-red-46`（深红 #b23838，`tokens.css:484`），墨字压深红仅 **2.78:1**，
跌破 `frontend-l0-design-tokens` 的 4.5:1。故对 `:not(.is-plain)` 的实心 danger 保留主题既有的浅色文字
（`tokens.css:485` 已注明该底色"白字仍可读"）。这是本设计唯一未统一为墨色的按键，由对比度硬约束决定，
已在 spec 中以独立 Scenario 登记。

- 备选：文字用白色以完全对齐侧栏「退出」— 白字 × 柠黄仅 1.57:1、× 天蓝 1.7:1，直接违反
  `frontend-l0-design-tokens` 的 4.5:1 硬约束，否决（已就此项单独询问并获用户确认取墨色）。
- 选中黄与 `AppTabs` 选中态（`workbench-theme.css:126-129`）同值，保持既有分段控件的口径。

### D4 hover 只位移与加深阴影，不改底

对齐参考按钮（`.logout-btn:hover` 保持 `--sidebar-red` 不变）。因此删除
`.action-bar-btn:hover { background: var(--app-bg-subtle) }` 与 `.card-btn:hover` 的背景覆写；
未命名按键（分页 `.wb-btn`、操作列）的既有 hover 背景保持不变。

### D5 视图切换容器必须同时改造

`.view-toggle` 现有 `border: 1px solid`、`border-radius`、`overflow: hidden`、`.view-btn` 的 `border-right`。
统一后每个按钮自带 2px 实边与偏移硬阴影，`overflow: hidden` 会**裁掉**阴影，容器描边与竖分隔线则与按钮实边重复。
故一并去掉容器描边/圆角/裁剪并改用 `gap`，`.view-btn` 去掉 `border-right`。这是统一几何的必要结果，不是顺带改进。

### D6 卡片「删除」并入实边

`--ghost` 的虚线属"外形"，统一后取消该变体与其类名绑定。破坏性提示仍由文案「删除」与
`DisconnectDialog` 的二次确认承担；卡片删除的底色保持卡片纸色不变（用户口径是"沿用现有语义底色"，不新造 danger 底色）。

### D7 不新增设计令牌

几何字面量与参考按钮逐字一致（`2px`、`2px 2px 0 0`、`3px 3px 0 0`）。
`border-radius: 2px` 已在样式门禁的图形量白名单内；阴影模糊半径为 0；动效走 `--app-duration-fast` / `--app-ease`。
单页单消费方不值得抽 `--comp-btn-*`（"复制，不发明"）。

### D8 显式限定既有冷蓝禁令的范围

`frontend-doodle-content-card` 的「MUST NOT 用冷蓝作为『蓝色』语义」经 delta 明确为只约束**内容卡操作按钮的语义色调**，
切换/分段控件的「未选中」默认态由新能力 `frontend-doodle-button` 规定。不静默忽略该约束。

## 模块防火墙自检

本设计为**纯前端样式与模板**改动，逐条确认：

- 跨 App import：无新增。改动文件全部位于 `frontend/src/modules/device-pool/`，不涉及后端 App。
- 跨 App import service/runner/consumer/state_machine：不适用（无后端改动）。
- INSERT/UPDATE/DELETE 收敛到各 App 的 api.py：不适用（无写库）。
- 前端不直连数据库、仪表盘不做写操作：不适用（无数据访问改动）。
- 无新增依赖、无 API 契约、无路由变更。

## Risks / Trade-offs

- [设备管理页与其它页面按键外观分叉] → 用户明确选择"仅设备管理页"；由 spec「Skin scope is limited to the device-management page」与"其它页面按钮计算样式不变"的验证断言共同守住。
- [页面块与子组件 `!important` 同优先级 → 依赖样式注入顺序] → 直接删除子组件中冲突的 `!important` 声明（D2），使页面块成为唯一来源。
- [2px 边 + 硬阴影使按钮变宽变高，工具条可能换行] → 测量工具条高度与各按钮 `offsetWidth/offsetHeight`；超限只调 `padding`，不动几何。
- [选中态由灰底改黄底后，`FilterTabs` 角标对比度下降] → 角标保持 `--app-bg-card` 底 + 墨色字（`FilterTabs.vue:59-62` 的 active 规则），黄底上仍可读；验证时一并测量角标。
- [卡片删除失去虚线提示] → 二次确认弹窗保留，破坏性由文案与弹窗按钮的 danger 语义承担。
- [`prefers-reduced-motion` 下位移失效] → 位移仅为增强，静态 2px 墨边与硬阴影仍保留可交互性；不依赖位移动效（符合 `frontend-doodle-content-card` 的 reduced-motion 要求）。
