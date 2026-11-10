## Why

当前「基本 LLM Agent 角色」创建主路径（YAML 五段 → `load_role_config` → `AgentRoleFactory.create` → `build_*`）概念清晰，但 **配置类型住在工厂模块、装载器又反向依赖工厂**，形成 `config.models` ↔ `agent_builders` 循环依赖；同时 `models.py` 职责过重、UI/case 的 toolkit 与 middleware 策略散落在多个几乎相同的 `build_*` 样板中。需要先用 SPEC 固化「基本角色创建」边界与目标形态，再小步重构，避免与 middleware 统一化、realtime 重命名、workflow 工具旁路清理、**skills** 缠在一起。

目标颗粒度（三节点）已在 `design.md` 锁定，摘要：

1. **N1 ModelConfig**：约束+校验 YAML → 创建模型对象 → **只把 `ChatModelBase` 交给 Agent**；**Agent 不接触 ModelConfig**。
2. **N2 Agent Harness 1:1**：`RoleConfig`=name+system_prompt；`ToolsConfig`=tools（**skills 延后**）；`ContextConfig`=context；`ReActConfig`=react；配置与数据一对一、链路不交叉；留在 Agent 配置/装载层，默认不对外公共 API。
3. **N3 Agent 与 workflow**：Agent 只提供角色；workflow 负责编排（`tool_*` 旁路清理仍后续）。

## What Changes

- **固化**「基本 Agent 角色」创建契约与**三节点颗粒度**：`Agent = Model(对象) + Harness(四分段)`，经 `AgentRoleFactory` + YAML `*_ROLE_CONFIG` + `tools_config` + `role_sys_prompts`；每次 `build_*` 返回独立 `Agent` 实例；ModelConfig 止于建模型。
- **拆环（方案 B）**：将 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig` 抽到独立类型模块，使 `config.models` 与 `agent_builders` 单向依赖该模块。
- **保留薄 `build_*` 门面**：七个现有 LLM 入口与旧名别名行为不变；内部继续经 `_agent_from_role_bundle` / Factory；可选轻量 helper 减样板（非破坏性）。
- **文档对齐**：`temps/agent_create_flow_complexity.md`、`temps/agents_architecture.md`、`agent-harness`、`engines/agents/AGENTS.md`；`design.md` 锁定三节点。
- **不改运行时默认行为**（除非 tasks 明确）：UI 仍默认中间件；case 仍 `middlewares=[]`；工具仍由 `tools_config` 注入。

## Acceptance（对齐三节点）

1. **N1**：Agent 构造/运行面不接触 `ModelConfig`；仅 `ChatModelBase` 进入 Agent；Factory 内持有配置仅用于建模型。
2. **N2**：四分段类型独立模块、无 `models`↔`builders` 环；字段 1:1 不交叉；配置留在装载层；**skills 不在本期**。
3. **N3**：规格写清 Agent=角色 / workflow=编排；**不**做 workflow `tool_*` 旁路清理代码。
4. `openspec validate simplify-basic-agent-role-create --strict` 通过；相关装配 pytest 绿。

## 关联文档

- 纯架构 / 重构类变更：对齐 OpenSpec `agent-harness`、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`engines/agents/AGENTS.md`「创建 Agent 统一流程」；无独立 PRD 编号。
- 复杂度盘点：`temps/agent_create_flow_complexity.md`
- 分层总图：`temps/agents_architecture.md`

## Capabilities

### New Capabilities

- `agent-basic-role-create`: 基本 LLM Agent 角色创建路径（YAML 五段装载 → Factory → `build_*`）的行为契约与模块边界（类型归属、无循环依赖、工具经 tools_config、三节点颗粒度；skills 延后）。

### Modified Capabilities

- `agent-harness`: 补充/收紧「角色经 AgentRoleFactory 装配」「模型配置唯一装载入口」中与类型模块边界、基本角色 create 路径、ModelConfig 不进入 Agent 相关的要求（不改变「engines 零 Django」「提示词/工具唯一入口」总则）。

## Impact

- 引擎：`engines/agents/agent_builders.py`、`engines/agents/config/models.py`（及拟新增的 role 类型模块）；可能触及 `engines/agents/__init__.py` / 再导出。
- 规格：`openspec/specs/agent-harness`（delta）、新增 `agent-basic-role-create`。
- 测试：现有 `tests/engines/agents/test_agents.py`、`tests/graybox/unit/test_case_authoring_roles.py` 等装配连通性用例应继续绿；可新增「无循环 import / 类型模块可独立 import」的静态或轻量单测。
- **不在本期（Non-goals）**：
  - **skills**（ToolsConfig 扩展 skills 字段 / 产品语义）— **延后单独处理**
  - `middleware` 统一策略重写
  - `realtime_vocie*` 重命名 / 并入 Factory
  - `workflow` 对 `tool_*` 旁路清理与 create 后改 toolkit 的强制收敛
  - Django/backend 路由、配置符号彻底去公共化（允许过渡期 re-export）
  - 三节点为**目标锁定**；本期以拆环 + 边界写清 + N1 防火墙为主，不一次做完 N3 旁路清理。
