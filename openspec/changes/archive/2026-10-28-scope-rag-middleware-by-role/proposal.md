## Why

上一个变更（`2026-10-28-add-agent-middleware-suite`）把 RAG 做成中间件后，开关是全局环境变量：一旦打开，**所有**角色都会去检索 `data/rag_index` 里的产品资料。但那份索引是给知识库／语音助手准备的——SOP 的执行者、验收者拿着「某产品参数」的片段去点手机，只会被无关资料带偏，还白花一次向量检索。

要求：**RAG 中间件默认关，只对知识类／语音类角色开**。

## What Changes

- `engines/agents/middleware/assembly.py`：`build_agent_middlewares()` 增加 `with_rag: bool = False` 参数；只有显式传 True 时才尝试装配 RAG（且仍需 `AGENT_RAG_ENABLED` 与索引可用）。
- `engines/agents/role/base.py` 保持默认（不传）→ SOP 角色天然不装 RAG。
- 知识／语音类角色今后自建 Agent 时传 `with_rag=True`；本次不改语音链路本身（仍走 pipeline，见下一条变更）。
- 测试补两条：声明为知识类时才会出现 `RagContextMiddleware`；未声明时即便 `AGENT_RAG_ENABLED=1` 也不装。

## 关联文档

- `openspec/specs/agent-middleware-assembly/spec.md`：RAG 那条要求补「按角色声明」。
- `engines/agents/rag/AGENTS.md`：失败降级、只读资料目录两条不变。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-middleware-assembly`：RAG 注入从「全局开关」收敛为「角色声明 + 全局开关」双条件。

## Impact

- 修改：`engines/agents/middleware/assembly.py`、对应测试
- 行为：SOP 类角色在任何配置下都不会装 RAG；只有显式声明的角色会
- 不影响：RAG 自身的检索逻辑、索引构建、语音 pipeline 现有链路
