## Context

两个工作台的分栏由模块 `ProjectWorkspace.vue` 的 grid 实现：`grid-template-columns: var(--<mod>-tree-pane-w) minmax(0, 1fr)`，宽度令牌转发 T0 的 `--layout-pane-left`（280px）。侧栏已有成熟的拖动先例：`shared/composables/useSidebarResize.ts`（mousedown 起拖 + window 上的 mousemove/mouseup + `localStorage` 记忆 + clamp），但它把宽度写到 `document.documentElement` 的 `--side-w` 上、且与折叠耦合，不适用于模块内的分栏。

## Goals / Non-Goals

**Goals:**

- 左栏宽度可用鼠标拖动改变，并且记住
- 拖动不越界、不把右栏挤没
- 键盘可达（可聚焦 + 方向键 + 复位），带正确的 ARIA
- 一件共享件服务于两个工作台，行为逐项一致

**Non-Goals:**

- 不做折叠左栏（另议）
- 不改右栏预览内部
- 不改侧栏拖动（`useSidebarResize` 保持不动）
- 不引入拖拽库或全局状态管理

## Decisions

**D1 共享组件 `SplitHandle.vue` 承担交互，宽度由调用方持有**
组件只负责「拖动 / 键盘 → 新宽度」并 `v-model` 回传，外加 `commit` 事件（松手 / 键盘操作后）供调用方持久化。理由：宽度的消费方是调用方的 grid 栅格（要把值写进模块令牌），持久化 key 属模块语义；组件保持无状态、无 key。

**D2 手柄作为栅格第三列，取代窗格分隔线**
`grid-template-columns: var(--<mod>-tree-pane-w) auto minmax(0, 1fr)`，手柄宽度 8px（含 2px 可见分隔线 + 6px 命中区），原左栏 `border-right` 移除，避免出现两条线。拖动时用 `handle.parentElement` 的 `getBoundingClientRect().left` 把指针 x 换算成左栏宽度，无需额外测量。

**D3 上限由容器宽度动态决定**
`maxAllowed = min(560, containerWidth - 360)`，下限 220。理由：不同视口下「合理的最大左栏」不同；写死上限在窄视口会把右栏压没。`360` 是右栏最小可用宽度（用例预览五列的最小可读宽度的保守下界）。

**D4 初值读 CSS 令牌，覆盖值读 localStorage**
调用方挂载时先取 `getComputedStyle(split).getPropertyValue('--<mod>-tree-pane-w')`（解析为 280px，单一真相源在 tokens.css），再用 `localStorage` 的已存值覆盖。理由：避免在 TS 里重复 280 这个字面量。

**D5 记忆 key 按模块隔离**
`app-split-locator-tree-w` / `app-split-case-tree-w`：两个工作台是两个页面，各自的宽度预期独立。

## 模块防火墙自检

- 跨 App import / 写库 / ORM：无（纯前端共享件）
- 前端 HTTP 出口：不变
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [拖动时右栏表格反复重算宽度] → 表格用 `min-width` + 横向滚动，拖动过程只改容器宽度，无数据请求
- [localStorage 存了越界值（换了小屏再看）] → 应用宽度前一律经 `clamp`，越界值在下一次渲染被夹回
- [键盘用户不知道手柄可聚焦] → 手柄聚焦时绘制可见焦点环（`:focus-visible`）
