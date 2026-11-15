## 1. 规则先行

- [ ] 1.1 改 `engines/ae_harness/AGENTS.md`：第 11 条放开只读知识库检索，目录结构与职责表增 `knowledge/`。验证：`git diff -- engines/ae_harness/AGENTS.md` 只含这两处
- [ ] 1.2 改 `engines/ae_harness/agents/AGENTS.md`：第 3 条收窄到 `agents/config/models.yaml` 与 `prompts/`；第 6 条放开检索工具挂载。验证：`git diff` 只含这两条
- [ ] 1.3 改 `engines/ae_harness/tools/AGENTS.md`：新增目录准入——只允许 Python 内置函数工具、Skill、MCP。验证：`git diff` 只含该条

## 2. 配置与嵌入模型

- [ ] 2.1 新增 `knowledge/config/models.yaml`（只放向量模型）与 `knowledge/config/knowledge_bases.yaml`（defaults + 库目录）。验证：`python -c "from engines.ae_harness.knowledge.config import load_embedding_spec, load_knowledge_bases; print(load_embedding_spec(), load_knowledge_bases())"`
- [ ] 2.2 `knowledge/models.py` 按配置造 `DashScopeEmbeddingModel` 并交出密钥环境变量名，密钥经 `.env` → 进程环境取值。验证：缺密钥时报可读错误，不打印密钥

## 3. 索引与检索

- [ ] 3.1 `knowledge/store.py` 实现 `VectorStoreBase`（SQLite，余弦相似度，支持 `metadata_filter`）。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_store.py -q`
- [ ] 3.2 `knowledge/indexer.py` 按库增量索引 `.md/.txt`，未变化文件跳过，删除的文件清理，切块版本变化重建。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_index.py -q`
- [ ] 3.3 `knowledge/service.py` 提供 `retrieve(base, query, top_k)`，返回结构化命中；库不可用返回空列表与可读原因，不抛异常。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_retrieve.py -q`

## 4. 工具与探针

- [ ] 4.1 `knowledge/tool.py` 产出只读 `search_knowledge` 工具，返回 JSON（成功带 hits，失败带 error，无命中单独文案）。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_knowledge_tool.py -q`
- [ ] 4.2 `knowledge/probe.py` 提供 `index` / `retrieve` 命令行，不创建智能体、不调用聊天模型。验证：`python -m engines.ae_harness.knowledge retrieve product_manuals "指示灯"`

## 5. 入口挂载与删除安全

- [ ] 5.1 `assistant/agent_executor.py` 加局部可选导入与挂载；整目录删除后入口照常运行。验证：临时改名 `knowledge/` 后 `python -m engines.ae_harness.assistant.agent_executor "现在在哪个应用"` 仍可启动
- [ ] 5.2 `.gitignore` 增加 `engines/ae_harness/knowledge/index/`。验证：`git status` 不出现索引文件

## 6. 变更自检

- [ ] 6.1 跑本变更相关单测与探针真机一轮，确认命中可读。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit -q`
- [ ] 6.2 检查注释与风格。验证：`.agents/skills/engines-docstring-check` 与 `.agents/skills/engines-agents-style-check` 均通过
