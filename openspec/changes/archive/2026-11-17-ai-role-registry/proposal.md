## Why

AI 助手要重新设计，第一步需要一张**只承载「角色」的最小表**。现有 `ai_agents` 表有 30 多个字段，把模型线路、密钥、任务类型、头像、提示词分段全糊在一行里，既不能当干净的角色注册表用，也不适合再往上叠新功能。先落一张只存「角色名称 / 模型名称 / 系统提示词 / 随机唯一 ID」的表和它的增删改查接口，后续功能再按需往上长。

## What Changes

- 新建 `ai_roles` 表（新 Model `AIRole`），只含五个业务字段：`role_id`、`name`、`model_name`、`system_prompt`、`created_at` / `updated_at`。
- `role_id` 为**当天日期（`YYYYMMDD`）+ 3 位随机字符**，字符集 `[0-9a-z]`，全表唯一、生成时绝不重复；不暴露自增主键作为对外标识。
- `name` 全表唯一，重名拒绝并返回可读错误。
- 新增角色增删改查接口：`GET/POST /api/ai/roles/`、`GET/PATCH/DELETE /api/ai/roles/{role_id}/`；成功响应统一 `{status, data}` 信封，路径带尾斜杠。
- `model_name` 本次**只做存储，不做取值校验**：它是一个留给后续装配的位置，本期不与引擎模型表联动，也不提供任何模型清单接口。
- `system_prompt` 本期**只做存储**：正文入库，不与 `engines/ae_harness/agents/config/prompts/*.md` 建立同步或覆盖关系，也不接入运行时。
- `ai_agents` 表与它的接口、任务清单、看板、bug 单等既有引用**完全不动**；前端不动。

**非目标（本期明确不做）**：角色的运行时装配与执行、模型清单或模型选择接口、提示词与仓库 `.md` 的双写或同步、角色与任务/会话的关联、权限模型细化（沿用现有登录态）、批量导入导出、软删除。

## 关联文档

无 PRD 编号。本次需求来源为「AI 助手模块重设计」的第一批后端底座，仅落表与 CRUD，不含业务行为。

## Capabilities

### New Capabilities

- `ai-role-registry`: 角色注册表的存储契约（字段、唯一性、`role_id` 生成规则）与增删改查接口契约（路径、方法、信封、错误码）。

### Modified Capabilities

无。`ai-assistant` 现有需求（智能体接口不下发头像大字段）行为不变；`role-prompt-guardrails` 约束的是提示词**内容**，与本次的存储位置无关。

## Impact

- 代码：`backend/apps/ai_assistant/`（`models.py`、`api.py`、`serializers.py`、`views_drf.py`、`urls.py`、`admin.py`，新增一个 migration）。
- 数据库：新增表 `ai_roles`（新迁移，不改动任何既有表）。
- API：新增 `/api/ai/roles/` 一族；既有端点无改动。
- 测试：`tests/ai_assistant/unit/`（ID 生成与唯一性、重名拒绝、api 层写库）与 `tests/ai_assistant/api/`（CRUD 契约）。
- 引擎：**无改动**，不碰 `engines/`。
- 前端：**无改动**，本期只到后端接口。
