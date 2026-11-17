## 1. 知识库目录与按库索引

- [x] 1.1 新增 `knowledge_bases.yaml` 和目录装载，校验库名、启用状态及资料目录冲突。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_catalog.py -q`
- [x] 1.2 将索引和向量库改为按库 collection 与增量状态工作，并补齐向量库异步上下文。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_store.py tests/engines/agents/unit/test_rag_index.py -q`
- [x] 1.3 提供按库检索的结构化命中，覆盖无命中、禁用库、失败重试和不跨库返回。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_retrieve.py -q`

## 2. 独立探针

- [x] 2.1 增加 `index` 与 `retrieve` 命令行探针，只调用嵌入模型并区分无命中和配置错误。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_probe.py -q`

## 3. 摘掉智能体引用

- [x] 3.1 文字会话和语音会话不再创建 RAG 服务或挂载 `search_knowledge`，语音提示词不再要求先检索。验证：`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_chat_session.py tests/knowledge/unit/test_knowledge_assistant_config.py -q`
- [x] 3.2 中间件装配不再包含系统提示词注入式 RAG。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_agent_middleware_assembly.py -q`

## 4. 变更自检

- [x] 4.1 运行 RAG 与知识库会话相关测试，并检查 engines 注释和风格。验证：`python -m pytest -c tests/pytest.ini tests/engines/agents/unit/test_rag_catalog.py tests/engines/agents/unit/test_rag_store.py tests/engines/agents/unit/test_rag_index.py tests/engines/agents/unit/test_rag_retrieve.py tests/engines/agents/unit/test_rag_probe.py tests/engines/agents/unit/test_agent_middleware_assembly.py tests/knowledge/unit/test_knowledge_chat_session.py -q`

> **2026-11-17 归档**：按需求方决定直接归档，未完成项不再执行；本次 delta 因目标 spec 不存在未合并，delta 原文保留在本目录 specs/ 下。
