## MODIFIED Requirements

### Requirement: AI assistant workbench titles are Chinese-only
AI 助手入口页（智能体看板、工具箱）的页头主标题 SHALL 仅为中文产品名，MUST NOT 在同一行并列英文对照（例如 `Platform Assistant`、`AI Toolbox`）。产品名中作为汉语习惯保留的「AI」（如「AI工具箱」）MAY 保留。副标题与其它子页页头不在本需求范围内。评测中心入口已由 `evaluator-retirement` 下线、知识库入口已由 `knowledge-base-retirement` 下线，本需求不再覆盖这两条路由。

#### Scenario: Agents view header title
- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 页头 `.brand-title` 文本为 `平台小助手`，且不包含 `Platform Assistant`

#### Scenario: Toolbox view header title
- **WHEN** 用户打开 `/ai-assistant/toolbox`
- **THEN** 页头 `.brand-title` 文本为 `AI工具箱`，且不包含 `AI Toolbox`

#### Scenario: Knowledge view header title

<!-- 场景名沿自变更前：知识库入口已整体下线（见 knowledge-base-retirement），本场景改为守住「该路由与页头都不再存在」这一不变量 -->

- **WHEN** 访问 `/ai-assistant/knowledge`
- **THEN** 该路由不存在（不渲染知识库页头），侧栏也没有对应子项
