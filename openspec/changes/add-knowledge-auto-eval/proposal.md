## Why

知识库检索入口（change `add-knowledge-search-entry`）落地后，准确率与召回率仍然没有量化数据，而 `knowledge/AGENTS.md` 明确「评测达标前不接回 Agent」。需求方要求在知识页勾选模块后一键「自动评测」，产出 Recall@k / MRR 等指标，作为阈值与切块调优、以及将来接回 Agent 的门槛依据。Recall/MRR 是监督指标，必须有「查询 → 正确文档」标注集；v1 采用业界通行的**合成评测集**路线（LLM 从语料出题，来源文档即正确答案，参照 LlamaIndex `generate_question_context_pairs` 与 RAGAS TestsetGenerator 的思路，自建轻量实现、不引入重依赖）。

## What Changes

- backend `knowledge_search` App 新增评测域：只读采样语料切块 → chat 模型生成正题（gold=来源文档，文档级）与负样本 → 经检索桥逐题检索 → 纯函数评分（Recall@1/3/5、MRR、误命中率）→ 报告落库。
- 新表 `ks_eval_runs` / `ks_eval_queries`（独立于旧评测中心 `ev_*` 表）；后台线程 + 状态轮询（照 assistant 对话模式）；每模块同时只允许一个运行中评测；题量默认 30 正题 + 10 负样本，上限 100；运行前显示预估 token 成本。
- 评测触发仅超管；报告登录可读；出题 chat 模型从运营「模型配置」（`AIModelConfig`，model_kind=chat，端点 `/api/ai/model-configs/`）中选择，经 `create_model` 原语创建，**不造 Agent**。
- 评测用量入账：chat token（LLM）与嵌入 token（Embedding）逐调用经 `usage_ledger.api` 写入，source=knowledge_eval，入账失败不阻断评测。
- frontend `knowledge-search` 页新增「自动评测」区：超管触发弹窗（模型下拉 + 题量）、进度轮询、报告展示（指标卡 + 逐题明细表 + 「合成评测集，结果偏乐观」显著标注）。
- 边界声明：这是知识页内嵌检索评测，**不是复活旧「评测中心」**——`/api/evaluator/*`、`ev_*` 表、AI 助手侧栏评测入口保持下线；`evaluator-retirement` spec 增加范围澄清。
- v1 明确不做（P1）：人工金标集审核流、LLM 裁判 Precision@k / nDCG、阈值扫描曲线、评测历史版本对比、运行中取消。
- 依赖：change `add-knowledge-search-entry` 先行（模块登记、检索桥、用量出口、知识页）。

## 关联文档

PRD-08（知识库能力条款）；自动评测为需求方 2026-11-18 对话确认的新增需求，PRD 条目在 apply 阶段补写。评测门槛口径出自 `engines/ae_harness/knowledge/AGENTS.md`「当前状态」段（Recall@k / MRR / 误命中率）。

## Capabilities

### New Capabilities

- `knowledge-auto-eval`: 知识库检索自动评测——合成评测集生成、Recall@k / MRR / 误命中率评分、评测运行生命周期与权限、报告展示、评测用量入账。

### Modified Capabilities

- `evaluator-retirement`: 「Evaluator product surface is gone」澄清退役范围为旧评测中心（题库 / 运行 / 框架 / KB 自测、`/api/evaluator/*`、`ev_*` 表、AI 助手侧栏入口），不禁止知识页内嵌的检索评测（`knowledge-auto-eval`）。

## Impact

- backend：`apps/knowledge_search` 新增评测 models / api / 服务（采样、出题、评分、运行器）/ views / urls（`/api/knowledge-search/evaluations/*`）；跨 App 只读 `ai_assistant.AIModelConfig` Model（规则允许）；chat 模型经 `engines.ae_harness.agents.create_model`（backend→engines 先例）。
- engines：**零改动**——评测不进 knowledge 模块（其红线禁止聊天模型与生成）；检索与用量出口复用 change 1 成果。
- frontend：`modules/knowledge-search` 新增评测区组件与 composable；模型下拉复用 `GET /ai/model-configs/`（只读）。
- 测试：`tests/knowledge_search/{unit,integration,api}` 评测场景（评分纯函数手算对拍、出题 mock、生命周期、权限、入账）。
- 计费：`ai_usage_records` 新增 source=knowledge_eval 行（LLM + Embedding）；价目表与公式零改动。
- 回退：删除评测表 / 端点 / 前端组件即可，检索入口不受影响；账本历史行保留。