## 1. 规则先行

- [x] 1.1 改 `engines/ae_harness/AGENTS.md`：第 11 条放开只读知识库检索，目录结构与职责表增 `knowledge/`，第 1 条与第 6 条同步收窄。验证：`git diff -- engines/ae_harness/AGENTS.md`
- [x] 1.2 改 `engines/ae_harness/agents/AGENTS.md`：第 3 条收窄到 `agents/config/models.yaml` 与 `prompts/`；第 6 条放开检索工具挂载。验证：`git diff`
- [x] 1.3 改 `engines/ae_harness/tools/AGENTS.md`：新增目录准入——只允许 Python 内置函数工具、Skill、MCP。验证：`git diff`

## 2. 配置与嵌入模型

- [x] 2.1 新增 `knowledge/config/models.yaml`（只放向量模型）与 `knowledge/config/knowledge_bases.yaml`（defaults + 库目录）。验证：`python -c "from engines.ae_harness.knowledge.config import load_config; print(load_config())"`
- [x] 2.2 `knowledge/models.py` 按配置造 `DashScopeEmbeddingModel` 并交出密钥环境变量名，密钥经 `.env` → 进程环境取值。验证：缺密钥时报可读错误，不打印密钥

## 3. 索引与检索

- [x] 3.1 `knowledge/store.py` 实现 `VectorStoreBase`（SQLite，余弦相似度，支持 `metadata_filter`）。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_store.py -q`
- [x] 3.2 `knowledge/indexer.py` 按库增量索引 `.md/.txt`，未变化文件跳过，删除的文件清理，切块版本变化重建。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_index.py -q`
- [x] 3.3 `knowledge/service.py` 提供 `retrieve(base, query, top_k)`，返回结构化命中；库不可用返回空列表与可读原因，不抛异常。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_retrieve.py -q`

## 4. 工具与探针

- [x] 4.1 `knowledge/tool.py` 产出只读 `search_knowledge` 工具，返回 JSON（成功带 hits，失败带 error，无命中单独文案）。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_tool.py -q`
- [x] 4.2 `knowledge/probe.py` 提供 `index` / `retrieve` 命令行，不创建智能体、不调用聊天模型。验证：`python -m engines.ae_harness.knowledge retrieve product_manuals "指示灯"`

## 5. 不挂载与删除安全

- [x] 5.1 本期**不挂载**：执行者入口保持原样，Harness 其它模块对知识库零引用。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_independence.py -q`
- [x] 5.2 `.gitignore` 增加 `engines/ae_harness/knowledge/index/`。验证：`git status` 不出现索引文件
- [x] 5.3 删除演练：整目录移走后三个入口仍可导入。验证：临时移走 `knowledge/` 后 `python -c "import engines.ae_harness.assistant.agent_executor"`

## 6. 变更自检

- [x] 6.1 跑知识库单测与全套 `engines/ae_harness` 单测。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness -q`
- [x] 6.2 本地门禁全绿（阻塞项 24/24）。验证：`python run.py check`

## 7. 效果评测（未做，是接回 Agent 的前置）

> 现状：只验证了「能不能跑通」（索引成功、命中字段齐全、三种返回文案正确），**没有测准确率与召回率**。因此本期不挂载。

- 【已取消 · 未做取消】7.1 建评测集：对 `product_manuals` 写 30~50 条「问题 → 正确文档 + 正确小节」的人工标注，覆盖按键、指示灯、固件、恢复出厂四类。
- 【已取消 · 未做取消】7.2 指标：Recall@k（k=1/3/5）、MRR、无答案问题的误命中率（用无关问题测「该说没有」）。
- 【已取消 · 未做取消】7.3 基线对比：`ApproxTokenChunker` vs 标题切块；阈值 0.35/0.40/0.45/0.50 分档；`top_k` 3/4/6。
- 【已取消 · 未做取消】7.4 只在指标达标后，才把 `build_knowledge_tools()` 挂回角色入口，并记录评测报告路径。
