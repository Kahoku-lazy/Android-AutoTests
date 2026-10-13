# 平台 Agent 功能设计

> **AGENTS 层级**：一级约束 —— 根 `AGENTS.md` 优先于本文件。

> 涉及平台 AI助手 AgentScope 框架代码变动时 **必须** 阅读此文档

## 技术栈

1. Agent框架当前版本： AgentScope 2.0.9


## 代码规则

1. **函数方法**：函数方法注释只写功能 / 入参 / 返回值，禁写设计旁白与"给谁看"

## 测试

> 代码修改后先检查是否需要执行迁移指令： `python manage.py migrate ai_assistant`,

