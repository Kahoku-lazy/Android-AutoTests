# 00-智能体

> 本栏目整理项目智能体体系结构。**`.claude/` 与 `.agents/` 目录只读引用，不在此复制或修改源文件。**

## 本栏目文档

| 文件 | 说明 |
|------|------|
| [`智能体体系设计.html`](./智能体体系设计.html) | **主设计图册** · 双体系 · 六角色 · Auto-Dev 7 阶段 · 三档强度 · Stage-Gate · SOP |
| [`结构总览.md`](./结构总览.md) | 目录树、路由关系、与 Stage-Gate 的对应 |

## 只读入口（仓库根）

| 文件 | 说明 |
|------|------|
| [`../../CLAUDE.md`](../../CLAUDE.md) | Agent 路由、身份定位、铁律、Rules/Skills 索引 |
| [`../../AGENTS.md`](../../AGENTS.md) | 项目概述、架构、模块边界、API/DB 约定 |

## 只读目录

| 路径 | 内容 |
|------|------|
| [`../../.claude/agents/`](../../.claude/agents/) | 6 个专用 Agent 定义 |
| [`../../.claude/skills/`](../../.claude/skills/) | 10 个项目 Skill |
| [`../../.claude/rules/`](../../.claude/rules/) | 15 条领域规则 |
| [`../../.claude/hooks/`](../../.claude/hooks/) | 会话钩子脚本 |
| [`../../.claude/memory/`](../../.claude/memory/) | 项目记忆索引 |
| [`../../.agents/skills/`](../../.agents/skills/) | 7 个通用/扩展 Skill |
