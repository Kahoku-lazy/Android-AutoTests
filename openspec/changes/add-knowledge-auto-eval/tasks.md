## 1. backend 评测数据面

- [x] 1.1 `knowledge_search` 新增评测 models（ks_eval_runs：模块快照/模型快照/题量/种子/状态/进度/预估成本/失败原因；ks_eval_queries：问题/gold 文档编号/正负类型/来源块/命中与排名/结果）+ api.py 唯一写点 + 迁移；验证 `python manage.py check` + `makemigrations --check` + 表单测
- [x] 1.2 评测列表/详情/触发的 serializer 与权限（触发超管、读登录）；验证 tests/knowledge_search/unit 权限与快照冻结用例

## 2. backend 评测服务

- [x] 2.1 `eval_corpus.py`：只读扫描 data_dir，用与索引相同的 TextParser/ApproxTokenChunker 切块，带种子均匀跨文档采样；经 knowledge 公开模块绑 KnowledgeBase 句柄调 list_documents 建 filename/relative_path→document_id 映射；验证单测（临时目录 fixture：采样可复现、同名文件映射正确、资料目录零写入）
- [x] 2.2 `eval_generation.py`：create_model 按运营模型配置批量出题（JSON 输出、换述/口语化约束）+ 负样本生成；解析失败跳过计数、有效正题 <5 失败；chat usage 逐调用经 usage_ledger.api 入账（source=knowledge_eval）；验证单测（mock 模型：出题解析、负样本、失败路径、入账幂等）
- [x] 2.3 `eval_metrics.py`：Recall@1/3/5、MRR、误命中率纯函数（document_id 匹配）；验证单测手算 fixture 对拍 + 同名文件不误判用例
- [x] 2.4 `eval_runner.py`：后台线程 + asyncio.run（pytest 不起线程）、快照冻结、每模块单运行（409）、进度经 api.py 落库、逐题检索 top_k=5、结束取 usage_events 入账、失败记可读原因；验证集成测试（mock 检索桥与模型：生命周期、进度、失败隔离、入账失败不阻断）

## 3. backend HTTP 面

- [x] 3.1 views/urls：POST evaluations/（超管，题量上限 100 校验、预估成本返回）、GET evaluations/（登录，按模块过滤）、GET evaluations/{id}/（登录，进度+报告）；验证 `pytest -c tests/pytest.ini tests/knowledge_search/api -q` + `python manage.py spectacular --validate` + arch 契约守护通过

## 4. frontend 评测区

- [x] 4.1 右栏模块私有 chip「提问 / 自动评测」（照 SerialLogTabs 先例）+ api.ts 评测端点与模型列表（GET /ai/model-configs/ 过滤 chat）；验证 vue-tsc + arch 路径 resolve 断言
- [x] 4.2 触发弹窗（超管）：模型下拉、题量输入（默认 30+10、上限 100）、预估成本展示；验证 lint:styles + vue-tsc
- [x] 4.3 `useEvalRun` composable：2s 轮询、终态停、卸载清理；运行列表与进度条；验证 vue-tsc + 单测（frontend 测试 runner 按仓库现状 placement）
- [x] 4.4 报告组件：KpiCard 指标卡（Recall@1/3/5、MRR、误命中率）+ AppTable 逐题明细 + 「合成评测集，结果偏乐观」标注 + 三态共享件（加载期不渲染空态）；非超管只见报告；验证 lint:styles + vue-tsc + 新 .vue ≤500 行 + `npm run build`

## 5. 测试、文档与门禁

- [x] 5.1 补齐 tests/knowledge_search 评测场景对照 spec（超限 400、重复触发 409、非超管 403、运行中改模块不影响、失败不拖垮检索、两类用量入账）；验证 `pytest -c tests/pytest.ini -m "unit or integration"` 相关路径全绿 + api 套件通过
- [x] 5.2 PRD 条目补写（自动评测，编号沿用体例，注明 2026-11-18 需求方确认）；验证人工审阅与 proposal 关联文档一致
- [ ] 5.3 全链路人工验收：选模型→触发→进度→报告→账本核对 LLM 与 Embedding 行→改阈值重跑对比；验证 `python run.py check` 退出码 0 + `python utils/gen_arch_stats.py --check-boundaries` 通过
- [ ] 5.4 按 Conventional Commits 分提交（backend / frontend / docs 逐文件暂存，禁 git add -A），推送 Kahoku；验证 ci-phase1.yml 6 个 job 全绿