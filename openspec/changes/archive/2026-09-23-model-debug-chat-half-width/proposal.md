## Why

对话栏加宽到正文 2/3 后，需求方观感「太宽了」：右侧对话区把配置区挤到只剩 1/3，左栏的工具分组与提示词读起来局促，而对话内容本身在 2/3 宽下也远超所需。按要求**宽度缩小一倍**（2/3 → 1/3），高度维持上一版结论（1.3 屏）不变。

## What Changes

- 模型调试页分栏由「配置区 1fr : 对话栏 2fr」改为**「配置区 2fr : 对话栏 1fr」**：对话栏宽度为正文的 1/3（即上一版 2/3 的一半），配置区回到 2/3。
- 对话栏高度契约**不变**：消息区仍固定 1.3 屏高（`132vh`），内部独立滚动。
- 窄屏单列堆叠断点（1200px）、对话栏内部结构、工具分组折叠、接口与交互一律不变。
- **BREAKING**：无（纯版式调整）

## 关联文档

- 需求编号：`PRD-08-AI助手`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-model-debug`: 对话栏横向占比契约由「正文 2/3」改为「正文 1/3」（配置区 2/3）

## Impact

- `frontend/src/modules/ai-assistant/ModelDebugPage.style.css`（`.md-split` 分栏比例 1 行 + 注释）
- `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`（分栏比例断言改为 2fr : 1fr）
- 后端 / 端点 / 迁移：零改动
- 可见变化：对话栏宽度约为上一版的一半（正文 1/3），左侧配置区回到 2/3；对话区高度与折叠行为不变
