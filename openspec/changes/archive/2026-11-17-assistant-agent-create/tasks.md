## 1. assistant 创建层

- [x] 1.1 新增 `engines/agents/assistant/`（`__init__.py` / `schema.py` / `loader.py` / `create.py`）与包级 `AGENTS.md`。门面只导出 `create_agent` 与 `AgentConfigError`。验证：`python -c "from engines.agents.assistant import create_agent, AgentConfigError"` 成功，且包内无 `import yaml`、无 `engines.agents.models` 导入。
- [x] 1.2 `schema.py` 校验角色节：必填模型短名、name、system_prompt；context / react 可缺省；出现 `provider` / `model_name` / `api_key` / `base_url` 直接报错。验证：单测覆盖缺字段、未知字段、连接参数被拒，错误信息带角色键。
- [x] 1.3 `loader.py` 从传入的整张角色表按键取节并校验；不读文件。未知键报错且列出可选键。验证：单测用内存 dict，不依赖磁盘 YAML。
- [x] 1.4 `create.py` 用角色节短名调用 `models_new.create_model`：`chat` 造 `Agent`，`realtime` 造 `RealtimeAgent`，其它族拒绝。每次新实例；不调用 `reply` / `reply_stream`。可选 `toolkit` / `middlewares` / `system_prompt` 覆盖。验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_assistant_create.py -q` 通过（假模型，不联网）。

## 2. 旧入口转调

- [x] 2.1 `agent_builders.build_*` 改为读 `load_agent_config` + `load_model_config`，解析提示词后转调 `create_agent`；工具包仍由 `tools_config` 注入。`Agent(` 不再出现在该文件。验证：`build_ui_executor()` / `build_case_writer()` 返回 `Agent`，名字与现 YAML 一致；`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_role_build_contract.py tests/case/unit/test_case_authoring_roles.py -q` 通过。
- [x] 2.2 `realtime_vocie_agent.build_realtime_vocie_agent` 改为转调 `create_agent(..., "OMNI_ROLE_CONFIG")`，仍返回 `(agent, model)`。`run_local_s2s` 留在原文件。验证：该函数源码不再含 `RealtimeAgent(`；无密钥时仍在创建前给出可读错误。
- [x] 2.3 `realtime_vocie/session.py` 删除内联 `RealtimeAgent(...)`，把会话算好的 name、追加后的 system_prompt、RAG toolkit 覆盖传入 `create_agent`。验证：`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_assistant_config.py tests/knowledge/unit/test_knowledge_chat_session.py -q` 通过；追加后的提示词进入实例。

## 3. 边界守卫

- [x] 3.1 增加 AST 守卫：`engines/agents` 下 `Agent(` 与 `RealtimeAgent(` 只允许出现在 `assistant/`。`workflow/` 仍不得直接调用角色装配。验证：新测试命中旁路构造即失败；`tests/engines/agents/unit/test_workflow_boundary.py` 仍通过。
- [x] 3.2 注释与风格自检。验证：在 `.agents/skills/engines-docstring-check` 跑 `python -m scripts.docstrings check`，在 `.agents/skills/engines-agents-style-check` 跑 `python -m scripts.check_engines_agents_style`，本次新增 engines 文件无新 error。

> **2026-11-17 归档**：按需求方决定直接归档，未完成项不再执行；本次 delta 因场景契约不匹配未合并，delta 原文保留在本目录 specs/ 下。
