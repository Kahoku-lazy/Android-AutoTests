## Why

执行角色自己拼智能体，和角色基座的创建、回复、技能登记各写一套。技能名单已经在工具配置里，角色构造时却没有按这份名单登记。现在把执行角色收成基座的子类，并在启动前登记技能。

## What Changes

- 执行角色改为继承角色基座，用角色配置提供名称、系统提示词、工具包和视觉输入。
- 构造执行角色时，按工具配置中的技能目录名单登记技能；同一目录已在工具包中则不重复挂载。
- 回复、流式输出和用量统计沿用基座，执行角色不再自建一套。
- 本地试跑入口不进入本变更的规格与归档正文，连接用的密钥不写入任何 OpenSpec 产物。

## 关联文档

引擎内角色装配，不改平台需求文档。AI 助手模块既有编号为 PRD-08，本次不新增需求文档。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-role-skills`: 执行角色在创建智能体之前，必须把工具配置中的技能目录名单登记到自己的工具包；同一目录已挂载时不重复登记。

## Impact

- `engines/agents/role/executor.py`：执行角色改为继承基座并登记技能。
- `engines/agents/role/base.py`、`engines/agents/tools_config.py`、`engines/agents/prompt_config.py`：只消费既有基座、技能名单和提示词，不改它们的契约。
- `apps/` 与前端零改动。
