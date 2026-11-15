## Why

模型连接参数被复制进 5 个角色的 `ModelConfig` 段：同一个 `deepseek-flash` 有 5 份事实，改一次模型要改 5 处，且模型能力靠手写 `vision: true` 表达。模型因此与角色强绑定，"给某个角色换模型"和"给所有角色换同一个模型"是两种改法、两套风险。

## What Changes

- 新增 `engines/agents/config/data/models.yaml` 作为**唯一模型数据源**，覆盖 chat / realtime / embedding / tts 四族；每条声明 provider、正式模型名、密钥环境变量、`base_url`、能力（`input_types` / `output_types`）、`context_size`、`output_size`、默认 `parameters`、`formatter`。
- 角色 `ModelConfig` 收缩为「引用 + 调用姿势」：`model: <短名>` 加 `stream` / `temperature` 等；在角色里写 `provider` / `model_name` / `api_key` 等连接参数直接报错。
- 门面改为**按模型名取模型**：`get_chat_model("deepseek_flash")`、`get_realtime_model("omni")`、`get_embedding_model("text_embedding_v4")`、`get_tts_model("qwen3_tts")`，任何角色、任何位置都可调用，不再要求角色键。**BREAKING**
- 新增**配置校验**：provider 白名单、必填字段与类型、能力声明自洽（`vision` 与 `input_types` 冲突即失败）、密钥环境变量能否解析；报错带 `models.yaml` 行号与字段路径。
- 视觉能力由 `input_types` 是否含 `image/*` **推导**，删除手写 `vision: true` 的真相；需要图片的模型由 adapter 选路（DeepSeek 走 OpenAI 兼容客户端）。
- 模型级参数可配置：`context_size`（压缩阈值基数）、`max_retries`、`formatter`、`parameters` 默认值；角色与调用点可覆盖。
- 备用模型以主模型 spec 为基线、只声明差量，支持跨 provider。
- **BREAKING**：`get_chat_model(role_key)` 的「按角色键」语义移除；调用方统一改为模型短名。

## 关联文档

- PRD-平台总需求（AI 执行内核：AgentScope SOP 双角色）
- ARCH-平台架构设计（Model + Harness 分层：Model 为独立资产，角色只引用）
- 模块设计：`engines/agents/models/AGENTS.md`

## Capabilities

### New Capabilities

- `agent-model-catalog`: 模型资产目录——`models.yaml` 唯一数据源、配置校验、按模型名加载四族模型、能力查询、实例复用、备用模型派生。

### Modified Capabilities

- `agent-harness`: 「模型配置唯一装载入口」「模型实例只经单一门面获取」「实例复用指纹」三条要求的装载形式与缓存键随模型资产化而变化；角色装配仍只接收已建好的模型实例。

## Impact

- 代码：`engines/agents/models/`（全部）、`engines/agents/agent_builders.py`、`engines/agents/config/role_loader.py`、`engines/agents/config/config.py`。
- 数据：新增 `engines/agents/config/data/models.yaml`；`agent_config.yaml` 的 5 个 `ModelConfig` 段改为引用。
- 测试：`tests/graybox/unit/test_models_public_surface.py`、`test_case_authoring_roles.py`、`test_role_build_contract.py`、`test_model_retry_middleware.py`、`tests/engines/agents/test_models.py`。
- 文档：`engines/agents/models/AGENTS.md`、`engines/agents/AGENTS.md`（模型数据落点与引用方式）。
- 不影响：智能体配置页（`ai-agent-model-config`，那是 AI 助手的模型选择 UI，不是引擎模型层）。
