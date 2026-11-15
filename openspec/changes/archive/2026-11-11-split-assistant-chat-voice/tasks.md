## 1. 拆出口

- [x] 1.1 `assistant` 门面改为导出 `create_chat_agent`、`create_voice_agent` 与 `AgentConfigError`，不再导出按实例类型分支的 `create_agent`。验证：`python -c "from engines.agents.assistant import create_chat_agent, create_voice_agent, AgentConfigError"` 成功，且 `create_agent` 不在包导出中。
- [x] 1.2 聊天出口只接受 `family=chat`，返回新的 `Agent`；realtime / embedding / tts 抛 `AgentConfigError`，消息含角色键和实际族。不调用 `reply`。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_assistant_create.py -q` 覆盖成功与三种拒绝。
- [x] 1.3 语音出口只接受 `family=realtime`，返回新的 `RealtimeAgent`；其它族拒绝。显式传入 context、react、中间件或 stream 时拒绝，不静默丢弃。语音模型不进聊天缓存。验证：同一单测文件覆盖成功、错族和多余参数。

## 2. 调用方改转调

- [x] 2.1 `agent_builders._build` 只转调 `create_chat_agent`。`build_ui_executor` / `build_case_writer` / `build_knowledge_chat` 的对外名字与返回类型不变。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_role_build_contract.py tests/case/unit/test_case_authoring_roles.py -q` 通过。
- [x] 2.2 `realtime_vocie/session.py` 与 `realtime_vocie_agent.py` 只转调 `create_voice_agent`。传输与 `reply_stream` 仍留在会话。验证：两处源码不再调用 `create_agent`；`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_assistant_config.py -q` 通过。
- [x] 2.3 更新 `engines/agents/assistant/AGENTS.md`：两个出口、各自拒绝的参数、TTS / 嵌入不进本包。验证：文档与门面导出一致。

## 3. 守卫

- [x] 3.1 包外不再引用已删除的 `create_agent`。`Agent(` / `RealtimeAgent(` 仍只允许出现在 `assistant/`。验证：`rg "create_agent" engines tests` 无旧出口引用；既有构造守卫测试通过。
- [x] 3.2 注释与风格自检。验证：在 `.agents/skills/engines-docstring-check` 跑 `python -m scripts.docstrings check`，在 `.agents/skills/engines-agents-style-check` 跑 `python -m scripts.check_engines_agents_style`，本次 engines 改动无新 error。
