## Context

见 proposal.md 的 Why。现状与本设计相关的约束：

- `ai_model_configs.model_kind` 只有 `chat / tts / realtime`，没有向量维度字段。运营页下拉与序列化器同步只有这三项。
- 知识库检索桥 `retrieval.py` 先由 `registry.sync_yaml()` 把 `ks_modules` 派生为 `logs/knowledge_search/knowledge_bases.yaml`，其 `defaults` 段每次从引擎 `knowledge_bases.yaml` 只读复制，再交给 `load_config(bases_path=…)`。向量模型仍由引擎 `models.yaml` 按短名 `dashscope_embedding_v4` 解析。
- 引擎 `load_config` 同时承担「读文件」与「校验」。`EmbeddingModelSpec` 用 `extra="forbid"`，只收 `provider / api_key / model_name / dimensions`，且 provider 与密钥名都锁死 dashscope。
- `engines/` 禁止 import `apps.*` 与 `django.*`。平台到引擎的方向只能是调用方把参数传进去。
- `sl_log_keywords` 已是关键词真相源。`load_log_keywords` 只被 `tests/engines/ae_harness/unit/test_agents_config.py` 调用，无生产调用方。
- 知识库模块内有一个 `enabled: false` 的库，名字也叫 `log_keywords`。它是资料目录占位，与型号关键词 md 不是一回事，本变更不动它。

## Goals / Non-Goals

**Goals:**

- 向量模型、检索参数、库登记、型号关键词四类数据各自只有一个真相源，且都在平台。
- 引擎知识库改为纯函数：收到参数就工作，不读自带 yaml，不连平台库。
- 改切块参数后，旧索引不能再被当成有效结果返回。

**Non-Goals:**

- 不把检索参数拆到每个库。
- 不重做索引存储；索引文件仍在引擎 `knowledge/index/`，失效只记标记，不在保存时删除文件。
- 不改串口日志的表结构、接口与页面。
- 不启用知识库里那个占位的 `log_keywords` 库，也不把它接到验收提示。
- 不改用量公式与价目。

## Decisions

### 1. 向量模型进 `ai_model_configs`，新增两列而不是新表

`model_kind` 增加取值 `embedding`。新增可空整数列 `dimensions`，仅该类型必填且必须为正整数。`embedding` 不要求 `base_url`，不要求 `voice`。

厂商约束沿用现有序列化器的成对校验：本期只允许 `dashscope + DASHSCOPE_API_KEY`，因为引擎 `create_embedding_model` 只实例化 `DashScopeEmbeddingModel`。其它厂商要等引擎有对应实现后再放开，不在本变更假装支持。

数据迁移：表中不存在 `model_name=text-embedding-v4` 且 `api_key_env=DASHSCOPE_API_KEY` 的行时插入一条，`provider=dashscope`、`model_kind=embedding`、`dimensions=1024`、`base_url` 空。已存在则不覆盖运营改过的值。

备选是知识库模块自建一张嵌入模型表。否决：需求明确要求进平台模型配置，两张模型表会回到本次要消除的双份维护。

### 2. 检索参数单独一张单行表，放在 `knowledge_search`

新表 `ks_retrieval_settings`，不加业务主键，读写都走「取唯一一行」。字段：`embedding_model_id`（整数，指向 `ai_model_configs.id`，不建跨 App 外键）、`top_k`、`score_threshold`、`chunk_size`、`chunk_overlap`、`index_epoch`（整数，默认 0）。

不建外键的原因：跨 App 只允许读 Model 与调对方 `api.py`。删除保护放在 `ai_assistant` 的删除函数里，删除前读 `knowledge_search.models.RetrievalSettings` 判断引用；被引用时拒绝。这与现有「被 Agent 配置引用则拒绝删除」同一写法。

种子值必须取引擎 yaml 里调过的数，不取代码默认：`top_k=4`、`score_threshold=0.45`、`chunk_size=400`、`chunk_overlap=60`。代码里的 `DEFAULT_SCORE_THRESHOLD=0.55` 已被注释否决（0.55 会漏掉「缺水提醒」这类短查询）。迁移把 `embedding_model_id` 指到决策 1 插入的那条。

保存时比较新旧 `chunk_size` 与 `chunk_overlap`，任一变化则 `index_epoch += 1`。只改 `top_k`、阈值或模型不增加。

备选是把这四个数加在 `KnowledgeModule` 上。否决：现状是全局一份，多库合并检索用同一个阈值；按库存会在合并时出现两个阈值。

### 3. 引擎改为接收参数，不再读自带 yaml

`load_config` 改为 `build_config(embedding: Mapping, bases: list[Mapping], **检索参数)`，返回不变的 `KnowledgeConfig`。校验规则原样保留：向量模型 `extra="forbid"`、库名正则、启用库目录隔离、检索参数类型。

`create_embedding_model` 签名不变，仍收 `EmbeddingModelSpec`。平台在边界上把模型配置行转成这个 spec：`api_key_env` 映射到 spec 的 `api_key` 字段。

`retrieval.search` 与预建索引不再调用 `registry.sync_yaml()`。同步段读取 `RetrievalSettings` 与勾选模块，组装参数后传入。`registry.py` 的 yaml 派生与 `KNOWLEDGE_SEARCH_BASES_FILE` 一并删除；评测快照改为冻结模块行与检索配置行的 JSON，不再冻结 yaml 文件。

命令行探针 `python -m engines.ae_harness.knowledge` 改为必填参数：模型名、维度、密钥环境变量名、库名、资料目录。缺任一参数即非零退出。不保留「没传就读 yaml」的回退。

### 4. 索引失效用 epoch 比对，不在保存时删文件

索引目录下每个库一个标记文件，内容是建索引时的 `index_epoch`。检索某库前比对：标记缺失或与当前 epoch 不一致，该库返回「检索不可用：切块参数已变更，需重建索引」，不抛异常。预建索引成功后写入当前 epoch。

比对放在平台检索桥，不放进引擎：epoch 是平台概念，引擎保持不知道平台的存在。

### 5. 向量模型不得进入角色

`model_configs.list` 增加按 `model_kind` 过滤的只读参数；Agent 配置页与评测触发只取 `chat`。写路径在 `agent_configs` 校验：提交的 `model_config_id` 不是 `chat` 时拒绝。这是后端权威，前端下拉过滤只是体验。

`embedding` 不进入 `ModelUseGrant` 的主动使用名单语义变更：沿用「新建只进超管名单」，但对话模型列表接口继续只返回 `chat`。向量模型没有对话入口。

### 6. 日志关键词直接删除，不迁移

`H6810.md` 的 15 个关键词是 `sl_log_keywords` 全量的一个子集视图，平台表已覆盖。不写数据迁移，不新增「按型号导出 markdown」接口。删除：

- `engines/ae_harness/agents/config/log_keywords/H6810.md`
- `engines/ae_harness/agents/config.py` 中的 `load_log_keywords` 与 `LOG_KEYWORDS_DIR`；该文件因此为空，整文件删除
- `tests/engines/ae_harness/unit/test_agents_config.py`

同一提交更新 `.agents/docs/engines/ae_harness_agents/ae_harness_agents_agent_creation.md`（目录职责不再提日志关键词）与 `.agents/docs/engines/ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md` 红线 4（改为：向量模型参数由调用方传入，本模块不读配置文件、不读平台库）。`.agents/docs/engines/ae_harness/ae_harness_overview.md` 里点名 `knowledge/config/` 豁免的那句同步收窄。

### 7. 规则文本与代码同一提交

本变更修改三处 AGENTS 红线与一条 OpenSpec 主规格（归档时合入）。不新增自定义异常，不改变 `engines → apps` 的依赖方向，不改计费口径。因此不单列变更申请；红线文本的改动范围以本设计决策 6 列出的句子为界，不得顺手改其它条款。

## 模块防火墙自检

- `knowledge_search` 读 `ai_assistant.models.AIModelConfig`：跨 App 只读 Model，符合现有评测触发的读法。
- 删除模型配置前的引用检查放在 `ai_assistant` 自己的删除函数，只读 `knowledge_search.models.RetrievalSettings`，不 import 对方 service。
- 检索配置的增改只经 `knowledge_search/api.py`；模型配置的增改删仍只经 `ai_assistant/api.py`。
- 引擎不新增任何 `apps.*` / `django.*` import。平台把已校验的普通 dict 传进 `build_config`。
- 前端只走各自模块的 `api.ts`，不直连数据库。

## Risks / Trade-offs

- [改切块后旧索引静默命中] → 检索前比对 `index_epoch`，不一致即返回「检索不可用」并要求重建，不返回旧命中。
- [种子迁移覆盖运营改过的向量模型] → 只在不存在同一密钥与模型名的行时插入，不更新已有行。
- [0.55 与 0.45 取错] → 种子写死 0.45，并在迁移注释里引用「缺水提醒」这条实测原因；单测断言种子值。
- [探针失去零参数可用性] → 接受。探针改为显式参数，文档同步改示例命令。
- [评测运行中改检索配置] → 沿用现有快照：触发时冻结当时的检索配置与模块行，运行中修改不影响该次评测。
- [回滚] → 代码回滚需先恢复三份本地文件；数据库多出的列与表可保留，旧代码不读它们。不提供自动反向迁移删除种子行，避免误删运营后加的向量模型。

## Migration Plan

1. 先扩表：`ai_model_configs.dimensions`、`model_kind` 接受 `embedding`、插入种子向量模型；建 `ks_retrieval_settings` 并写入种子行。
2. 再切读路径：检索桥、预建索引、评测改为读平台配置。此时引擎 yaml 仍在，可用于对照。
3. 最后删文件与派生链路，同一提交更新三份 AGENTS。
4. 部署后既有索引的标记文件不存在，首次检索会要求重建一次。这是预期，不是故障。

## Open Questions

无。检索参数的归属已由需求方确认：放知识库模块的一份全局配置。
