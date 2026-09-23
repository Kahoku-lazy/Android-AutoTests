## Why

上一轮把「太宽了，缩小一倍」误读成横向收窄，实际需求方说的是**纵向**：对话区太高了。本次纠正两件事：① 高度由 1.3 屏缩到一半（`132vh` → `66vh`）；② 宽度退回上一轮误改前的比例（对话栏回到正文 2/3）。

## What Changes

- 对话区高度：消息区固定高度由 `132vh`（约 1.3 屏）改为 **`66vh`（约 2/3 屏，即上一版的一半）**；仍为固定高度（无消息时同样占位）且超出在该区内独立滚动。
- 分栏比例退回：`.md-split` 由 `minmax(0, 2fr) minmax(0, 1fr)`（对话栏 1/3）恢复为 `minmax(0, 1fr) minmax(0, 2fr)`（对话栏 2/3）——上一轮的横向收窄是误读需求所致。
- 窄屏单列断点（1200px）、工具分组折叠、对话栏内部结构、接口与交互一律不变。
- **BREAKING**：无

## 关联文档

- 需求编号：`PRD-08-AI助手`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-model-debug`: 消息区高度契约由「固定 1.3 屏」改为「固定 2/3 屏」；对话栏横向占比契约由「正文 1/3」恢复为「正文 2/3」

## Impact

- `frontend/src/modules/ai-assistant/ModelDebugPage.style.css`（`.md-split` 分栏比例 + `.md-chat-body` 高度各 1 行，含注释）
- `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`（两条版式断言改口径）
- 后端 / 端点 / 迁移：零改动
- 可见变化：对话区高度回到约 2/3 屏（上一版的一半），宽度恢复为正文 2/3
