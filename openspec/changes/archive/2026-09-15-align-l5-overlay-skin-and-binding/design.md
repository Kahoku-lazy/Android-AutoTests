## Context

19 处 EP 覆盖层的可见性绑定实测分类（`rg -n "<el-dialog|<el-drawer"` 逐处读标签）：

| 类 | 数量 | 写法 | 状态归属 |
|----|:--:|------|------|
| A | 8 | `v-model="本地 ref"` | 本组件持有 |
| B | 3 | `:model-value="store.x"` + `@update:model-value="(v) => (store.x = v)"` | store 持有、纯写回 |
| C | 3 | `:model-value="派生表达式"` + handler 做清理 | 派生 / 需联动 |
| D | 5 | `:model-value="visible"` + emit 领域事件 | 父组件持有（薄封装） |

B 类三处：`SavedPagePicker.vue`、`SaveToElementsDialog.vue`（device-inspector 组件）与 `SnapshotListDrawer.vue`（el-drawer）。C 类三处：`workflow/index.vue`（`creatingKind === 'folder'`）、`PageElementsPanel.vue`、`StructureAnalysisPanel.vue`（关闭需清 `enlargeRow`）。D 类五处：`LoginErrorOverlay` / `KnowledgeImportDialog` / `KnowledgePreviewDrawer` / `DisconnectDialog` / `NetworkConnectDialog`。

皮肤现状：`style.css:65-69` 有 `.el-dialog`、`:136-141` 有 `.el-message`，**`.el-drawer` 命中 0**。

## Goals / Non-Goals

**Goals:**

- 补 `.el-drawer` 全局皮肤，使抽屉与对话框同源
- 把 B 类 3 处纯写回收敛为 `v-model`，消除多余展开
- 把「按状态归属确定绑定写法」写成可验收需求，终结「同一情形多种写法」

**Non-Goals:**

- 不把 C / D 类强行改成 `v-model`（会破坏语义：派生可见性无法双向绑定，薄封装不该自持状态）
- 不改 5 处薄封装组件的对外 API（`visible` prop + 领域事件）
- 不给 `.el-drawer` 加模块私有皮肤，也不改抽屉的 `size` / 内容布局
- 不统一各弹层的 `close-on-click-modal` / `destroy-on-close`（属另一口径，本变更只登记）

## Decisions

**D1 · 绑定写法按状态归属二分，而非全局统一成一种**

「统一成 `v-model`」对 C 类不可行：`creatingKind === 'folder'` 是派生表达式，`v-model` 需要可写目标；对 D 类不可行：薄封装自持或写回可见性会与其 `cancel` / `confirm` 语义打架（父组件才是状态所有者）。因此约定写成「按归属选写法」，并把它表述为可验收需求 + 三个场景。备选「全部改成 `:model-value` + `@update:model-value`」会把 8 处本地 `ref` 的 `v-model` 展开成样板代码，降低可读性，不采纳。

**D2 · 只收敛 B 类 3 处，且逐处确认「纯写回」**

这三处的 handler 只做 `(v) => (store.x = v)`，与 `v-model` 编译产物等价，属零行为变化。C 类的 handler 还有 `cancelCreate()` / `closeEnlarge()`，不属纯写回，保持原样。

**D3 · `.el-drawer` 皮肤与 `.el-dialog` 逐条对齐**

沿用 `.el-dialog` 的 `border-radius: 6px 10px 6px 10px` + `border: 2.5px solid var(--ink)` + `overflow: hidden`，不引入新颜色 / 新令牌（AGENTS L0：组件类样式只作用于类名、不新增模块私有尺寸）。

**D4 · 抽屉外观变化按「有意统一」交付并留浏览器核验项**

两个抽屉会从 EP 默认外观变为涂鸦外观，属可见变化；本环境无浏览器，交付时登记为待补核验，不以静态证据充当观感结论。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无

## Risks / Trade-offs

- [给抽屉加 `border` 会占 2.5px，可能挤压内容宽度] → 项目 L0 已有 `* { box-sizing: border-box }`，边框计入元素尺寸，不改变外部布局；仍以浏览器核验为准
- [`.el-drawer` 的 `overflow: hidden` 可能影响抽屉内部滚动] → 抽屉的滚动容器是 `.el-drawer__body`（自带 `overflow: auto`），根节点裁切只用于圆角收边；若核验发现异常，回退为仅 `border-radius` + `border`
- [`v-model="store.x"` 直接写 store 状态属 Pinia 允许但需自觉的用法] → 这三处本就是「写回同一字段」，收敛后语义不变；store 未定义 setter，不存在绕开 action 的副作用
- [约定写进 spec 后，C / D 类可能被下一个接手者误判为「不合规」] → 在 spec 的两个场景里显式写明「MUST NOT 被改成 `v-model`」，并在 L5 速查③给出三类归属的判据

## Migration Plan

- 无数据迁移；回滚为 revert 本变更提交
- 验证顺序：`vue-tsc --noEmit`（改动文件零错误）→ `vue-frontend-check` 静态扫描 → 两个抽屉 + 三个弹层的浏览器目视（本环境待补）
