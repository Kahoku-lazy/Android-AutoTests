## 0. 范围锁定

- [x] 0.1 确认本 change **仅**覆盖三节点边界 + 类型拆环；**skills / middleware 统一 / realtime / workflow `tool_*` 旁路**均为 Non-goals；验证：proposal/design Non-goals 与本 tasks 无对应实现项。
- [x] 0.2 对照 `temps/agent_create_flow_complexity.md` 与 WIP：7× LLM `build_*` + `_agent_from_role_bundle` + `load_role_config` 未漂移；验证：文档入口列表与 `agent_builders.py` 一致。

## 1. N1 — ModelConfig → 校验 → ChatModelBase only（禁泄漏）

- [x] 1.1 边界写清：`Agent` 构造/运行面 MUST NOT 接收或持有 `ModelConfig`；仅 `ChatModelBase`（或等价）进入 Agent；验证：design + `agent-basic-role-create` spec 有对应 MUST NOT。
- [x] 1.2 实现对齐：`AgentRoleFactory.create` 经 `ChatModelFactory` 建模型后只把 model 交给 `Agent`；Factory 可短暂持有 `ModelConfig` **仅**用于建模型；验证：grep `Agent(` 无传入 ModelConfig + 相关 pytest 绿。

## 2. N2 — Harness 1:1（Role / Tools / Context / ReAct）；skills 延后

- [x] 2.1 新增独立类型模块承载四分段 dataclass（**本期不扩展 skills 字段**）；验证：可不 import `agent_builders`、不触发 Agent 创建即可 import。
- [x] 2.2 `engines/agents/config/models.py`：装载仅从类型模块导入；删除对 `agent_builders` 的 runtime / TYPE_CHECKING 依赖；验证：`python -c "import engines.agents.config.models"` 成功且依赖图无 `agent_builders`。
- [x] 2.3 `engines/agents/agent_builders.py`：从类型模块导入；过渡期 re-export 保留；四分段字段 1:1、不交叉；`ToolsConfig` 仍以现有 toolkit 占位/注入为准；验证：`from engines.agents.agent_builders import RoleConfig, AgentRoleFactory` 可用。
- [x] 2.4 四分段留在 **Agent 配置/装载层**，不作为稳定公共 API（对外以 `build_*` → `Agent`）；验证：AGENTS.md / design 标明非公共面。
- [x] 2.5 `build_*` 仍经 `_agent_from_role_bundle` → Factory；toolkit 仍经 `tools_config`；可选瘦 helper，**不**改对外函数名与 middleware 默认（case 仍 `middlewares=[]`）；验证：`pytest tests/engines/agents/test_agents.py tests/graybox/unit/test_case_authoring_roles.py -q`。

## 3. N3 — Agent = 角色；workflow = 编排（旁路清理延后）

- [x] 3.1 规格写清：Agent 只提供已装配角色；workflow 消费 `build_*` → Agent，不以 ModelConfig / 四分段为编排 API；验证：spec 有对应 Requirement / Scenario。
- [x] 3.2 **不**实现 `workflow` → `tool_*` / create 后改 toolkit 清理；验证：本 change 无该类代码改动项。

## 4. 规格与门禁

- [x] 4.1 `openspec validate simplify-basic-agent-role-create --strict` 通过。
- [x] 4.2 更新 `engines/agents/AGENTS.md`「创建 Agent 统一流程」：类型模块路径 + 三节点边界（含 skills 延后）；必要时改 `temps/agents_architecture.md` 为「已拆环」。
- [x] 4.3 `ruff check` 覆盖改动文件；相关 pytest 全绿；无新增 `engines` → `django` / `apps` import。
