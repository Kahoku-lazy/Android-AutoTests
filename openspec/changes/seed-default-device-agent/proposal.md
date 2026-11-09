## Why

从远程全新拉取并 `migrate` 后，平台只剩 1 个智能体（`Agent-02` 用例编写），设备执行的默认智能体不存在——它只是某台机器 `ai_agents` 表里的历史手工数据。同时，唯一的种子迁移把 owner 取为「迁移时刻的第一个超级管理员」，而项目标准启动顺序是「先 `migrate`、后 `createsuperuser`」，于是干净库上种子行的 owner 为 `NULL`：普通用户在列表里看不到它，提交任务时也会被判不可见。

## What Changes

- 新增数据迁移，种下默认的**设备执行**智能体（`task_kind=device_control`）。已存在任意设备执行智能体的库（含现存手工数据）不重复创建，保证幂等。
- 修正「无主」语义为**平台共享**：`owner_id` 为空的智能体对所有登录用户可见、可用于提交任务；不再依赖「迁移时点是否已有超级管理员」。
- 迁移内顺带把仍是 `NULL` owner 的智能体回填给「当前已存在的第一个超级管理员」（存在时），让旧库逐步收敛到显式归属。
- 新增单测覆盖：无主智能体对普通用户可见/可用、种子迁移的幂等与回填行为。

## 关联文档

- 需求入口：PRD-平台总需求 §「AI 助手 / 智能体身份」（智能体记录只决定归属与任务类型）
- 既有规格 `admin-managed-shared-agent`：本变更补「默认智能体种子化」与「无主 = 平台共享」两条要求
- 根 `README.md`「快速开始」：`migrate` → `createsuperuser` 的执行顺序是本变更的成因

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `admin-managed-shared-agent`: 新增「默认智能体随迁移种子化」与「无主智能体视为平台共享」两条需求，使智能体集合不依赖任何机器的历史数据、也不依赖启动顺序。

## Impact

- 代码：`backend/apps/ai_assistant/migrations/`（新增数据迁移）、`backend/apps/ai_assistant/api.py`（`filter_agents_for_user`）、`backend/apps/ai_assistant/permissions.py`（`check_agent_visible`）
- API：`GET /api/ai/agents/` 对普通用户会多出「无主智能体」；响应结构不变
- 测试：`tests/graybox/unit/`（可见性与迁移幂等）
- 前端：无改动（沿用「一个可见 Agent 一张卡」）
