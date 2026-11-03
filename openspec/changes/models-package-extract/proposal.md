## Why

「模型」这件事目前没有单一归属：`engines/agents/config/models.py` 一个文件 803 行，把模型类型、模型工厂、角色四分段装载、命名模型目录混在一起；真正「造模型实例」的代码散在 5 处，其中 3 处不在任何模型模块里（`agent_builders` 的主模型与备用模型、`realtime_vocie/config.py` 的 Omni、`rag/service.py` 的嵌入、`middleware/tts.py` 的语音合成）。连带把**模型能力知识**（`model_supports_image`、`DEEPSEEK_MODELS`）放进了提示词模块，把**备用模型连接参数**（`AGENT_FALLBACK_*`）放进了重试中间件。

结果是改模型相关的一处要翻四五个模块，调用方还得自己懂 `ModelConfig`、`api_key`、`vision`、`stream` 怎么传。调用方要的其实只有一句「给我这个角色的模型」。

## What Changes

- **新增 `engines/agents/models/` 包**：`types`（配置数据类）、`catalog`（命名模型目录 + 能力查询）、`chat_model`（聊天模型工厂 + 强制交卷关思考）、`realtime_model`（Omni）、`embedding_model`（含用量计量）、`tts_model`、`loader`（只读 YAML 的 `ModelConfig` 段）、`fallback`（备用模型）。每文件单一职责。
- **对外只留一个门面**：其它模块 `from engines.agents.models import get_chat_model` 即可取到模型；`get_chat_model` / `get_fallback_chat_model` / `get_realtime_model` / `get_embedding_model` / `get_tts_model` / `get_text`·`get_realtime`·`get_embedding` / `model_supports_image`。MUST NOT 再直接 import 子模块或自行构造 agentscope 模型实例。
- **模型配置代码归 models，数据仍留 config**：`config/data/agent_config.yaml` 与 `config/data/config.yaml` 内容与位置不变；`loader` 只经 `config.config.load_agent_config` 读数据。
- **角色装载与模型装载拆开**：删除 `engines/agents/config/models.py`；四分段装载迁到 `engines/agents/config/role_loader.py`，`load_role_config` 不再返回 `ModelConfig`（改返回角色键 + 四分段）。**BREAKING**：仓内 `ui_*_role_config` / `case_*_role_config` 五元组 API 退役。
- **5 个创建点收口**：`agent_builders`（主模型 + 备用模型）、`realtime_vocie/config`（Omni，与 `omni_realtime_model` 的重复实现合并为一处）、`rag/service`（嵌入 + 用量计量）、`middleware/tts`（语音合成）。中间件只接收已建好的模型实例。
- **备用模型参数迁出重试模块**：`AGENT_FALLBACK_MODEL` / `AGENT_FALLBACK_PROVIDER` / `AGENT_FALLBACK_BASE_URL` / `AGENT_FALLBACK_API_KEY` 由 `models/fallback.py` 解析；`RetrySettings` 只保留次数、退避与开关。环境变量名不变，运维配置零改动。
- **模型能力知识迁出提示词模块**：`model_supports_image` / `DEEPSEEK_MODELS` 从 `role_sys_prompts` 移到 `models/catalog`，提示词模块不再持有模型元数据。
- **加门面守卫单测**：扫描 `engines/` 的 import，出现 `engines.agents.models.<子模块>` 直接失败，防止门面被旁路。

## 关联文档

无 PRD 需求编号。本次是结构重构：触发于「模型配置代码归口 models、调用方只经一个门面取模型」的架构要求；约束来源为根 `AGENTS.md`「Agent = Model + Harness」与 `engines/agents/AGENTS.md`「创建 Agent 统一流程」。不新增产品行为。

## Capabilities

### New Capabilities

（无：不新增产品能力，只调整模型相关代码的落点与对外入口。）

### Modified Capabilities

- `agent-harness`: 「模型配置唯一装载入口」改为「模型代码在 `engines/agents/models`、数据在 `config/data`、角色装载留在 `config`」；新增「其它模块只经 `engines.agents.models` 门面取模型实例」的约束。

## Impact

- 新增：`engines/agents/models/`（9 个文件，含 `AGENTS.md`）、`engines/agents/config/role_loader.py`。
- 删除：`engines/agents/config/models.py`。
- 修改：`engines/agents/agent_builders.py`、`realtime_vocie_agent.py`、`realtime_vocie/config.py`、`rag/service.py`、`middleware/tts.py`、`middleware/model_retry.py`、`middleware/assembly.py`、`messaging/billing.py`、`role_sys_prompts.py`、`config/__init__.py`、`config/role_types.py`（注释）。
- 测试：`tests/engines/agents/test_models.py`、`test_agents.py`、`tests/graybox/unit/test_forced_handover_thinking.py`、`test_case_run_continuity.py`、`test_case_authoring_roles.py`、`test_model_retry_middleware.py`（import 与断言），新增 `tests/graybox/unit/test_models_public_surface.py`（门面守卫）。
- 文档：`engines/agents/AGENTS.md`（模块表与统一流程）、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`openspec/specs/agent-harness/spec.md`（经本变更 delta）。
- 行为：对外零行为变化——同样角色取到同样的模型、同样的环境变量、同样的报错条件；唯一可见差异是错误文案里的模块路径与角色装载函数的返回形状（仓内调用方同步改）。
- 不影响：SOP 执行、中间件顺序与开关、事件/计费链路、前端、数据库。
