## 1. 只读视图

- [x] 1.1 新增 `engines/agents/config/model_view.py`：从已装载表按短名返回冻结视图（`model_name` / `family` / `voices` / `dimensions` / `api_key_env`）；未知短名抛 `ValueError` 并列出可选短名；不调用 `reveal()`。验证：新增不联网单测覆盖已知短名、未知短名、缺密钥仍可查看、`repr` 不含明文。
- [x] 1.2 `role_loader.py` 改为用只读视图确认短名存在，去掉对 `engines.agents.models` 的 `RoleModelRef` / `get_model` / `load_role_model_ref` 依赖；角色引用形状留在 config。验证：`python -m pytest -c tests/pytest.ini tests/case/unit/test_case_run_continuity.py tests/engines/agents/unit/test_role_build_contract.py -q` 通过，且该文件不再 import 旧包。
- [x] 1.3 `knowledge_chat/config.py`、`realtime_vocie/config.py` 的默认模型名、`rag/config.py` 的默认嵌入名与维度，改为读只读视图，不创建模型。验证：`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_chat_session.py tests/knowledge/unit/test_knowledge_assistant_config.py -q` 通过。
- [x] 1.4 `backend/apps/knowledge_assistant/consumer.py` 的音色白名单改为读只读视图的 `voices`；缺失时为空，空列表不拦截。验证：`python -m pytest -c tests/pytest.ini tests/knowledge/ -q` 中音色相关用例通过；非法音色仍返回可读错误。

## 2. 造实例改道

- [x] 2.1 `rag/service.py` 改为 `load_model_config()` + `create_model(表, 短名)` 取嵌入模型；删除调用点明文 `api_key` 与 `dimensions` 覆盖。用量只在 RAG 服务内记录，不作为 `create_model` 参数。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_retrieve.py tests/engines/agents/unit/test_rag_store.py -q` 通过。
- [x] 2.2 删除 `realtime_vocie/config.py::create_realtime_model` 及其包导出；会话路径只保留 `create_voice_agent`。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_realtime_vocie_models.py -q` 通过，且仓内无第二套 Omni 构造调用。
- [x] 2.3 `messaging/billing.py` 的 Flash / Pro 档名改为从只读视图取正式模型名，删除 `DeepSeekModelConfig` 导入；旧名别名仍按 Flash 价。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_billing_eight_decimals.py -q` 通过。

## 3. 交卷行为搬家

- [x] 3.1 把强制结构化交卷时关闭思考的改写从旧包装饰器挪到 `engines/agents/middleware/`，由现有中间件装配在调用前改写；非交卷请求原样返回，共享模型不叠包装。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_forced_handover_thinking.py -q` 通过。

## 4. 删除旧包

- [x] 4.1 确认生产代码与测试不再 import `engines.agents.models` 后，删除 `engines/agents/models/`。门面守卫改为：包外不构造聊天 / 实时 / 嵌入 / 合成模型类，且不 import 已删除包。验证：`rg "engines\.agents\.models" --glob "*.py"` 无命中；`python -m pytest -c tests/pytest.ini tests/models/unit/test_models_public_surface.py tests/engines/agents/unit/test_model_retry_middleware.py -q` 通过。
- [x] 4.2 更新 `engines/agents/AGENTS.md`、`engines/agents/config/AGENTS.md`、`engines/agents/models_new/AGENTS.md`：造实例只经 `models_new`，查规格只经 `config.model_view`，删除旧包归属描述。验证：三份文档不再把 `engines/agents/models` 写成模型唯一归属；`models/AGENTS.md` 随包删除。

## 5. 收口

- [x] 5.1 跑注释与风格检查，以及模型替换相关单测。验证：`cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check` 无本次新增 error；`cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style` 通过；`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_assistant_create.py tests/engines/agents/unit/test_role_build_contract.py tests/knowledge/unit/test_knowledge_chat_session.py tests/engines/agents/unit/test_rag_retrieve.py -q` 通过。
