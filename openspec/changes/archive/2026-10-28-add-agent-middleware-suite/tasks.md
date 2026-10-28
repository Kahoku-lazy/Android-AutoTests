## 1. 现状与取舍

- [x] 1.1 复核框架能力：`TracingMiddleware`（`on_reply` / `on_model_call` / `on_acting` 三层 span，未配 `TracerProvider` 时短路）、`ReplyBudgetControlMiddleware`（单 reply 加权 token）、`TTSMiddleware`（`TTSModelBase`）、`RAGMiddleware`（需要预先构造好的 `KnowledgeBase` 列表）、`AgenticMemoryMiddleware` / `Mem0Middleware`（需外部存储）
- [x] 1.2 判定 RAG 走自研适配而不是框架 `RAGMiddleware`：我们的 `RagService` 是**懒建索引**（`ensure_index()` 异步、首次检索才建），框架 `RAGMiddleware` 构造时就要拿到可用 `KnowledgeBase`；`BaseRole.__init__` 是同步的，强行等待索引会把网络 IO 挪进角色构造。因此写 `RagContextMiddleware` 复用同一个 `RagService`，检索结果按用户消息缓存
- [x] 1.3 判定语音与长期记忆的落地边界：语音用框架 `TTSMiddleware` + `DashScopeTTSModel`，默认关闭（当前没有任何 Agent 产出语音，pipeline 走自研 TTS）；长期记忆只留 `build_memory_middleware()` 入口，恒返回 None
- [x] 1.4 固定顺序写入 `assembly.py` 文档：追踪最外（预算触发的收尾也在同一棵 span 里）、重试最内（只重发那次模型调用）

## 2. 实现

- [x] 2.1 `engines/agents/middleware/envs.py`：`env_flag` / `env_int` / `env_float`
- [x] 2.2 `tracing.py`：`setup_tracing()` 进程内注册一次 `TracerProvider` + `BatchSpanProcessor(OTLPSpanExporter)`；`build_tracing_middleware()` 仅在配了 `AGENT_TRACING_OTLP_ENDPOINT` 时装配，缺依赖只记警告
- [x] 2.3 `budget.py`：`ReplyBudgetControlMiddleware`，默认 60 万加权 token（输入 1 / 输出 2；按「失控护栏」取值——执行者一轮最多 60 次 ReAct，20 万会误杀正常长步骤），`AGENT_REPLY_TOKEN_BUDGET=0` 关闭
- [x] 2.4 `rag_context.py`：`RagContextMiddleware.on_system_prompt` 取最后一条用户消息检索、同一 query 只检索一次、命中片段按 `## 参考资料` 追加、异常与无命中原样返回；`build_rag_middleware()` 需 `AGENT_RAG_ENABLED` 且 rag 索引启用
- [x] 2.5 `memory.py`：入口函数恒返回 None；配了 `AGENT_MEMORY_BACKEND` 只记警告，不引入 mem0 依赖
- [x] 2.6 `tts.py`：`TTSMiddleware(DashScopeTTSModel(...))`，需 `AGENT_TTS_MIDDLEWARE=1` 且 `DASHSCOPE_API_KEY`
- [x] 2.7 `assembly.py`：`build_agent_middlewares(fallback_model=...)`，单项用 `_safe()` 包裹，配置非法只跳过该项
- [x] 2.8 `engines/agents/role/base.py`：`_middlewares()` 改为调用装配入口，保留备用模型构造
- [x] 2.9 `.env.example` 增「其余引擎中间件」段（追踪 / 预算 / RAG / 语音 / 记忆入口共 12 个变量）

## 3. 验证

- [x] 3.1 `tests/graybox/unit/test_agent_middleware_assembly.py`（18 例）：默认集合（预算 + 重试）、顺序（追踪 → 预算 → 语音 → 重试）、各开关、预算参数解析、RAG 注入/缓存/无命中/异常降级/无用户消息、记忆入口恒 None
- [x] 3.2 `test_model_retry_middleware.py` 两条装配用例改为检查 `role._middlewares()` 全量列表，并断言 `Agent` 的模型调用链里只有重试（预算不实现 `on_model_call`）
- [x] 3.3 真 Agent 冒烟（`temps/probe_assembly_reply.py`）：`middlewares: ['ReplyBudgetControlMiddleware', 'ModelRetryMiddleware']`，一次 `reply` 正常返回 `done`
- [x] 3.4 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_agent_middleware_assembly.py tests/graybox/unit/test_model_retry_middleware.py -q` → **52 passed**
- [x] 3.5 `ruff format --check` / `ruff check` 对 `engines/agents/middleware`、`role/base.py`、两个测试文件 → 通过
- [x] 3.6 `python run.py check` → 与本次相关项全 PASS（django-check / ruff-lint / pytest-collect / ruff-engines-format / ruff-engines-lint / boundary / vue-tsc / vitest / vite-build）；5 项 FAIL 仍是那条在途改动：`backend/apps/task_list/event_store.py` 与 `backend/apps/usage_ledger/{api,pricing}.py` 未格式化（`ruff format --check` 仅剩这 3 个文件）、openapi 两条（knowledge_assistant 新路径未登记）、prettier 两条（`frontend/src/modules/knowledge-assistant/**`）
- [x] 3.7 `npx openspec validate add-agent-middleware-suite --strict` 通过
