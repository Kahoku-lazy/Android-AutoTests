# ae_harness · 原语层总览
> 归属模块：`engines/ae_harness` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/__init__.py`、`engines/ae_harness/agents/`、`engines/ae_harness/tools/`、`engines/ae_harness/event/`、`engines/ae_harness/middleware/`、`engines/ae_harness/workflow/`、`engines/ae_harness/knowledge/`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 此文档的生效范围是 `engines/ae_harness` 目录
> `ae_harness` 为此项目提供 Agent智能体创建、多智能体编排、智能体工具配置、上下文管理等功能。
> 此模块不参与具体的业务实现，只提供与智能体，模块相关的工具与方法。

## 技术栈

1. 核心模块是 `AgentScope`，当前使用的版本是 **2.0.12**。


## 红线（AI 禁止事项）

1. 禁止 import ae_harness外的功能模块; 可使用 `lint-imports` 指令检查是否违反这个红线。

