## Why

角色创建链路（`YAML → load_role_spec → get_chat_model → AgentRoleFactory.create → Agent`）结构上已符合 N1/N2/N3 边界，但实测暴露三个与「角色内容」无关的问题：

1. **装配成本几乎全在模型客户端构建**：11 步用例一次建 22 个角色（执行者 + 验收者），本机实测 **25.2 s**；cProfile 显示 96% 时间在 `openai` 客户端构造时重复加载 CA 证书（每个 client 建 3 个 `SSLContext`，每次 `load_verify_locations` ≈ 0.37 s），单个角色约 1.1 s。这些时间全部发生在第一个模型调用之前，事件流里看不到任何进展。
2. **`__all__` 与实现不一致**：`engines/agents/agent_builders.py` 的 `__all__` 仍列出已删除的 `build_case_planner` / `build_case_writer_goal` / `build_case_verifier_goal`，`from engines.agents.agent_builders import *` 直接抛 `AttributeError`；现有测试只断言 `hasattr` 为假，没有任何门禁覆盖 `__all__`。
3. **分段配置拼错静默失效**：`role_loader._merge_dataclass` 只遍历 dataclass 字段，YAML 里多出的键既不报错也不生效（例如 `ReActConfig.max_iter` 少一个 `s`），属于最难排查的一类配置事故。

另外根 `AGENTS.md` 仍把角色描述为 `role/` 包（继承 `BaseRole`）并指向已删除的 `engines/agents/role/config.py`，与 `engines/agents/AGENTS.md` 的「禁止恢复 `role/` 或 `BaseRole`」直接矛盾——而根文件是默认必读项。

## What Changes

- **模型实例按配置指纹复用**：`engines.agents.models` 门面在**同一事件循环内**复用已建聊天模型实例；配置（provider / 模型名 / 地址 / 密钥 / vision / stream）任一变化即视为不同实例。跨事件循环不复用：每个平台任务在自己的线程里 `asyncio.run`，异步客户端与事件循环绑定，跨循环共享会引入连接复用风险。
- **强制交卷钩子幂等**：`bind_forced_handover` 已包装过的实例直接返回，避免共享实例被反复包裹。
- **`__all__` 与实现一致**：删除三个僵尸名，并修正模块 docstring 的编号错误；补一条「`__all__` 每个名字都必须存在」的测试。
- **分段配置严格校验**：`_merge_dataclass` 遇到未知键时抛 `ValueError`（列出未知键与合法键），空节仍取默认值。
- **文档对齐**：根 `AGENTS.md` 两处（角色层描述、参考模块路径）与 `dev_docs/ARCH_PRD/ARCH-平台架构设计.md` 的角色层描述改为当前的 `agent_builders` / `AgentRoleFactory` / `config/role_types.py`。

## Acceptance

1. 本机 `temps` 脚本建 11 对角色，总耗时从 25.2 s 降到 **5 s 以内**（同一进程、同一事件循环）。
2. `python -c "from engines.agents.agent_builders import *"` 成功；`__all__` 每个名字都是模块属性。
3. 在 `agent_config.yaml` 的 `ReActConfig` 下写一个未知键时 `load_role_spec` 抛 `ValueError` 并点名该键。
4. 门面取到的模型实例在同一循环内 `is` 相同、配置不同（如改 `vision`）时 `is not` 相同；新线程/新循环取到新实例。
5. `python run.py check` 通过；相关 pytest 全绿；注释与风格检查技能通过。

## Capabilities

### Modified Capabilities

- `agent-harness`：为「模型实例只经单一门面获取」补实例复用与循环亲和语义；新增「角色装配配置严格校验」要求（未知分段键必须报错、`__all__` 必须与实现一致）。

## Impact

- 引擎：`engines/agents/models/__init__.py`、`engines/agents/models/chat_model.py`、`engines/agents/agent_builders.py`、`engines/agents/config/role_loader.py`。
- 文档：`AGENTS.md`、`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`。
- 测试：新增 `tests/graybox/unit/test_role_build_contract.py`；现有 `test_agents.py`、`test_case_authoring_roles.py`、`test_models_public_surface.py` 应继续绿。
- 不在本期（Non-goals）：
  - 按步**惰性**建角色（缓存已把单对成本降到约 0.2 s，代价值得不单列；仍需保持「每步独立实例、不跨步继承上下文」）；
  - `agent_config.yaml` 的解析结果缓存（单次 34 ms，收益小于新增的失效语义）；
  - `role_sys_prompts` 的模块级提示词常量去重（仅测试使用，无功能影响）；
  - 用例编写角色 `middlewares=[]`（零中间件）的语义与是否补重试/追踪——待产品确认，本变更不改运行时行为。
