## Why

对话栏消息区固定 2/3 屏高（`66vh`）后，加上标题、范围说明与输入区，整块面板仍略高于一屏——输入框与「发送」落在折线以下。需求方要求：**对话栏整块必须在首屏之内**（不用滚动就能看全）。

## What Changes

- 对话栏（`aside.md-chat`）增加整体上限：高度 MUST ≤ 视口高度 − 页头高度 − 面包屑与页面内边距，即整块面板不超出一屏。
- 消息区保留 `66vh` 作为期望高度，但改为**可伸缩**（`min-height: 0` + 允许收缩）：面板触到上限时只有消息区被压缩，标题、范围说明、输入区 MUST 保持自身高度不被压扁。
- 宽度、断点、工具分组折叠、消息区内部滚动规则与接口一律不变。
- **BREAKING**：无

## 关联文档

- 需求编号：`PRD-08-AI助手`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-model-debug`: 消息区高度契约由「固定 2/3 屏」改为「以 2/3 屏为期望高度、整体受首屏可容纳高度约束」

## Impact

- `frontend/src/modules/ai-assistant/ModelDebugPage.style.css`（新增对话栏上限 + 可伸缩规则）
- `frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`（新增首屏约束断言）
- 后端 / 端点 / 迁移：零改动
- 可见变化：对话栏底边（输入框与发送按钮）回到首屏内；窗口变矮时对话栏随之收缩，消息更多时只在消息区内部滚动
