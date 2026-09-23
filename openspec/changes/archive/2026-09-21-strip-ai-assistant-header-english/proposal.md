## Why

AI 助手模块四个侧栏子页的 `WorkbenchHeader` 主标题采用「中文 + 英文」并列（如「平台小助手 Platform Assistant」），与设备检查器已改为纯中文标题的口径不一致，页头过长且在窄宽下更容易被省略号截断。现在只改可见主标题文案，不改路由、副标题与业务逻辑。

## What Changes

- `/ai-assistant/agents|toolbox|knowledge|evaluator` 共用页头的 `VIEW_META.title` 去掉英文对照词，只保留中文产品名：
  - `平台小助手 Platform Assistant` → `平台小助手`
  - `AI工具箱 AI Toolbox` → `AI工具箱`
  - `知识库 Knowledge Base` → `知识库`
  - `评测中心 Evaluation Center` → `评测中心`
- 「AI工具箱」中的「AI」视为中文产品名的一部分，MUST 保留；去掉的是其后独立英文 `AI Toolbox` 等对照。
- 副标题、子页（任务详情 / Skill / 工具调试 / 智能体编辑）页头、代码注释与 API 注释 MUST NOT 纳入本次范围。

## 关联文档

- 无独立 PRD 条目：纯 L2 页头展示文案收敛，与设备检查器页头去掉 `Device Inspector` 同一口径；不改 AI 助手业务能力。

## Capabilities

### New Capabilities

- `ai-assistant/workbench-header-copy`：AI 助手四子页 WorkbenchHeader 主标题仅展示中文产品名，不得并列英文对照。

### Modified Capabilities

（无）现有 `frontend-l2-page-region` 约束页头结构与截断，不约束模块标题语言。

## Impact

- 前端：`frontend/src/modules/ai-assistant/index.vue` 中 `VIEW_META` 四条 `title`。
- API / 后端 / 路由 `meta.title`：不改。
- 测试：仓库内无断言这四条英文对照的用例；若后续加视觉/文案断言，应对齐纯中文标题。
