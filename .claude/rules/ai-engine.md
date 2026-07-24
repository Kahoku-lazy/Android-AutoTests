# AI Engine Rules — Android-AutoTests

## 关键约束

| 规则 | 说明 |
|------|------|
| Anthropic/Custom 走 OpenAI 协议 | 通过 `base_url` 区分 |
| 写 Tool 必须走 Django `api.py` | 禁止 Tool 内直接 ORM 写入 |
| 读 Tool 设 `is_read_only=True` | 框架借此判断是否需要用户确认 |
| `run_sync()` 异步桥接 | 封装 `sync_to_async`，8s 超时 |
| AgentScope 依赖 Redis | Redis 不可用时 AgentScope 无法启动 |

## 新增 Tool

在 `agentscope_service/tools/{domain}_tools.py` 创建 `ToolBase` 子类 → 在 `factory.py` 注册。必须定义 `name` `description` `input_schema`，返回值用 `ToolChunk`。

## Agent Team

5 个预设角色模板在 `agentscope_service/teams/`：element-inspector / case-writer / device-operator / test-executor / report-writer。

## 鉴权

AgentScope 默认 `X-User-ID` → 替换为 JWT Bearer（与 Django 共享 `SECRET_KEY`）。见 `agentscope_service/app.py` `dependency_overrides`。

## RAG

ChromaDB PersistentClient，`data/chromadb/`，collection `project_knowledge`，32 篇文档。初始化：`python agentscope_service/rag/init_kb.py`。
