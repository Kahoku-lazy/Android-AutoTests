# ai-assistant/workbench-header-copy Specification

## Purpose

约定 AI 助手模块四个工作台子页的 L2 页头主标题只展示中文产品名，去掉并列的英文对照词，使标题更短、与其它模块页头口径一致。

## Requirements

### Requirement: AI assistant workbench titles are Chinese-only
AI 助手入口页（智能体看板、工具箱、知识库）的页头主标题 SHALL 仅为中文产品名，MUST NOT 在同一行并列英文对照（例如 `Platform Assistant`、`AI Toolbox`、`Knowledge Base`）。产品名中作为汉语习惯保留的「AI」（如「AI工具箱」）MAY 保留。副标题与其它子页页头不在本需求范围内。评测中心入口已由 `evaluator-retirement` 下线，本需求不再覆盖该路由。

#### Scenario: Agents view header title
- **WHEN** 用户打开 `/ai-assistant/agents`
- **THEN** 页头 `.brand-title` 文本为 `平台小助手`，且不包含 `Platform Assistant`

#### Scenario: Toolbox view header title
- **WHEN** 用户打开 `/ai-assistant/toolbox`
- **THEN** 页头 `.brand-title` 文本为 `AI工具箱`，且不包含 `AI Toolbox`

#### Scenario: Knowledge view header title
- **WHEN** 用户打开 `/ai-assistant/knowledge`
- **THEN** 页头 `.brand-title` 文本为 `知识库`，且不包含 `Knowledge Base`
