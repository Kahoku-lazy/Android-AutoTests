## 1. 模型表与校验

- [x] 1.1 新建 `engines/agents/config/data/models.yaml`：chat（`deepseek_flash` / `deepseek_pro` / `qwen_plus`）、realtime（`omni`）、embedding（`text_embedding_v4`）、tts（`qwen3_tts`），字段含 provider / model_name / api_key_env / base_url / input_types / context_size / max_retries / parameters / formatter；验证：`python -c "import yaml;print(len(yaml.safe_load(open('engines/agents/config/data/models.yaml',encoding='utf-8'))))"` 输出 4 个族键
- [x] 1.2 实现模型表装载器（读 YAML → 规格对象），支持 `vision` 兼容别名转换并告警；验证：`test_model_spec.py::test_vision_true_converts_to_image_types`
- [x] 1.3 实现配置校验：provider 白名单、必填非空、字段类型、`input_types` 与 `vision` 自洽、禁止提示词字段；验证：`test_model_spec.py` 的 provider / vision / prompt / dimensions 用例
- [x] 1.4 实现角色侧校验：`ModelConfig` 出现 `provider` / `model_name` / `base_url` / `api_key` 时报错并指出禁止字段；验证：`test_model_spec.py::test_role_ref_rejects_connection_fields`
- [x] 1.5 提供 `validate_models()` 显式校验入口，供门禁与启动检查调用；验证：`test_model_spec.py::test_catalog_loads_all_four_families`

## 2. 门面与加载

- [x] 2.1 门面改为按模型名取：短名与正式名都解析到同一条目；四族入口统一命名；验证：`test_model_spec.py::test_short_and_formal_name_resolve_same_spec`
- [x] 2.2 未知模型名报错并列出可用短名；验证：`test_model_spec.py::test_unknown_model_lists_candidates`
- [x] 2.3 缓存键改为 `(模型短名, 覆盖指纹, 事件循环)`，保留清空入口；验证：`test_role_build_contract.py` 复用 / 换循环 / 清空用例
- [x] 2.4 能力查询：`capabilities()` / `describe_model()` / `available_models()`，图片能力由 `input_types` 推导；验证：`test_model_spec.py::test_capabilities_derive_image_support`、`test_describe_model_never_leaks_secret`
- [x] 2.5 provider 注册表：把现有 3 个 provider 分支改为注册项，新增 provider 只加一行；验证：`test_model_spec.py::test_registered_provider_is_accepted`
- [x] 2.6 交卷关思考改为装配管线上的装饰器，保持幂等；验证：`test_forced_handover_thinking.py` 全绿

## 3. 角色迁移

- [x] 3.1 `agent_config.yaml` 5 个 `ModelConfig` 段改为 `model: <短名>` + `stream` 等调用姿势；验证：`build_ui_executor()` 能取到 `deepseek-flash` 模型
- [x] 3.2 角色装载与 `AgentRoleFactory` 适配：bundle 携带模型短名与 stream，装配层只调用门面；验证：`test_case_authoring_roles.py`、`test_role_build_contract.py` 通过
- [x] 3.3 备用模型改为「主规格 + 差量」，允许跨 provider；验证：`test_model_spec.py::test_fallback_can_cross_provider`、`test_model_retry_middleware.py` 通过

## 4. 清理与文档

- [x] 4.1 删除内置目录、`config.yaml` 覆盖死路径、`_DeepSeekModelsProxy`、`model_supports_image`；验证：`grep -rn "model_supports_image\|_DeepSeekModelsProxy\|_load_catalog_from_yaml" engines/` 无命中
- [x] 4.2 更新 `engines/agents/models/AGENTS.md` 与 `engines/agents/AGENTS.md`：模型数据落点改为 `models.yaml`，角色只写引用；验证：两份文档已改写「模型配置」小节
- [x] 4.3 原 models 设计稿（`dev_docs/DEV_TEST`）已删除，其内容并入 `engines/agents/models/AGENTS.md`；本项验证改为：该文档不含已删除文件的链接

## 5. 验证与门禁

- [x] 5.1 跑模型相关单测：`python -m pytest tests/graybox/unit/test_model_spec.py tests/graybox/unit/test_models_public_surface.py tests/graybox/unit/test_role_build_contract.py tests/graybox/unit/test_case_authoring_roles.py tests/graybox/unit/test_model_retry_middleware.py tests/graybox/unit/test_forced_handover_thinking.py -q` → 86+ 用例通过
- [x] 5.2 跑本地门禁：`python run.py check` → 阻塞项 23/23 通过
- [x] 5.3 跑 engines 风格与注释检查：`check_engines_agents_style` 的 models/ 相关告警清零；`docstrings check` 0 error

## 6. 修订：配置校验改为声明式（2026-11-10）

> 动机与决策见 `design.md`「修订」；原型见 `temps/models_config_prototype/`。

- [x] 6.1 `spec.py`：`ModelSpec` 由 frozen dataclass 改为 pydantic `BaseModel`（`frozen=True` / `extra="forbid"` / `str_strip_whitespace=True`），16 个字段带 `Field` 约束与 `Literal` 枚举；验证：`ModelSpec.model_validate` 能拦未知字段 / 类型错 / 枚举错 / 负数
- [x] 6.2 `spec.py`：新增归一层 `ModelSpec._normalize`（`mode="before"`）——拦禁键、展开 `vision`、对账 `vision` 与 `input_types`、按族给 `output_types` 缺省；验证：`test_model_spec.py` 的 vision 展开 / 矛盾 / 禁键用例
- [x] 6.3 `spec.py`：新增 `MESSAGES` + `to_spec_error()`，把 pydantic 的 `(loc, type, ctx)` 翻成 `models.yaml:族.短名.字段: 原因`；验证：报错文案用例断言中文与字段路径
- [x] 6.4 `spec.py`：删除 `validate_spec` / `check_forbidden_keys`（职责被字段声明与归一层吸收）；验证：`grep -rn "validate_spec\|check_forbidden_keys" engines/` 无命中
- [x] 6.5 `loader.py`：装载收敛为 `_parse_entry`（结构 + `validate_semantics`）→ `validate_references`（批量）→ `load_catalog`；删除 `_parse_spec` / `_parse_int` / `_parse_str_tuple` / `_parse_optional_str_tuple` / `_apply_vision`；验证：`test_model_spec.py` 全绿
- [x] 6.6 `loader.py`：新增 `validate_semantics()`（provider 已注册、族必填项、`parameters` 禁键、能力列表非空）；验证：provider / dimensions / voice 用例
- [x] 6.7 `loader.py`：新增 `validate_references()`（短名唯一 + `model_name` 必须在该 provider 该族模型目录内，`CHECK_CARD_NAMES` 可关闭）；验证：模型名写错时装载即失败并列候选
- [x] 6.8 `fallback.py`：`dataclasses.replace` → `spec.model_copy(update=...)`；验证：`test_model_retry_middleware.py` 与 `test_model_spec.py::test_fallback_can_cross_provider` 全绿
- [x] 6.9 对齐 `test_model_spec.py` 的报错文案断言；验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_model_spec.py tests/graybox/unit/test_models_public_surface.py tests/graybox/unit/test_role_build_contract.py tests/graybox/unit/test_model_retry_middleware.py tests/graybox/unit/test_forced_handover_thinking.py -q` 全绿
- [x] 6.10 门禁与文档：`python run.py check`、`check_engines_agents_style`、`docstrings check`、`openspec validate model-asset-catalog --strict` 全通过；`engines/agents/models/AGENTS.md` §4.1 同步「1 类 + 1 钩子 + 2 函数」
