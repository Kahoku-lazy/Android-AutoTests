## Why

设备控制三角色（规划 / 执行 / 验收）的系统提示词目前写死在引擎 `config.py`，工具箱无法查看或修改，改提示词必须发版。需要把提示词收口到平台唯一智能体的数据表，由 Django 装配时注入引擎，并在工具箱提供可编辑、Markdown 渲染的管理面。

## What Changes

- 工具箱左侧「工具来源」新增第三项「设备提示词」（无总闸开关）：选中后右侧展示规划 / 执行 / 验收三份系统提示词。
- 三份提示词以 Markdown 源码存库；页面默认渲染 Markdown，管理员可编辑并保存。
- `ai_agents` 新增三角色提示词字段；数据迁移把现行引擎常量灌入已有平台智能体。
- **BREAKING**：`TaskRequest` 增加三角色 `system_prompts`；引擎 `PLANNER_PROMPT` / `VISION_PROMPT` / `VERIFIER_PROMPT` 留空且不再作为运行时回退。Django 装配时从库读取并注入；任一角色提示词为空则装配 fail-fast。
- 读写权限与现有工具箱一致：登录可读，仅超级管理员可写。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-需求总纲.md`（AI 助手 / 工具箱；无独立「提示词管理」子 PRD，本变更为工具箱装配能力增量）
- ARCH：`dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md`（Django 装配、引擎可替换插槽）
- API：`dev_docs/DEV_TEST/接口文档/API-AI助手.md`（将增补设备提示词读写端点）
- 主 spec：`openspec/specs/ai-engine-protocol/spec.md`（`TaskRequest` 契约）

## Capabilities

### New Capabilities

- `ai-device-prompts`: 工具箱管理设备控制三角色系统提示词（库表字段、读写 API、Markdown 渲染与管理员保存）

### Modified Capabilities

- `ai-engine-protocol`: `TaskRequest` 必须携带三角色系统提示词；引擎不得使用内置提示词回退；空提示词装配失败

## Impact

- 后端：`apps/ai_assistant/models.py`、迁移、`api.py`、`views_drf.py` / `urls.py`、`engine_adapter.py`、`serializers.py`；`tests/graybox` 装配与 platform-config 相关单测
- 引擎：`engines/ai/base.py`（`TaskRequest`）、`engines/ai/agentscope/config.py`（常量留空）、`model.py` / `engine.py`（使用注入提示词）；`model_test` 管理命令
- 前端：`ToolboxPanel`、装配 composable/helper、`api/toolbox.ts`；复用 `renderSkillMarkdown`
- 文档：`API-AI助手.md` 增补端点
