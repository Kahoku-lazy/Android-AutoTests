## Context

动机见 `proposal.md - Why`。这里只列实现所需的当前状态与约束（均为读码核实，非推测）：

- `.action-btn` 的样式声明**逐字重复在两处**：`index.vue:264-272`（`<style scoped>`）与
  `CaptureForm.vue:48-57`（后者多一条 `--primary`）。二者都是普通 `<style scoped>`，
  **不是 ` :deep()`** —— 因此 `index.vue` 的 `.action-btn` 规则够不到 `CaptureForm` 内部的按钮，
  这正是重复的来源。
- 页面根为 `.inspector-workbench`（`index.vue:50`，与 `.wb-shell` 同一元素）。
- `CaptureForm.vue` **仅被 `index.vue` 引用**（全仓只有一处 import 与一处使用），故可安全地把皮肤上提到页面作用域。
- 全模块**没有任何** `append-to-body` / `teleport` 声明，`el-dialog` / `el-drawer` 保持默认不传送 body。
  因此弹窗与抽屉 DOM 仍在页面根之内，页面作用域的 `:deep()` 规则可达。
- 唯一的既有硬边皮肤实现在 `DevicePoolView.style.css:106-142`（作用域 `.device-workbench`）；
  几何 = 2px 墨边 / 2px 圆角 / `2px 2px 0 0 var(--ink)`，hover 位移 `(-1px,-1px)` + `3px 3px 0 0`，
  disabled `opacity .5` + `box-shadow: none`。
- 依赖的既有令牌：`--ink`（`--color-indigo-13`）、`--app-bg-card`（`--color-white`）、
  `--el-color-primary`（`--color-yellow-63`）、`--color-white`、`--app-duration-fast`、`--app-ease`。**不新增任何令牌。**
- 全页可点控件清点：9 个按键（6 原生 + 3 `el-button`）+ 非按键可点元素（el-tree 节点、表格行、输入控件）
  + 2 处共享件。非按键可点元素不在本次范围。

## Goals / Non-Goals

**Goals:**

- `/inspector` 的 6 个原生按键与 2 个弹窗按键共用已登记的硬边几何，且文字对比度全部达标。
- `.action-btn` 的几何声明**只剩一处**（消除跨文件重复）。
- 用页面作用域就地覆写实现，共享件与全局主题零差异。

**Non-Goals:**

- 不把 `DoodleBtn` 的 2.5px/3px 几何拉齐到唯一几何（仓库内既有偏差，独立变更处理）。
- 不动非按键可点元素（tree 节点、表格行、el-select / el-radio-group）。
- 不改布局、间距、栅格、滚动，不改 store / api / 路由。

## Decisions

### D1 · 用页面作用域覆写，而不是换成共享组件

在 `.inspector-workbench` 上写一份皮肤（`:deep()` 覆盖 `el-button` + 直接覆盖 `.action-btn`）。

- **备选 B（改用 `<DoodleBtn>`）被否**：其几何为 2.5px 边 / `3px 3px` 阴影 / `min-height: 32px`，
  与 `frontend-doodle-button` 的「唯一几何 = 侧栏退出按钮 2px/2px」冲突，等于把已存在的第二套硬边几何再扩散一次；
  且它属**模板改写**（6 处标签替换）而非样式改动；并且弹窗内的 `el-button` 依然覆盖不到。
- **备选 C（只给 `.action-btn` 补 box-shadow）被否**：弹窗 3 个按键仍走 EP 默认，页内仍是两套语言。

### D2 · 皮肤集中到页面作用域一处，组件内不再声明几何

`.action-btn` 的皮肤（border / border-radius / box-shadow / hover / disabled）全部写在 `index.vue` 的
`<style scoped>` 里，用 `:deep(.action-btn)` 与 `:deep(.action-btn--primary)` 命中；
`CaptureForm.vue` 删除其 `.action-btn*` 全部声明。这样 D2 直接满足 Goals 的第 2 条，
并消除「组件 scoped 规则 vs 页面 `:deep()` 规则」的特异性竞争。

依据：`CaptureForm.vue` 仅被 `index.vue` 引用（已核实），上提安全；
`:deep()` 编译为 `.inspector-workbench[data-v-x] .action-btn`，对子组件内部元素同样生效。

### D3 · `text` 型按键用选择器排除，而不是事后复位

皮肤选择器写成 `:deep(.el-button:not(.is-text):not(.is-link))`，而不是先套皮肤再把 `.is-text` 复位。
理由：快照抽屉的删除键是 `text` + `type="danger"` 的图标键，套上边框与硬阴影会在列表行内形成过重色块；
正向排除比反向复位更不容易漏（新增的 `is-link` 一并排除）。

### D4 · 深色底按键走「浅色文字」而不是改底色

`获取` 按键沿用既有墨黑底 `var(--ink)`，文字改用 `--color-white`；
弹窗 `保存` 沿用 `--el-color-primary` 柠黄，文字用 `var(--ink)`。
理由：皮肤要求文字色为 `var(--ink)`，但墨黑底上墨字不可读，spec 已为「沿用深色底色」预留浅色令牌例外；
把底色改成柠黄/绿等于重新分配语义，违反「其余按键沿用各自既有语义底色」。

### D5 · disabled 同时覆盖原生与 Element Plus 两种形态

原生 `button:disabled` 与 EP 的 `.el-button.is-disabled` 是两套机制，两条规则都写，
且都以「`opacity: .5` + `box-shadow: none`」收口，避免出现「半透明但仍带位移阴影」的混合态。

## 模块防火墙自检

- 本变更**只改前端样式与模板**，不触及 `apps/`（Python）。因此不涉及跨 App import、跨 App ORM 写、
  写库收敛到 `api.py` 等后端红线；`git status` 对 `apps/` 与 `tests/` 应为零差异。
- 前端侧**不新增** HTTP 调用、端点、DTO 或路由，四通道与「前端唯一 HTTP 出口」约束不受影响。
- 不修改共享件，不引入新的跨模块前端依赖（`SavedPagePicker.vue` 对 `element-locator/api` 的既有依赖保持不变）。
- 未引入任何新的跨模块依赖，故无需说明「为何无法走 `api.py`」。

## Risks / Trade-offs

- [弹窗/抽屉按键皮肤依赖 `.inspector-workbench` 祖先，一旦有人加 `append-to-body` 即失效]
  → 该模块当前无任何传送声明；在任务中加入实测断言，并在 `device-inspector/AGENTS.md` 无关，改为在 spec 的
  Scenario 里以「同一页面作用域覆写」固定该前提，后续若需传送必须同时调整皮肤承载方式。
- [页面 `:deep()` 与组件 scoped 规则特异性竞争]
  → D2 把几何集中到一处并删除组件内声明，从结构上消除竞争，而不是靠 `!important` 堆叠。
- [disabled 在原生与 EP 两条路径表现不同]
  → D5 两条都写；任务中对「未选设备时的获取」「无快照时的保存到元素定位」分别测量。
- [把 `text` 型删除键误纳入，导致列表行出现重盒子]
  → D3 选择器正向排除，并由 spec 的 `Text-type icon key is excluded from the skin` Scenario 固定。
- [柠黄底 + `--ink` 墨字、墨黑底 + `--color-white` 的对比度是否达标不能只靠"看起来"] 
  → 任务中以计算样式取实际色值并计算对比度，必须 ≥ 4.5:1（`frontend-l0-design-tokens` 已登记该门槛）。
- [几何测量受 Chromium 对 `border-width` 取整影响]
  → 断言按比较进行（与设备管理页同一几何对比），而非硬编码小数期望值。
