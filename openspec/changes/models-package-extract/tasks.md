## 1. 建包骨架（纯搬移，先可独立 import）

- [x] 1.1 新建 `engines/agents/models/types.py`：搬 `ModelConfig`、`RealtimeModelConfig` 两个纯数据类（含 `Attributes:` / `Raises:` 注释），不加任何 IO、不建模型实例；验证：`python -c "from engines.agents.models.types import ModelConfig, RealtimeModelConfig; print(ModelConfig().provider)"` 输出空串。
- [x] 1.2 新建 `engines/agents/models/catalog.py`：搬 `TextModelReady` / `RealtimeModelReady` / `EmbeddingModelReady` 三个目录项（含 `to_model_config` / `create_chat_model` / `create_realtime_model` 便捷方法）、内置目录、`TEXT_MODELS` / `REALTIME_MODELS` / `EMBEDDING_MODELS`、`get_text` / `get_realtime` / `get_embedding`、`DeepSeekModelConfig`、`model_supports_image`；目录覆盖文件改为显式指向 `engines/agents/config/data/config.yaml`（缺失则用内置默认）；验证：`python -c "from engines.agents.models.catalog import TEXT_MODELS; print(sorted(TEXT_MODELS))"` 输出 `['deepseek_flash', 'deepseek_pro']`。
- [x] 1.3 新建 `engines/agents/models/chat_model.py`：搬 `ChatModelFactory` 与 `apply_forced_handover_kwargs` / `bind_forced_handover`（`GenerateStructuredOutput` 时关思考的行为逐字不变）；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_forced_handover_thinking.py -q` 通过（该文件 import 暂指向旧模块，稍后统一改）。

## 2. 装载与备用模型

- [x] 2.1 新建 `engines/agents/models/loader.py`：只读 `agent_config.yaml` 的 `<KEY>.ModelConfig` 段，产出 `ModelConfig` / `RealtimeModelConfig`（保留现有校验与报错条件：缺节、`api_key` 非变量名、未知字段、`base_url` 非字符串）；验证：`python -c "from engines.agents.models.loader import load_model_config; print(load_model_config('UI_EXECUTOR_ROLE_CONFIG').model_name)"` 打印出 YAML 里配置的模型名。
- [x] 2.2 新建 `engines/agents/models/fallback.py`：解析 `AGENT_FALLBACK_MODEL` / `_PROVIDER` / `_BASE_URL` / `_API_KEY`，复用主模型的 vision / stream 与默认密钥地址，返回已建好的备用聊天模型；未配置模型名返回 `None`；验证：`AGENT_FALLBACK_MODEL= python -c "from engines.agents.models.fallback import build_fallback_chat_model; print(build_fallback_chat_model('UI_EXECUTOR_ROLE_CONFIG'))"` 输出 `None`。
- [x] 2.3 从 `middleware/model_retry.py` 移除四个 `_FALLBACK_*_ENV` 与 `RetrySettings` 的 fallback 字段，只留 attempts / base_delay / max_delay / enabled；同步 `middleware/__init__.py` 导出；验证：`python -c "from engines.agents.middleware import load_retry_settings; print(vars(load_retry_settings()))"` 不含 `fallback_` 键。

## 3. 三类非聊天模型收口

- [x] 3.1 新建 `engines/agents/models/realtime_model.py`：合并 `config/models.omni_realtime_model` 与 `realtime_vocie/config.create_realtime_model` 的模型构造（provider 仅 dashscope、缺 `agentscope[realtime]` 抛 `RuntimeError`、支持自定义 `Parameters`）；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_realtime_vocie_models.py -q` 通过。
- [x] 3.2 新建 `engines/agents/models/embedding_model.py`：搬 `DashScopeEmbeddingModel` 用量计量子类，暴露 `build_embedding_model(api_key, model_name, dimensions, usage_sink)`；验证：`python -c "import engines.agents.models.embedding_model as m; print(callable(m.build_embedding_model))"` 输出 `True`。
- [x] 3.3 新建 `engines/agents/models/tts_model.py`：搬 `DashScopeTTSModel` 构造（含 `AGENT_TTS_MODEL` / `AGENT_TTS_VOICE` 默认值与缺依赖判定的返回语义）；验证：`python -c "import engines.agents.models.tts_model as m; print(m.DEFAULT_MODEL)"` 输出 `qwen3-tts-flash`。

## 4. 门面与包文档

- [x] 4.1 新建 `engines/agents/models/__init__.py`：只导出 `get_chat_model` / `get_fallback_chat_model` / `get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_text` / `get_realtime` / `get_embedding` / `model_supports_image` / `DeepSeekModelConfig`，并显式维护 `__all__`；验证：`python -c "import engines.agents.models as m; print(sorted(m.__all__))"` 与清单一致。
- [x] 4.2 写 `engines/agents/models/AGENTS.md`：本包职责、数据归 `config/data` 的红线、门面唯一入口、职责判定表（连接参数→models / 四分段→config / 数据→config/data / 退避重试→middleware）；验证：`python -m scripts.docstrings check --path engines/agents/models` 无新增 error（在 `.agents/skills/engines-docstring-check` 下运行）。

## 5. 拆分角色装载

- [x] 5.1 新建 `engines/agents/config/role_loader.py`：搬 `_is_empty_section` / `_merge_dataclass` / `_build_role_config` / `_build_tools_config`，提供 `load_role_spec(role_key) -> RoleBundle`（`role_key` + 四分段），保留空节默认 `Toolkit()`、`app_info` 追加、角色节为空报错；验证：`python -c "from engines.agents.config.role_loader import load_role_spec; b = load_role_spec('UI_EXECUTOR_ROLE_CONFIG'); print(b.role.name, b.react.max_iters)"`。
- [x] 5.2 改 `engines/agents/agent_builders.py`：`AgentRoleFactory` 改为接收已建好的 `model`（+ 可选 `fallback_model`），`build_*` 用 `load_role_spec(role_key)` + `get_chat_model(role_key)` + `get_fallback_chat_model(role_key)`；删除 `_fallback_chat_model` 与本文件对 `config.models` 的 8 处 import；验证：`python -c "from engines.agents.agent_builders import build_ui_executor; print(type(build_ui_executor()).__name__)"` 输出 `Agent`。

## 6. 改剩余调用方

- [x] 6.1 改 `realtime_vocie_agent.py`（用 `load_role_spec("OMNI_ROLE_CONFIG")` + `get_realtime_model`）与 `realtime_vocie/config.py`（`create_realtime_model` 只组装 `Parameters` 后调门面，`DEFAULT_OMNI_MODEL` / `get_realtime` 改从 `engines.agents.models` 取）；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_assistant_config.py tests/graybox/unit/test_realtime_vocie_models.py -q` 通过。
- [x] 6.2 改 `rag/service.py` 与 `rag/config.py`：用 `get_embedding_model(api_key, usage_sink=...)`，删 `_UsageEmbeddingModel` 与 `agentscope.embedding` 导入；`get_embedding` 改从 `engines.agents.models` 取；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_rag_store.py -q` 通过。
- [x] 6.3 改 `middleware/tts.py`：只保留开关、缺密钥与缺依赖的降级，构造走 `get_tts_model()`；验证：`python -c "from engines.agents.middleware.tts import build_tts_middleware; print(build_tts_middleware())"` 输出 `None`（开关默认关）。
- [x] 6.4 改 `messaging/billing.py` 与 `role_sys_prompts.py`：`DeepSeekModelConfig` 改从 `engines.agents.models` 取；删除 `role_sys_prompts` 内的 `DEEPSEEK_MODELS` 代理与 `model_supports_image`（含 `__all__` 条目）；验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/test_billing_eight_decimals.py -q` 通过。

## 7. 删除旧模块与收尾

- [x] 7.1 删除 `engines/agents/config/models.py`，更新 `engines/agents/config/__init__.py`、`config/role_types.py` 里对它的描述；验证：`rg "config\.models|config import models" engines backend tests` 无输出，且 `python -c "import engines.agents.agent_builders, engines.agents.rag.service, engines.agents.realtime_vocie.session, engines.agents.middleware.assembly"` 成功。
- [x] 7.2 更新 6 个测试文件的 import 与断言（`test_models.py`、`test_agents.py`、`test_forced_handover_thinking.py`、`test_case_run_continuity.py`、`test_case_authoring_roles.py`、`test_model_retry_middleware.py`，后者把 4 条 `AGENT_FALLBACK_*` 断言迁到 models 侧）；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_run_continuity.py tests/graybox/unit/test_case_authoring_roles.py tests/graybox/unit/test_forced_handover_thinking.py tests/graybox/unit/test_model_retry_middleware.py -q` 全过。
- [x] 7.3 新增 `tests/graybox/unit/test_models_public_surface.py`：AST 扫描 `engines/**/*.py`（跳过 `engines/agents/models/**`）断言无 `engines.agents.models.<子模块>` 导入，且非 models 包内无 `agentscope` 模型类构造；验证：该测试文件单独通过，且故意在 `rag/service.py` 加一行子模块导入时用例会失败（手工验证后还原）。

## 8. 文档与整体验证

- [x] 8.1 同步 `engines/agents/AGENTS.md`（模块表把 `config/models.py` 换成 `models/` 包 + `config/role_loader.py`，统一流程的「模型配置」步骤改为经门面取模型）与 `dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`；验证：`rg "config\.models" engines dev_docs` 无输出。
- [x] 8.2 跑注释与风格自检：`cd .agents/skills/engines-docstring-check; python -m scripts.docstrings check`，再 `cd .agents/skills/engines-agents-style-check; python -m scripts.check_engines_agents_style`；验证：本次改动文件无新增 error，输出贴进结论。
- [x] 8.3 跑回归与门禁：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_agent_middleware_assembly.py tests/graybox/unit/test_model_retry_middleware.py tests/graybox/unit/test_rag_store.py tests/graybox/unit/test_case_authoring_roles.py -q` + `ruff check engines/agents` + `python run.py check`；验证：pytest 全过、ruff 无新增、`run.py check` 阻塞项与 HEAD 基线一致（不新增失败）。
- [x] 8.4 真机冒烟：用单步 UI 执行任务（设备 `R5CT62RH88F`）跑一条用例，确认模型照常建出、`GenerateStructuredOutput` 交卷、日志 `运行阶段：completed`；验证：任务状态 completed，`logs/agents/agent_events.log` 里无导入/构造相关异常。
