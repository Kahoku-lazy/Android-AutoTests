## Context

动机见 proposal.md - Why。方案需要的现状与约束：

- 依赖 change `add-knowledge-search-entry`：模块登记（ks_modules）、检索桥（每请求 KnowledgeRetriever、多选合并、三态）、用量出口（usage_events）、知识页分栏台。
- Recall@k / MRR 是监督指标，必须有「查询 → 正确文档」标注集；零标注只能算裁判类精确率指标。业界通行合成路线：LlamaIndex `generate_question_context_pairs` + `RetrieverEvaluator`（hit_rate / MRR）、RAGAS TestsetGenerator + IR 指标层。本设计自建轻量实现，不引入 ragas / llama-index 依赖。
- agentscope 2.0.9（本机已核实）：`ChatUsage` 含 input_tokens / output_tokens / cache 字段，与 `usage_ledger.record_usage` 入参对齐；`KnowledgeBase.list_documents()` 返回 DocumentSummary（document_id / source / metadata.relative_path），是公开只读 API；`TextParser` / `ApproxTokenChunker` 与索引器用的是同一套原语。
- knowledge 红线：模块内禁止聊天模型、禁止生成、资料目录只读——评测逻辑必须放后端。
- 运营模型配置：`ai_assistant.AIModelConfig`（provider / api_key_env / model_name / base_url / model_kind），端点 `GET /api/ai/model-configs/`（前端 ops-console 已在用）；chat 模型经 `engines.ae_harness.agents.create_model` 原语创建（backend→engines 先例）。
- 后台执行先例：`assistant_threads.queue_turn`（threading.Thread + asyncio.run，pytest 下不起线程）。
- 旧评测中心退役约束：`/api/evaluator/*`、`ev_*` 表、AI 助手侧栏入口保持下线（evaluator-retirement delta 已澄清边界）。

## Goals / Non-Goals

**Goals:**

- 一键产出可审计的 Recall@1/3/5、MRR、误命中率报告，含逐题明细与合成集偏差标注。
- 评测全链路（出题 chat + 检索嵌入）token 逐调用入账。
- 评测与检索入口故障隔离：评测失败不影响提问。

**Non-Goals:**

- 不做人工金标集审核流、LLM 裁判 Precision/nDCG、阈值扫描、历史版本对比、运行中取消（P1）。
- 不改 engines（knowledge 零改动；create_model 用现成原语）。
- 不引入新评测框架依赖；不改价目表与计费公式。
- 不做块级 gold（v1 文档级；块级需要与索引 document_id 方案更深对齐，列 P1）。

## Decisions

### D1 合成评测集：采样 → 出题 → 负样本

`eval_corpus.py` 只读扫描模块 data_dir，用与索引相同的 TextParser / ApproxTokenChunker（参数取自 load_config）切块；带种子的 RNG 均匀跨文档采样（种子随运行落库，可复现）。`eval_generation.py` 经 create_model 批量出题（每批约 5 块，JSON 输出：每块一题），提示词约束：口语化 / 换述 / 不抄原文 / 仅凭该块可答；负样本给模型模块描述与文档标题样本，要求生成语料范围外的问题。解析失败的条目跳过并计数；有效正题不足 5 条时运行失败并给可读原因。

- 为什么文档级 gold：块级 gold 依赖索引内部 document_id 生成方案，文档级稳健且标注含义清晰（"该问题的答案在这个文件里"）。
- 备选「人工金标集」：最诚实但要人力，v1 冷启动不可行；P1 以"合成题人工审核升级金标"合流。
- 备选「仅 LLM 裁判」：算不了真 Recall，只能作 P1 补充。

### D2 gold 匹配：document_id，经公开 list_documents 建映射

评测服务用 knowledge 公开模块（store.SQLiteVectorStore + models.create_embedding_model）绑一个 agentscope KnowledgeBase 句柄，调 `list_documents()` 建「relative_path / filename → document_id」映射；命中匹配一律用 KnowledgeHit.document_id。

- 为什么：不同子目录同名文件会让 filename 匹配误判；list_documents 是公开只读 API，不复制索引内部 sha1 方案、不直读 SQLite 表。
- 备选「按 source 文件名匹配 + 采样时跳过同名文件」：削弱语料覆盖，弃。

### D3 评分：纯函数 + 手算对拍

`eval_metrics.py` 零依赖纯函数：Recall@k（单 gold 文档即 hit@k 比例）、MRR（首条 gold 命中排名倒数均值，无命中记 0）、误命中率（负样本有过阈值命中比例）。检索用 top_k=5（覆盖 Recall@5），阈值取配置。单测用手算 fixture 对拍。报告必带 n 与「合成评测集，结果偏乐观」标注。

### D4 运行器：后台线程 + 状态轮询 + 快照冻结

`eval_runner.py` 照 assistant queue_turn 模式（pytest 下不起线程）；触发时冻结快照（模块 name/data_dir/description + 检索参数 + 模型连接参数 + 题量 + 种子），运行期间模块变更不影响该运行。状态 pending→running→done/failed，进度按已完成题数经 api.py 落库；每模块同时只允许一个运行中（触发时 409）。模型下拉默认取列表第一条 chat 类配置（假设已记录：需求方未指定默认模型，弹窗可改，运行快照记录实际所用模型）。

- 备选「同步请求」：出题 + 逐题检索要几分钟，必超时，弃。
- v1 不做取消：题量有上限（≤100），运行有界；取消列 P1。

### D5 入账：chat 与嵌入逐调用，source=knowledge_eval

chat：每次模型调用读 ChatResponse.usage → `usage_ledger.api.record_usage`（category=LLM，event_id=`knowledge_eval:{run_id}:{seq}`）。嵌入：运行结束取 retriever.usage_events() → change 1 的 `record_embedding_usages(events, execution_id=run_id, source="knowledge_eval")`。入账失败只记日志。

### D6 成本预估：启发式，显著标注"预估"

触发前按「采样块数 × 平均块 token × 出题开销系数 + 题量 × 查询 token」估算输入/输出 token，按价目表折人民币展示；标注为预估，实际以账本为准。不引入精确 tokenizer 依赖。

### D7 前端：右栏模块私有 chip「提问 / 自动评测」

照 SerialLogTabs 先例（模块私有手稿 chip，不用共享 AppTabs）：评测 tab 内含触发弹窗（超管，模型下拉复用 `GET /ai/model-configs/` 过滤 model_kind=chat、题量输入、预估成本）+ 运行列表 + 报告（KpiCard 指标卡 + AppTable 逐题明细 + 合成集标注）。`useEvalRun` composable 轮询（2s，终态停，卸载清理）。三态共享件；非超管只见报告。

**过程可视化（2026-11-18 追加）**：运行表增 `phase` 字段（indexing/generating/retrieving，运行器经 api 打标），前端据此显示等待文案与进度条；逐题明细在运行中即实时渲染（轮询详情已带 queries）；点击行展开该题的来源片段与检索命中原文（复用 HitCard）；报告区内置「评测原理与判断依据」说明（合成集生成 / gold 定义 / rank 与三指标口径 / 合成偏差读法）。

### D8 端点与边界

`POST /api/knowledge-search/evaluations/`（超管）、`GET /api/knowledge-search/evaluations/`（登录，按模块过滤）、`GET /api/knowledge-search/evaluations/{id}/`（登录，进度 + 报告）。表 `ks_eval_runs` / `ks_eval_queries`。不注册 `/api/evaluator/*`、不建 `ev_*` 表、不加 AI 助手侧栏入口（evaluator-retirement delta 守护）。

## 模块防火墙自检

- 跨 App import：只读 `ai_assistant.AIModelConfig` Model（规则允许的跨 App 读）；不 import 任何其它 App 的 service/runner/views。
- 所有 INSERT/UPDATE/DELETE 收敛：`ks_eval_*` → `knowledge_search/api.py`；`ai_usage_records` → `usage_ledger/api.py`。View 只分发。
- 前端不直连数据库；模型下拉走后端既有端点；仪表盘不动。
- 新跨模块依赖清单：① knowledge_search → ai_assistant.AIModelConfig（只读 Model）；② knowledge_search → usage_ledger.api（写路径合规）；③ knowledge_search → engines.ae_harness.agents.create_model 与 knowledge 公开模块（backend→engines 注入方向，先例见 change 1 D3）。无 engines 反向依赖。
- engines 红线：评测不进 knowledge（聊天模型与生成都在后端）；不新增自定义异常类；不造 Agent（create_model 是模型原语，非角色创建）；资料目录只读。

## Risks / Trade-offs

- [合成题与原文词汇相近 → 指标偏乐观] → 提示词强制换述/口语化、报告显著标注、P1 人工审核升级金标集；指标用于纵向对比（同集改阈值/切块）而非绝对达标线。
- [出题质量依赖所选 chat 模型] → 模型显式选择 + 运行快照记录模型；解析失败跳过计数、有效题不足则失败给原因。
- [运行数分钟占后台线程] → 题量上限 100 + 进度轮询；v1 无取消（有界运行），P1 补取消。
- [评测花钱失控] → 题量上限 + 触发前预估成本 + 逐调用入账可审计。
- [同名文件 gold 误判] → document_id 匹配（D2）。
- [运行中模块被改/删] → 触发时快照冻结（D4）。
- [嵌入密钥缺失] → 运行失败给可读原因，不影响检索入口。
- [小样本波动] → 报告带 n；同种子可复现；P1 加置信区间与历史对比。

## Migration Plan

1. 前置：change `add-knowledge-search-entry` 已 apply（检索桥 / 用量出口 / 知识页就绪）。
2. backend：ks_eval_* 迁移 → 评测服务（采样/出题/评分/运行器）→ 端点注册。
3. frontend：评测 tab + 弹窗 + 报告组件 + 轮询 composable；lint:styles + vue-tsc + build。
4. 验证：`python run.py check`；`pytest -c tests/pytest.ini tests/knowledge_search -q`；手工演练（选模型→触发→看进度→读报告→账本核对 LLM 与 Embedding 行）。
5. 回退：删除评测端点 / 表 / 前端组件；检索入口不受影响；账本历史行保留。

## Open Questions

（无。默认模型取第一条 chat 配置已作为假设记录在 D4，弹窗可改，不影响 specs 与任务拆分。）