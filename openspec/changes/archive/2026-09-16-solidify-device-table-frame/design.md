## Context

动机见 `proposal.md - Why`。方案所需约束（读码核实）：

- `.sketch-sheet` 的描边是**简写** `border: var(--comp-sheet-border)`（`workbench-theme.css:165`），令牌值 `2.5px dashed var(--color-indigo-13)`（`tokens.css:281`）。
- 该令牌被**所有**带 `accent` 的 `AppTable` 消费（`AppTable.vue:113` 按 `accent` 加 `sketch-sheet` 类）。
- 页面作用域选择器 `.device-workbench :deep(X)` 编译为 `.device-workbench[data-v-p] X`（特异性 `(0,3,0)`），高于共享规则 `.wb-shell .sketch-sheet`（`(0,2,0)`）。
- 状态色条由 `tr.row-online` / `tr.row-busy` 驱动，类名由 `DevicePoolView.logic.ts:199-203` 的 `deviceRowClassName` 产出；全仓检索显示**没有第二个消费方**。
- Element Plus 自身已在 `.el-table .el-table__cell` 上声明 `position: relative`（实测 minified CSS 命中 1 条），故页面那条 `position: relative` 不是色条的专属锚点。

## Goals / Non-Goals

**Goals:**

- 设备管理页表纸外框呈现为**实线**，且宽度/颜色仍与共享令牌单源。
- 去掉首列纯颜色条这一冗余状态载体，行状态只由状态列承载。
- 删掉由该装饰撑起来的行类名机制，不留孤儿代码。

**Non-Goals:**

- 不改内部网格线（行线/列线仍不绘制），不推翻 `frontend-l4-data-surface`。
- 不改共享令牌 `--comp-sheet-border`、不改其它页面表纸、不改 `AppTable` 与 `workbench-theme.css`。
- 不改表头底线（本来就是 2px 墨色实线）、不改圆角/硬阴影/表体不旋转。
- 不动 `td.el-table__cell` 上的 `position: relative`（EP 自身已声明同属性，删它不属本请求且可能引入层叠差异）。

## Decisions

### D1 只覆写 `border-style`，不重声明令牌

页面作用域加一条：

```css
.device-workbench :deep(.sketch-sheet) { border-style: solid; }
```

- 备选 1：在 `.device-workbench` 上重定义 `--comp-sheet-border: 2.5px solid var(--ink)` —— 可生效且无特异性博弈，但会把宽度与颜色从令牌里**复制**一份到模块，令牌改版即漂移。否决。
- 备选 2：改共享令牌本身 —— 会让 `/reports`、`/elements` 一起变，超出用户选定的范围。否决。
- 备选 3：给 `AppTable` 加 `frame` 之类的新属性 —— 单页单消费者，属过度设计。否决。

只覆写简写中的一个长属性，是"令牌唯一来源"与"单页作用域"同时成立的最小写法。

### D2 用页作用域特异性取胜，不加 `!important`

`.device-workbench[data-v-p] .sketch-sheet`（`(0,3,0)`）严格高于 `.wb-shell .sketch-sheet`（`(0,2,0)`），且 `border-style` 与简写 `border` 按属性逐项比较，页面长属性胜出。无需 `!important`，与本页统一按键皮肤块（那处必须 `!important`，因为对手同为 `(0,3,0)`）理由不同。

### D3 状态色条移除后连带删除行类名机制

`row-online` / `row-busy` 的唯一消费方就是这 3 条 `::before` 规则。删装饰而留类名，会留下"产出但无人消费"的行类名与 `row-class-name` 传参。故同步删除 `deviceRowClassName`（函数 + 接口成员 + 返回值）、`index.vue` 的解构与 `:row-class-name` 传参。这一步的每一行都能追溯到本请求。

### D4 内部网格线不动

用户在澄清中确认只改外框（"第三问作废"）。`style.css:110` 与 `workbench-theme.css:142` 的 1px `transparent` 占位保持原样，`frontend-l4-data-surface`「Tables draw no visible grid lines」不产生 delta。

## 模块防火墙自检

纯前端样式与模块内逻辑改动：

- 跨 App import：无。改动集中在 `frontend/src/modules/device-pool/`，不涉及后端 App。
- 跨 App import service/runner/consumer/state_machine：不适用。
- INSERT/UPDATE/DELETE 收敛到 `api.py`：不适用（无写库）。
- 前端不直连数据库：不适用。
- 无新增依赖、无 API 契约、无路由变更、无新令牌。

## Risks / Trade-offs

- [设备表与 `/reports`、`/elements` 的表纸线型分叉] → 用户明确选择"仅设备管理页"；已在 spec 里把线型登记为按页属性，并用「其它页面表纸仍为虚线」的断言守住。
- [模块 CSS 只改 `border-style` 后，若将来令牌改线型，设备页仍被覆写成实线] → 这正是登记后的预期行为（spec 已写明设备页为实线）；若将来要统一，改的是这一条覆写。
- [删掉状态色条后，长列表里"哪台在线"的先扫视线索变弱] → 状态列本身是文字标签 + 三态配色，且行底色在 hover 时按模块色着色；信息未丢失，与 `unify-card-surfaces` 的同一取舍一致。
- [删除行类名影响 `AppTable` 的行渲染] → `row-class-name` 缺省即 `undefined`，`AppTable` 已按可选处理；用"行仍渲染、斑马纹仍生效、选中态仍生效"的断言覆盖。
