## Context

页面为工作台壳层策略 ②：`.doc-page--fixed` 视口固定、`.doc-body` 承担滚动。`.doc-body` 内自上而下是面包屑与 `.md-page`（栅格 `.md-split`），页头 `WorkbenchHeader` 在页面根内、高度为 `--app-topbar-h`（96px）。对话栏 `aside.md-panel.md-chat` 是栅格第二列，`align-items: start` 使其高度由内容决定：标题 + 范围说明 + 消息区（`md-chat-body`，当前固定 `66vh`）+ 输入区（`.md-chat-input`）。页面内边距 16px、栅格/正文间距 16px、面包屑约 32px。

## Goals / Non-Goals

**Goals:**

- 对话栏整块落在首屏内，输入区不必滚动即可见。
- 视口变矮时自动收缩，不改动宽度、断点与折叠行为。

**Non-Goals:**

- 不改分栏比例、工具分组折叠、消息区内部结构、接口与交互。
- 不做「页头 / 输入框吸顶固定」这类结构调整（可作后续独立变更）。

## Decisions

**D1：给面板加上限，让消息区吸收差额，而不是继续调 `vh` 数值。** `.md-chat { max-height: calc(100vh - var(--app-topbar-h, 96px) - 72px) }`（72px = 文档区内边距 16 + 面包屑约 32 + 正文间距 16 + 余量），并让 `.md-chat-body { flex: 0 1 auto; min-height: 0; height: 66vh }`。理由：`vh` 数值是死的，面板内固定部分（标题 / 说明 / 输入区）在换行、字体差异下会变高；把约束放在面板上、让可滚动的那一块吸收差额，才能保证「永远不出首屏」。备选：把 `66vh` 直接改小（如 52vh）——治标，窄屏或说明换行时仍可能超出。

**D2：面板内除消息区外的子项设为 `flex: none`。** 默认 `flex-shrink: 1` 会在面板被压缩时把输入区一起压扁（textarea 变矮、按钮错位）。显式声明标题 / 范围说明 / 输入区不可收缩，收缩只发生在消息区。备选：给输入区设 `min-height` 硬值——仍需逐项防压缩，不如一次性声明。

**D3：不给面板加 `overflow`。** 消息区收缩到位后面板不会溢出，额外 `overflow: auto` 会造出第二层滚动条与滚动链，反而更难用；极端矮视口（高 < 约 400px）下允许由 `.doc-body` 兜底滚动。

## 模块防火墙自检

- 跨 App import：无（只动一个前端模块内的样式与测试文件）。
- 引擎边界 / 通信通道：不涉及；不新增或修改任何 HTTP、WebSocket、SSE 调用。
- 前端不直连数据库、不新增写操作。

## Risks / Trade-offs

- [72px 是按当前面包屑与内边距估的常量，改版式后可能失准] → 常量写在注释里并说明构成；失准时调整一个数值即可（弹性收缩保证不会因为内边距变化而压扁输入区）。
- [页头动作区换行时 `WorkbenchHeader` 高于 `--app-topbar-h`（其 `min-height`）] → 面板会随之略超出；72px 中的余量与 `flex: none` 组合可吸收小幅增长，超出时由 `.doc-body` 滚动兜底。
- [视口极矮（< 约 400px）时消息区被压到很小] → 属可接受的降级：优先保证输入区完整可用。

## Migration Plan

纯前端样式调整，无数据迁移。回滚：还原 `ModelDebugPage.style.css` 的对话栏与消息区声明。
