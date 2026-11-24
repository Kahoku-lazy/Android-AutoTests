## Why

知识库的向量模型、库目录和型号日志关键词还各留着一份本地文件，与平台已有的模型配置、知识库模块登记、串口关键词表重复维护。本地文件是引擎侧真相源时，运营改配置必须改仓库再重启，且两处已经出现漂移。现在平台三张表都已能承载这些数据，本地链路应改为从平台取数，取完删除本地文件。

## What Changes

- **BREAKING** 删除 `engines/ae_harness/knowledge/config/models.yaml`。向量模型改由平台模型配置登记：`model_kind` 增加 `embedding`，并增加 `dimensions`。知识库建索引、检索、评测一律使用平台指定的这条向量模型，由调用方把连接参数传给引擎，引擎不读库。
- **BREAKING** 删除 `engines/ae_harness/knowledge/config/knowledge_bases.yaml`。库登记继续以 `ks_modules` 为真相源；检索参数（`top_k`、相似度阈值、切块大小、切块重叠）与「使用哪条向量模型」收成知识库模块的一份全局配置，不再从引擎 yaml 的 `defaults` 复制。
- **BREAKING** 删除 `engines/ae_harness/agents/config/log_keywords/` 与 `load_log_keywords`。型号日志关键词以平台 `sl_log_keywords` 为唯一真相源；该本地目录无生产调用方。
- 知识库命令行探针不再隐式读自带 yaml，必须由调用方显式传入向量模型与库列表。
- Agent 配置与评测触发只允许选择 `chat` 模型；`embedding` 不得用于创建角色。

## 关联文档

无独立 PRD 编号。本变更是配置真相源收敛：需求由运营直接提出（知识库模型进平台模型配置、库目录走知识库模块、日志关键词走串口日志表），无新增产品需求文档。

## Capabilities

### New Capabilities

- `knowledge-retrieval-settings`: 知识库模块的一份全局检索配置——向量模型引用、默认返回条数、相似度阈值、切块参数，以及改切块后索引失效。

### Modified Capabilities

- `harness-knowledge`: 取消「必须自带 `models.yaml` 与 `knowledge_bases.yaml`」。向量模型与库目录改为由调用方传入；引擎仍只接受向量模型参数，且不反向依赖平台。
- `agent-model-catalog`: 嵌入模型不再由知识库自带配置文件创建，改为由调用方传入的向量模型参数创建；聊天创建层仍不得创建嵌入模型。
- `knowledge-search-entry`: 检索、建索引、评测改用平台检索配置与平台向量模型；首次部署不再依赖引擎自带库目录文件。
- `ops-model-config`: 模型类型增加「向量」；该类型只支持 dashscope，必须填写向量维度，且不得绑定 Agent 配置。

## Impact

- 后端：`backend/apps/ai_assistant/`（模型配置字段与校验）、`backend/apps/knowledge_search/`（检索配置、派生 yaml、检索桥、评测）、`backend/apps/serial_log/` 不改表，只作为关键词唯一来源被确认。
- 引擎：`engines/ae_harness/knowledge/`（`config.py`、`models.py`、探针）、`engines/ae_harness/agents/config.py` 与 `config/log_keywords/`。
- 规则文档：`.agents/docs/engines/ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md` 红线 4、`.agents/docs/engines/ae_harness_agents/ae_harness_agents_agent_creation.md` 的日志关键词职责。这两处是红线文本，须随本变更同一提交更新。
- 前端：运营模型配置页增加「向量」类型与维度；知识库模块页增加检索配置。
- 测试：知识库配置/检索单测、知识库模块集成测、模型配置 API、`test_agents_config.py`。
