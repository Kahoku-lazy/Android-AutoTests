## Why

引擎侧现在只有「模型重试与回退」一个中间件（`2026-10-28-add-model-retry-fallback`）。其余四类能力都还散在引擎外或根本没接：一次 reply 花掉多少 token 无人拦、链路耗时只能靠日志时间戳拼、语音助手的检索上下文与语音合成各自写死在 pipeline 里、长期记忆没有入口。AgentScope 2.0 的中间件机制正好覆盖这些点，但**没有一个统一的装配处**——每加一个能力就要改一次 `BaseRole`，顺序也无人负责。

本变更建立**一套装配入口**：`BaseRole` 只调用一次 `build_agent_middlewares()`，由它按环境变量决定装哪些、按固定顺序装。

## What Changes

五个能力，全部按环境变量开关，默认只保留当前已有的「模型重试」（行为不变）：

| 能力 | 实现 | 默认 | 开关 |
|---|---|---|---|
| 链路追踪 | 框架 `TracingMiddleware`（`on_reply` / `on_model_call` / `on_acting` 三层 span） | 关（无 collector 时装了也白装） | `AGENT_TRACING_OTLP_ENDPOINT` |
| 单次 reply 预算 | 框架 `ReplyBudgetControlMiddleware`（累计加权 token，超限注入收尾提示 + 禁止再调工具） | 开，60 万加权 token（失控护栏，不是成本控制） | `AGENT_REPLY_TOKEN_BUDGET`（0 = 关） |
| RAG 上下文 | 自研 `RagContextMiddleware`，复用 `RagService` 现有索引，在 `on_system_prompt` 注入检索片段 | 关 | `AGENT_RAG_ENABLED` |
| 长期记忆 | 入口函数 `build_memory_middleware()`，恒返回 None | 关（只留入口，不实现） | 暂无 |
| 语音合成 | 框架 `TTSMiddleware` + `DashScopeTTSModel` | 关 | `AGENT_TTS_MIDDLEWARE=1` |

另加：

- `engines/agents/middleware/assembly.py`：固定装配顺序 **追踪（最外）→ 预算 → RAG → 语音 → 模型重试（最内）**，并把「未配置就返回空列表」的判定收在一处；
- `tracing.py`：注册 `TracerProvider` + OTLP/HTTP 导出器（进程内只注册一次），缺依赖或没配端点时安静跳过；
- `rag_context.py`：`RagContextMiddleware` 取最后一条用户消息检索、按 query 缓存、检索失败原样返回 system prompt；
- `memory.py`：长期记忆入口（docstring 写明接入点与 TODO），不引入 mem0 依赖。

## 关联文档

- `openspec/specs/agent-model-resilience/spec.md`：重试与回退行为不变，本变更只把它挪到装配链最内层。
- `openspec/specs/agent-role-run/spec.md`：角色运行入口不变。
- `engines/agents/rag/AGENTS.md`：RAG 只读资料目录、失败降级两条红线继续适用。

## Capabilities

### New Capabilities

- `agent-middleware-assembly`：五类中间件的装配入口、顺序与各自开关。

### Modified Capabilities

（无）

## Impact

- 新增：`engines/agents/middleware/{assembly,tracing,budget,rag_context,memory,tts}.py`
- 修改：`engines/agents/middleware/__init__.py`、`engines/agents/role/base.py`（`_middlewares()` 改为调装配入口）
- 新增测试：`tests/graybox/unit/test_agent_middleware_assembly.py`
- 默认行为：只多出「预算 20 万 token」这一条护栏（原先无上限）；追踪/RAG/语音/记忆默认不装
- 不影响：Django 接口、任务状态机、事件流（预算超限由框架注入提示，不落新事件类型）
