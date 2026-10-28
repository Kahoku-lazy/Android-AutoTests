## Why

知识库助手 Pipeline 的 `deepseek-flash` 目前完全自由回答，无法利用 `D:\Govee\data\rag_data` 中的产品资料。需要把这些 Markdown 建成本地 RAG 索引，在每轮语音提问时检索相关片段并注入 DeepSeek 的上下文，让回答有资料依据。

## What Changes

- 新增 `engines/agents/rag/`：RAG 配置、文档解析/切块、SQLite 向量库、AgentScope `KnowledgeBase` 封装。
- 索引 `D:\Govee\data\rag_data` 下的 `.md/.txt`；索引文件存本地 `data/rag_index/`，按文件 mtime/size 增量重建。
- 嵌入使用 `text-embedding-v4`（`DASHSCOPE_API_KEY`，1024 维）；检索默认 top_k=4、余弦相似度阈值。
- Pipeline 的 `DeepSeekAnswerer` 在每轮提问前检索资料，把命中片段作为上下文注入；没有命中时仍正常回答。
- RAG 失败/索引不可用时降级为原有自由对话，不阻塞语音会话。
- 说明：本期 RAG 只接 Pipeline 的 DeepSeek LLM；Omni 直连实时模型不经过文本 LLM，暂不注入检索结果。

## 关联文档

- AgentScope 2.0.10 RAG 教程：https://docs.agentscope.io/zh/versions/2.0.10/building-blocks/rag
- 已归档 `2026-10-28-add-pipeline-voice-mode`
- 数据目录：`D:\Govee\data\rag_data`

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `knowledge-assistant-voice`: 新增「Pipeline LLM 的 RAG 增强」需求。

## Impact

- 引擎：新增 `engines/agents/rag/`；`pipeline_llm.py` 注入检索上下文；`pipeline.py` 创建 RAG 服务。
- 后端：无新接口；WS 链路不变。
- 配置：`.env.example` 增加 RAG 开关、数据目录、索引目录、top_k/阈值。
- 依赖：不新增第三方包（SQLite + 已安装 AgentScope/numpy）。
- 测试：向量库单测、RAG 检索真实数据、Pipeline 回答验证。
