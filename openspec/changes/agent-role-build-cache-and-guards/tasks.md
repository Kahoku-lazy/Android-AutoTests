## 1. 门面复用模型实例

- [x] 1.1 `engines/agents/models/chat_model.py`：新增 `get_or_create_chat_model(config)`（按配置指纹 + 事件循环弱引用判等，未命中则 `ChatModelFactory(config).create()` 并登记）与 `clear_chat_model_cache()`；`bind_forced_handover` 改为幂等（实例标记，已包装直接返回）。验证：`python -c "from engines.agents.models.chat_model import get_or_create_chat_model"` 退出码 0；同配置连续两次取到同一实例。**验证结果**：通过 —— `tests/graybox/unit/test_role_build_contract.py` 12 passed（同循环复用、换循环新建、密钥变化新建、清空后重建、二次包装 `_call_api` 身份不变）。

- [x] 1.2 `engines/agents/models/__init__.py`：`get_chat_model` 改走 `get_or_create_chat_model`，`__all__` 增加 `clear_chat_model_cache`；模块 docstring 能力清单同步。验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_models_public_surface.py -q` 通过（门面断言是 `EXPECTED_FACADE <= exported`，新增导出不破坏它）。**验证结果**：通过 —— 该文件 4 passed；`test_models_public_surface` 的子集断言未受影响。

- [x] 1.3 成本复测：`temps/time_role_build.py` 建 11 对角色，总耗时 ≤ 5 s（改前 25.2 s）。验证：脚本输出的 `total=` 值。**验证结果**：通过 —— 主线程 11 对 **1001 ms / 91 ms 每对**；循环内（真实路径）11 对 **962 ms**；改前 25195 ms / 2290 ms 每对。22 次装配只建 1 个客户端：`UI_EXECUTOR_ROLE_CONFIG` 与 `UI_VERIFIER_ROLE_CONFIG` 连接参数完全相同，共享实例。

## 2. `__all__` 与 docstring

- [x] 2.1 `engines/agents/agent_builders.py`：`__all__` 删除 `build_case_planner` / `build_case_writer_goal` / `build_case_verifier_goal`；模块 docstring 的「简介说明」编号修正为连续。验证：`python -c "from engines.agents.agent_builders import *"` 退出码 0。**验证结果**：通过 —— 改前实跑报 `AttributeError: ... has no attribute 'build_case_planner'`，改后 `import *` 成功（由 `test_star_import_succeeds` 与 `test_all_names_exist_in_agent_builders` 守住）。

## 3. 分段配置严格校验

- [x] 3.1 `engines/agents/config/role_loader.py`：`_merge_dataclass` 拒绝未知键（`ValueError`，报错列出未知键与合法键）；空节行为不变。验证：在临时 YAML 里给 `ReActConfig` 加 `max_iter` 后 `load_role_spec` 抛 `ValueError`。**验证结果**：通过 —— `test_unknown_section_key_raises`（消息含 `max_iter`）与 `test_empty_section_still_uses_defaults`（空节取默认 30 轮）均绿。

- [x] 3.2 回归：现有 6 个角色节无未知键。验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_authoring_roles.py tests/graybox/unit/test_role_build_contract.py -q` 全绿。**验证结果**：通过 —— 装载全部 4 个 LLM 角色节的用例全绿；另用一次性脚本逐节核对 `ContextConfig` / `ReActConfig` 的键集合与 dataclass 字段完全一致（无未知键）。

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_role_build_contract.py`：① `__all__` 每个名字都是模块属性；② 同配置同循环取到同一实例；③ 连接参数不同则实例不同；④ 环境变量（密钥）变化得到新实例；⑤ `clear_chat_model_cache()` 后重新构建；⑥ 未知分段键抛 `ValueError`；⑦ `bind_forced_handover` 二次调用不叠包装。验证：该文件 `-q` 全绿。**验证结果**：通过 —— 12 passed；连同既有角色/模型用例共 **69 passed**（`test_models_public_surface` / `test_case_authoring_roles` / `test_forced_handover_thinking` / `test_model_retry_middleware` / `test_case_run_continuity` / 本文件）。

## 5. 文档与门禁

- [x] 5.1 根 `AGENTS.md`：角色层描述与「参考模块」路径改为 `agent_builders` / `AgentRoleFactory` / `config/role_types.py`，与 `engines/agents/AGENTS.md` 的禁令一致。**验证结果**：通过 —— 第 26 行指向 `agent_builders.py` + `AgentRoleFactory` + `config/role_types.py`；第 74 行参考模块改为 `config/role_types.py` 与 `models/chat_model.py`。

- [x] 5.2 `dev_docs/ARCH_PRD/ARCH-平台架构设计.md`：角色层描述同步。**验证结果**：通过 —— 第 57 行不再出现 `role/` 与 `BaseRole`。

- [x] 5.3 门禁：`python run.py check` 通过；`engines-docstring-check` 与 `engines-agents-style-check` 对改动文件无新增问题；`ruff check` / `ruff format --check` 覆盖改动文件。**验证结果**：通过 —— `python run.py check` **23/23 阻塞项通过**（`engines-agents-style` 仍是既有 22 条 `raises-doc` 告警，涉及 `realtime_vocie` / `role_sys_prompts` / `device`，本次 4 个改动文件不在其中）；`docstrings check` 报 `0 error(s), 0 warn(s)`；`ruff check` 与 `ruff format --check engines/` 均通过。

- [x] 5.4 `openspec validate agent-role-build-cache-and-guards --strict` 通过。**验证结果**：通过 —— `Change 'agent-role-build-cache-and-guards' is valid`。
