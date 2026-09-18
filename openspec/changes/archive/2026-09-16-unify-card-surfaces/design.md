# 设计：统一卡片语言

## Context

`openspec/specs/frontend-doodle-appcard-panel` 已要求「MUST 通过共享 `AppCard` 呈现可复用数据块……SHALL NOT 再使用实线大圆角 + 彩色顶条作为默认壳」。本变更是对该既有要求的实现修复，因此 `skip_specs: true`。

三个模块各自的自建壳不是"没来得及迁移"，而是有具体成因，需逐个核实后再改。

## Goals / Non-Goals

- Goals：让 report-generator / device-pool / device-inspector 的可复用数据块统一走 `AppCard` 钉板壳。
- Non-Goals：不改 `AppCard`/`SketchCard` 自身的皮肤规格；不决定 `AppCard` 与 `SketchCard` 的选用边界（那是 §3.7 的另一半问题，且 SketchCard 的消费点本次不动）；不动卡片内的业务样式（`.case-header`、`.task-block` 等）。

## Decisions

### D1 report-generator：删除外层自建壳与剥壳规则（已实施）

**事实**（逐条核实，非推断）：

- `CaseBreakdown.vue:138` 页根为 `<div class="doc-page wb-shell case-breakdown-page">` → `.case-group` 位于 `.wb-shell` 作用域内。
- `workbench-theme.css:57-95` 定义 `.wb-shell .ac-card`：`border: 2.5px dashed var(--ink) !important`、`border-radius: 2px !important`、`box-shadow: 4px 4px 0 0 var(--ac-accent) !important`、图钉、`overflow: visible !important`。
- `.case-group`/`.bug-case-group` 自建 `border: 2.5px solid` + `--app-radius-lg` + `overflow: hidden`；随后 `:deep(.el-card){border/box-shadow/border-radius: …!important}` 把内层 AppCard 壳压制为零。

即：**AppCard 的壳本应生效，是被刻意剥掉的**；外层再叠一个实线大圆角壳，形成双壳；`overflow: hidden` 还把 AppCard 的图钉（`top: -7px`）裁掉。

**选择**：同时删除外层壳声明（含 hover）与两条剥壳规则，`AppCard` 成为唯一壳。

**被否方案**：

- 只删剥壳规则、保留外层壳 → 双壳（虚线套实线）依旧违反 spec。
- 把外层壳改写成钉板样式 → 重复实现共享组件已有的皮肤，违反"不要重复造轮子"。

**副作用**：`.case-group:hover` 的 `translateY(-1px)` 一并移除；`.ac-card:hover` 自带 `rotate(0) translate(-1px,-1px)` + 5px 阴影，替代行为等价。BUG 列表的红色身份由 `AppCard color="red"`（→ `--c-runner`，实测 `rgb(255,181,167)`）的 accent 承担。

**与审计报告的差异（如实记录）**：审计称剥壳"全库仅该模块 3 处"，实测当前仓库只有 2 条 `:deep(.el-card)` 规则。3 个 `AppCard` 消费点（第 188 / 242 / 337 行）对应 2 个外层壳类（`.bug-case-group` / `.case-group`），2 条规则即覆盖全部 3 处，故无遗漏。

### D2 device-pool `DeviceCard`：待设计决策（未实施）

`DeviceCard.vue:119-149` 的自建壳承载了 AppCard 没有的两个职责，改前必须定口径：

1. **左侧 4px 色条**由 `--card-accent` 驱动，而该变量同时承载**状态语义**：`.device-card.busy` → `--c-dashboard`、`.device-card.offline` → `--app-border-light`（默认 `--c-device`）。AppCard 的 accent 由 `tone`/同排 cycle 决定，二者语义不同：一个是"模块色轮转"，一个是"设备状态"。
2. **`aspect-ratio: 2.2 / 1`（min-height 132 / max-height 168）**的横长比例由自建壳提供，AppCard 不设比例。

这两点须先定「状态色是否保留为色条/改为图钉色」与「横长比例是否保留」，不猜测处理。

**核实补充（第 15 轮）**：

- **状态色不再是问题**：`DeviceCard` 模板第 56–59 行已经有 `.status-chip`，带 `statusTag()` 的**文字** + 几何图形（`busy` 用 `geo--triangle`，其余 `geo--diamond`）+ 三态独立配色（`.status-chip.online/busy/offline`，第 214–222 行）。即左侧 4px 色条是**冗余的第二套状态载体**，且是"仅靠颜色"的编码。移除它**不丢信息**，反而消除了 color-only 状态表达。
- **横长比例按"只碰必须碰的"处理**：本变更声明的范围是卡片**壳**（补图钉 + 微旋转 + 模块色硬阴影），`aspect-ratio: 2.2/1` 是卡片自身的布局属性，不在范围内，故**保留**。
- **accent/tilt 注入口径（沿用既有模式，不发明）**：`AppCard` 的 accent 与微倾由**父级**注入，仓库既有 14 个消费点全部如此——`PrototypeList.vue:106-107`、`case-manager/ProjectList.vue:106-107`、`element-locator/ProjectList.vue:61-62` 均为 `:tone="sketchToneAt(index)"` + `:tilt="sketchTiltAt(index)"`，helper 在 `shared/helpers/sketchCard.ts`（`sketchToneAt(0)`=`var(--c-dashboard)`、`(1)`=`var(--c-device)`，越界即抛错）。因此改造落在两处：`DeviceCard.vue` 换成 `AppCard` 根、设备卡片网格的 `v-for` 补 `tone`/`tilt`。这也自动满足 `frontend-doodle-appcard-panel`「同排相邻卡 accent MUST 循环、SHALL NOT 锁成单一模块色」——当前 `DeviceCard` 把同排卡全锁在 `--c-device`，本身即违反了该条。

### D3 device-inspector 3 处：核实后判定**不改**（已实施=不改）

审计 §3.7 把这三处列为「device-inspector 自建卡」。逐一读源码后确认：**它们是按样式签名（实线 2–3px + 扁阴影）扫出来的工具容器，不是 spec 所称的「可复用数据块」**。

| 审计指认 | 实际选择器与结构 | 判定 |
| --- | --- | --- |
| `index.vue:207-219` | `.filter-bar`：`display:flex; align-items:center; gap:10px; flex-wrap:wrap; padding:10px 14px`，内容是搜索框与统计文本——**过滤工具栏** | 不是卡片块 |
| `StructureAnalysisPanel.vue:261-268` | `.sap-sections`：`min-height:0; overflow-y:auto; padding:var(--app-space-sm)`，是两列网格右列的**滚动区** | 不是卡片壳；AppCard 也不提供滚动区职责 |
| `SnapshotListDrawer.vue:63-68` | `.snap-item`：380px 抽屉内的**紧凑列表行**，`display:flex; justify-content:space-between` + 行尾删除按钮 + `padding:10px 12px` | 不是卡片壳 |

**结论**：本变更不改这三处。理由：强行套 `AppCard` 会引入图钉、微倾、`4px 4px` 硬阴影与 `--app-space-md` 内边距——一个 380px 抽屉里排 10 行"钉板卡片"、给过滤工具栏和图钉加微倾，是明确的视觉回归；且 `.sap-sections` 的 `overflow-y:auto` 无法由 AppCard 承担。

**对审计报告的修正**：§3.7 device-inspector 行应改为「实线边框的**工具容器**（过滤栏 / 滚动区 / 列表行），非卡片语言分叉」。逐条存疑即改，不把审计结论当既成事实执行。

## Verification

### 改动前反证（Chromium 计算样式，真实 `tokens.css` + `style.css` + `workbench-theme.css` + 本页 `<style>` 源码与复刻 DOM）

```
.case-group : border 2px solid · radius 8px · overflow hidden · shadow rgba(0,0,0,0.06) 3px 4px 0 0
.ac-card    : border 0px none · shadow none · radius 0px        ← 壳被剥成零
.bug-case-group / .bug-card : 同上
图钉        : pinTop -5.04 > 组边框盒顶 -3.34 → 被 overflow:hidden 裁掉
```

### 改动后断言

```
.case-group : border 0px none · overflow visible · shadow none   ← 不再有外层壳
.ac-card    : border 2px dashed rgb(30,30,36)                    ← 2.5px 虚线墨色边（Chromium 计算值取整）
              shadow rgb(255,181,167) 4px 4px 0px 0px            ← 模块色硬阴影
              radius 2px · transform rotate(0.3deg)              ← 近直角 + 微倾
.bug-case-group / .bug-card : 同上
图钉        : 不再被裁剪（overflow visible）
```

- `npm run lint:styles` → 0
- `npx vite build --mode development` → 0（33.50s）

脚本：`temps/card-shell-check.mjs`（把 `:deep(X)` 还原为后代选择器后注入裸 CSS，否则解析器会丢弃整条剥壳规则而无法复现改动前状态）。

### device-pool（`DeviceCard` → `AppCard`）

**核实**：`DeviceCard` 模板第 56–59 行已有 `.status-chip`（`statusTag()` 文字 + `busy` 三角形/其余菱形 + 三态独立配色），左侧 4px 色条是冗余且**仅靠颜色**的第二状态载体；`DevicePoolView.style.css:152-162` 另有一套本地 `.card-group-grid > :nth-child(3n+k) { transform: rotate(...) }` 微倾 + `:hover{scale(1.03)}` + 独立 reduced-motion，与 `AppCard` 的 `--ac-tilt`/hover **抢同一个 `transform`**（两套都写 `transform`，必然互相压过）。

**实施**：`DeviceCard` 根换为 `AppCard`（`tone`/`tilt` 由 `index.vue` 的 `v-for` 注入 `sketchToneAt(i)`/`sketchTiltAt(i)`，沿用 `PrototypeList.vue:106-107` 等既有模式）；删除 `::before` 左侧色条与 `.busy`/`.offline` 的 `--card-accent` 覆写；删除网格的本地微倾 3 条 + hover + 其 `@media` reduced-motion 块。reduced-motion 仍由 `DeviceCard` 自身与 `.ac-card` 的降级块覆盖。

**改动前后对比**（Chromium，同一网格父级，含 Element Plus 自带样式表；合成 OLD 变体逐条照抄被移除的声明与旧 DOM）：

| | 布局尺寸 | 边框 | 圆角 | 阴影 | 左侧色条 |
| --- | --- | --- | --- | --- | --- |
| 改前 | 420 × 168 | `2px solid` | `6px` | `rgba(0,0,0,0.04) 2px 2px 0 0` | `::before` 宽 4px |
| 改后 | **420 × 168**（不变） | `2px dashed` 墨色 | `2px` | `rgb(247,201,72) 4px 4px 0 0` | 无（`::before` content = none） |

- `overflow` 由 `hidden` 变 `visible` → 图钉不再被裁剪；`aspect-ratio: 2.2/1` + `max-height: 168px` 仍生效。
- `el-card__body` 内边距必须 `padding: 0 !important`：共享规则 `.wb-shell .ac-card .el-card__body`（0,3,0）特异性高于本选择器（0,2,0），实测不加 `!important` 时为 16px，会挤压固定比例的内容区。
- 状态仍可辨识：`.status-chip.busy` 底色 `rgb(255,248,224)` vs `.offline` `rgb(255,254,245)`。
- 源码级核对：`::before`、`--card-accent`、`.device-card.busy`、实线边 / md 圆角 / sm 阴影声明均已不存在；网格 `> :nth-child` 微倾规则已不存在。

**一次测量口径错误（如实记录）**：第一次用 `getBoundingClientRect()` 量到改后为 `424.3 × 178.9`，据此误判为「网格拉伸回归」并顺手加了 `align-self: start; min-width: 0`。核对数字后发现 `424.3×178.9` 恰是 `420×168` 旋转 −1.5° 的**外接矩形**（`420·cos1.5+168·sin1.5=424.26`、`420·sin1.5+168·cos1.5=178.93`）——是 transform 污染了测量，并非布局变化。已撤回那两条 CSS，改用 `offsetWidth/offsetHeight` 复测，前后均为 420×168。

脚本：`temps/devicecard-shell-check.mjs`（内含合成 OLD 变体，可直接复跑）。
