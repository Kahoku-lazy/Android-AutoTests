# AgentScope 用法盘点与最佳方案（2.0.9 口径）

> 日期：2026-11-19 ｜ 性质：**只读审计，未改动任何代码**
> 版本口径：本机实测 `agentscope.__version__ == 2.0.9`；文档引用全部钉在 `/zh/versions/2.0.9/`。
> 方法：`engines-docstring-check read` 取模块地图 → 读关键实现 → 官方文档 MCP 逐块对照 → 安装包源码/运行时实测交叉验证。
> 来源标注：【文档】= 官方文档原文；【实测】= 本机安装包源码或运行时验证；【推断】= 我的分析，需实测确认。

---

## 一、结论先行

**总体判断：仓库对 AgentScope 2.x 的核心用法（credential+model 装配、FunctionTool、SOP 引擎、reply_stream 事件消费、VectorStoreBase 扩展）都是官方姿势，架构方向不需要推倒重来。** 但存在 **1 个实测确认的潜在缺陷**、**3 处与官方机制重叠或偏离的自研实现**、以及 **一批官方已有而仓库未用的能力**。按优先级：

| 级别 | 发现 | 一句话最佳方案 |
| --- | --- | --- |
| **P0 缺陷** | `document/tools.py` 与 `case_library/tools.py` 把 **lambda** 传给 `FunctionTool(permission=...)`，官方该参数只收 `PermissionDecision` 实例；实测 `check_permissions()` 返回的是函数对象 | 改传实例（adb 域已是正确写法）；写工具 `save_authored_case` 在 DEFAULT 模式下走到权限检查时会拿到非法返回值 |
| **P1 重叠** | 模型层内置重试（默认 `max_retries=3`，即 4 次尝试）× 自研 `ModelRetryMiddleware`（默认 3 次）叠加，瞬时错误最多打 **12 次** | 重试单层化：模型层调低、中间件只保留「流式首块前重试」这一官方没有的兜底 |
| **P1 偏离** | 取消用 `CancelMiddleware` 在每次模型调用前抛 `RunCancelled`；官方中断是 `task.cancel()` / `UserInterruptEvent`，上下文一致且可恢复 | 保留 `CancelToken` 跨线程登记，触发改为对 reply 协程 `task.cancel()`，边界把 `CancelledError` 记成「取消」 |
| **P1 空转** | 用例编写生产入口 `_finish_goal._attempt` 是**桩**（恒 `passed=True`，不跑模型）；`goal_case.py` 手写退回循环与官方 `GoalPipeline` 语义重复 | 落地用例编写时直接装配官方 `GoalPipeline(executor, verifier, max_iters)`，不要扩展手写循环 |
| **P2 增强** | SOP 报告靠 reply 顺序推断执行者/验收者分块（已知限制）；官方引擎每步尝试前后产出 `SOP_STEP_STARTED/ENDED` CustomEvent | 报告分块改消费官方 CustomEvent，消除对「先执行后验收」固定结构的依赖 |
| **P2 增强** | 自研 `SQLiteVectorStore` 余弦全表扫描；官方有本地文件型 `QdrantStore(path=...)` / `MilvusLiteStore(uri=...)` | 评测通过后换官方本地向量库，删掉手写存储实现 |
| **P2 增强** | 会话 `_SESSIONS` 纯内存，进程重启即丢；官方 `AgentState` 可 JSON 序列化跨进程恢复 | 状态序列化交后端落库（engines 不写库红线不变），实现可恢复会话 |
| **P2 调参** | `create_agent`/`create_model` 未暴露官方四个配置对象与 `context_size`/`parameters`；注入时区默认 UTC | 按需暴露 `ContextConfig`/`ReActConfig`/`InjectionConfig(timezone="Asia/Shanghai")` 等 |

**需要需求方决策的事项见第六节**；其中触及 AGENTS 红线的（预算中间件语义、取消异常口径、能力型中间件准入）必须先走「变更申请」，本报告不自行批准任何规则改动。

---

## 二、盘点范围

仓库实际 import AgentScope 的模块（grep 全量核对）：

| 区域 | 模块 | 用到的官方 API |
| --- | --- | --- |
| Agent 装配 | `ae_harness/agents/creator.py` | `Agent(name, system_prompt, model, middlewares)` |
| 模型与凭证 | `ae_harness/agents/models.py` | `DeepSeek/DashScope/OpenAIChatModel` + 三家 Credential + MultiAgentFormatter + 自定义 `GoveeChatFormatter`/`GoveeThinkingChatModel` |
| 中间件 | `ae_harness/middleware/{observer,retry,control}.py` | `MiddlewareBase`（on_model_call / on_system_prompt / on_compress_context） |
| SOP | `ae_harness/workflow/sop/runner.py` | `SOP / SOPStep / SOPEngine / reply_stream / engine.state / engine.phase` |
| 工具与权限 | `tools/{adb,case_library,document}/tools.py`、`knowledge/tool.py`、`backend_bridge/workflow/fake_world.py` | `FunctionTool / ToolChunk / PermissionDecision / PermissionBehavior` |
| RAG | `knowledge/{store,indexer,service,models,usage}.py` | `VectorStoreBase / KnowledgeBase / TextParser / ApproxTokenChunker / DashScopeEmbeddingModel / EmbeddingModelBase` |
| 会话与运行 | `backend_bridge/session.py`、`run.py` | `UserMsg / agent.reply_stream / agent.toolkit.add_tool / get_tool_schemas` |
| 编排（目标/团队） | `backend_bridge/workflow/{goal_case,team_breakdown}.py` | 文档声称生产用 `GoalPipeline / TeamPipeline`，**实测生产调用方未接入**（见 §3.9） |
| 运行时引导 | `ae_harness/assistant/_bootstrap.py` | `agentscope.setup_logger` |

---

## 三、逐块对照与最佳方案

### 3.1 Agent 装配（creator.py）——✅ 官方姿势，配置面未暴露

现状：`Agent(name=..., system_prompt=..., model=..., middlewares=observers)`，工具创建后由调用方 `toolkit.add_tool` 挂载。
【文档】[配置智能体](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/configure-agent) 的最简配置与此完全一致；`Toolkit` 是工具唯一来源，`add_tool` 是公开 API，创建后挂载合法。

官方还提供四个配置对象，仓库一个都没传（全部吃默认值）【实测安装包字段】：

| 配置对象 | 关键字段与默认值 | 对本平台的意义 |
| --- | --- | --- |
| `ModelConfig` | `max_retries=0`、`fallback_model=None` | Agent 级重试 + 备用模型（官方内置，见 §3.3） |
| `ContextConfig` | `trigger_ratio=0.8`、`tool_result_limit=50000`、`max_image_num=5`、压缩失败回退截断=True | adb 截图多、`adb_dump_ui` 输出大；默认值基本合理，但 `tool_result_limit` 与图片张数值得按真机任务调参 |
| `ReActConfig` | `max_iters=50`、`stop_on_reject=False`、`interruption_raise_cancelled_error=False` | 迭代上限与取消语义（见 §3.4） |
| `InjectionConfig` | `inject_runtime_state=True`、**`timezone="UTC"`**、`tool_retries_limit=3`（同参工具连败注入换思路提示） | 平台在中国时区，注入的时间是 UTC【推断：对「按时间判断日志」类任务有误导风险】；官方自带「重复工具报错提示」，与自研重试互补 |

**最佳方案**：`create_agent` 保持「角色三要素」红线不变，把运行参数以**可选显式入参**透传（如 `context_config`/`react_config`/`injection_config`），由 `backend_bridge` 装配时决定；至少把 `timezone="Asia/Shanghai"` 定下来。这属于装配参数面扩展，是否违反「禁止第四样东西」需按 agents/AGENTS.md 口径请示（配置对象不是能力，倾向不违反，但**先请示**）。

### 3.2 模型与凭证（models.py）——✅ 模式正确；govee 补丁建议换官方扩展点

现状正确的部分【文档】[大语言模型](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/model/llm)：
- `Model(credential=..., model=..., stream=..., formatter=...)` 是官方统一模式；
- `GoveeChatFormatter` 继承 `OpenAIChatFormatter` 覆写公开 `format()`，是合法定制；
- DeepSeek/DashScope 用 `MultiAgentFormatter`：官方多实体对话推荐件（SOP 执行者/验收者具名交接场景适用）。

三个改进点：

1. **`GoveeThinkingChatModel` 覆写私有 `_call_api` + 网关错误字符串匹配**（`"Thinking mode does not support this tool_choice"`），三段重发逻辑约 50 行。
   【实测】官方 `ChatModelBase.generate_structured_output` 已内置策略阶梯 `forced → auto → no_think → none`，`no_think` 用的正是 `_get_disable_thinking_kwargs()` 扩展点；`DeepSeekChatModel` 的实现就是返回 `{"extra_body": {"thinking": {"type": "disabled"}}}`——与 govee 补丁想注入的参数**一模一样**。`OpenAIChatModel` 未覆写该钩子（所以 govee 走 OpenAI 类时官方阶梯跳过 no_think），且其 `_get_structured_output_fallback_exceptions` 已含 `BadRequestError`。
   【文档】2.0.9 [发布说明](https://docs.agentscope.io/zh/versions/2.0.9/release-notes) #2140：官方已为 Anthropic/DeepSeek/DashScope/Moonshot 修复「思考模式拒绝强制 tool_choice」——正是本仓库手工补丁对抗的问题。
   **最佳方案**：govee 模型类改为只覆写 `_get_disable_thinking_kwargs()`（官方 protected 扩展点，与 DeepSeek 同款写法），把「关思考」交给官方阶梯。
   **⚠️ 必须实测的前提**【实测+推断】：SOP 交付/验收走的是 `reply_stream(structured_schema=...)` + 内置 `GenerateStructuredOutput` 工具（`agent/_structured_output_tool.py`），**不是** `generate_structured_output()` 方法；策略阶梯是否覆盖这条路径未确认。若不覆盖，`_call_api` 兜底仍需保留，但应把字符串匹配收窄为「仅识别该网关拒绝 + 复用官方 disable kwargs」。落地前用 govee 真网关跑一次 SOP 强制结构化输出验证。

2. **`create_model` 未暴露 `max_retries` / `retry_delay` / `context_size` / `parameters`**【实测默认值】：OpenAI 系 `context_size=128000`、DeepSeek `65536`、DashScope `131072`、`max_retries=3`。govee 网关背后的真实模型窗口若与 128000 不符，上下文压缩触发点就错了。**最佳方案**：连接参数增加可选 `context_size`（由运营配置传入），重试参数与 §3.3 一起定口径。

3. **单用户对话页也用 MultiAgentFormatter**【推断，需评测】：官方说默认 ChatFormatter 适合一人一智能体对话，MultiAgentFormatter 会把历史合并成一条带名 user 消息。对 DeepSeek 前缀缓存（计费里有 cache_hit 项）是否更优/更劣不确定。**最佳方案**：对话页角色做一次 A/B（缓存命中率、token 成本、回答质量），再决定是否按角色区分 formatter；SOP 角色保留 MultiAgentFormatter。此项涉及成本口径观测，不动计费规则。

### 3.3 重试（retry.py）——⚠️ 三层重试叠加，建议单层化

【实测】官方有两层内置重试：
- 模型层：`ChatModelBase.__call__` 对 `_get_retryable_exceptions()` 内的异常重试 `max_retries+1` 次（OpenAI 系声明了 APIConnectionError/APITimeoutError/RateLimitError/InternalServerError），默认 3+1=4 次，固定 `retry_delay=1.0s`；
- Agent 层：`ModelConfig(max_retries=0, fallback_model=...)` 默认关闭，开启后按备用模型列表轮转。

【实测】模型层重试**只包 `_call_api` 的调用返回**，不包流式迭代中段（基类源码无 asyncgen 包装）。

现状：自研 `ModelRetryMiddleware` 默认 3 次、指数退避+抖动，叠在模型层之上 → 瞬时错误最坏 **4×3=12 次调用**，退避时间也叠加。自研中间件的**真实独有价值**是「流式首块之前可重试、首块之后不重放」——这恰好补官方缺口；错误分类（黑名单优先）也比官方按异常类型更细。

**最佳方案**（二选一，推荐 A）：
- **A. 模型层 `max_retries=0或1`，中间件保留**：重试策略集中在自研中间件（退避+抖动+流式边界+错误分类），模型层只留极薄兜底。改动最小，语义不变，符合「可靠性中间件重试同一动作」准入。
- **B. 删中间件的调用错误重试，只留流式包装**：调用错误全交模型层（需把 `retry_delay`/`max_retries` 暴露成可配）。代码更少，但失去抖动与细分类。
- 备用模型（`ModelConfig.fallback_model`）官方内置，但 middleware/AGENTS.md 明文「备用模型切换属换动作，需单独立项」——**不在本次建议内自动启用**，列为决策项。

### 3.4 预算与取消（control.py）——⚠️ 取消建议改官方中断；预算语义差异需决策

**取消**：
【文档】[中断智能体](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/interrupt-agent)：官方机制是对承载 `reply/reply_stream` 的协程 `task.cancel()`（内部 `asyncio.CancelledError` 干净展开，**上下文保持一致、会话可立即继续**）；暂停态用 `UserInterruptEvent`。【实测】模型基类捕获 `CancelledError` 返回 `INTERRUPTED` 响应；`ReActConfig.interruption_raise_cancelled_error=True` 可改为向上抛 `CancelledError`。
现状：`CancelMiddleware` 只在**每次模型调用前**检查令牌并抛 `RunCancelled`。差距【推断】：① 长工具执行（adb 安装/截屏）期间取消不生效，要等下一次模型调用；② 自定义异常从 reply 中途抛出，上下文一致性不如官方展开路径；③ 取消后能否原会话继续，官方路径有明确保证。
**最佳方案**：`CancelToken` 跨线程登记保留（backend_bridge/cancel.py 不动语义），运行侧改为「令牌置位 → 对当前 reply task 执行 `task.cancel()`」，在运行边界捕获 `CancelledError` 记为「取消」（可继续用已登记的 `RunCancelled` 在边界包装，避免新增异常类）。SOP 场景同理：引擎 `reply_stream` 的承载协程被 cancel。此项改变取消的实现机制与异常来源，**触及 middleware/AGENTS「必须抛 BudgetExceeded/RunCancelled」条款的字面口径，先提变更申请**。

**预算**：
【文档】[中间件·预算控制](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/middleware)：官方 `ReplyBudgetControlMiddleware` 按**加权 token**（input×w1+output×w2）累计单次 reply 成本，超限注入收尾 HintBlock 并强制 `tool_choice=none`，让模型**优雅收尾**；实例无状态、HITL 恢复安全。
现状：自研 `RunBudget` 按**模型调用次数+墙钟秒数**硬中止（抛 `BudgetExceeded`）。
差异：官方是 token 成本口径（与平台记账天然对齐）+ 优雅收尾；自研是次数/时长口径 + 硬中止。两者语义不同，不是简单替换关系；且官方中间件会改 `tool_choice`、注入提示——按本仓库中间件准入分类属于「改变行为」，**与现行红线冲突**。
**最佳方案**：保留自研硬中止作为「运行控制」；若平台想要「成本封顶且拿到结论性回复」，把官方 `ReplyBudgetControlMiddleware` 作为**可选第四类准入**提变更申请（改什么/为什么/影响面/回退四件事齐备后再动）。也可两者并用：token 预算先触发优雅收尾，次数/时长预算兜底硬中止。

### 3.5 观测（observer.py）——✅ 合规；可选补充官方 TracingMiddleware

现状：只读采样 `on_system_prompt` / `on_compress_context`，透传不改行为，符合官方 hook 形态与仓库准入清单。事件记录走 `reply_stream` 事件流 + 自研 recorder/HTML 报告——官方没有等价的「HTML 运行报告」件，**自研合理，保留**。
【文档】官方 `TracingMiddleware` 提供 OpenTelemetry 全生命周期追踪（reply/model_call/acting 三层 span，含 token 数），未配 TracerProvider 时近零开销。**最佳方案（可选）**：平台要接 OTel 观测后端时直接挂官方件，不自研 span；它与现有 HTML 报告互补不冲突。挂载仍走 `observers` 显式入参（只读类准入满足）。

### 3.6 SOP（workflow/sop/runner.py）——✅ 与官方 quickstart 一致；三个官方能力未用

现状【文档】[标准作业流程](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/sop)：`SOP/SOPStep(executor, verifier, max_attempts)/SOPEngine/reply_stream/engine.phase` 用法与官方示例逐项吻合；`run_sop` 是薄封装（记录+报告+结论汇总），没有重写编排，符合红线。
未用的官方能力：
1. **`SOP_STEP_STARTED` / `SOP_STEP_ENDED` CustomEvent**（每次尝试前后各一个，含 step 名与 attempt 序号）。仓库 workflow/AGENTS「已知限制 2」说报告分块靠 reply 顺序推断、依赖引擎固定结构——**官方事件正是这个限制的解法**。最佳方案：recorder 消费这两个 CustomEvent 做执行者/验收者分块与尝试计数，删掉顺序推断。
2. **`SOPRunState` 持久化/恢复**（Pydantic，`model_dump_json` 落盘后另一进程重建引擎续跑）。平台 SOP 目前跑完即弃；若要做「任务中断后续跑」，这是官方路径（注意：执行者/验收者各自的 AgentState 需另行保存，见 §3.8）。
3. **AWAITING 挂起与人机交互**（工具授权/外部执行挂起，`UserConfirmResultEvent` 续跑）。平台无人值守暂不需要，列为远期。
另：`_collect_schemas` 兜底路径读私有 `toolkit._tools`【实测】——主路径已用公开 `get_tool_schemas()`，兜底建议也走公开 API 或明确标注版本脆弱点。SOP 模块官方标注**实验性**，升级前复核（仓库已知限制 3 已登记，保持）。

### 3.7 工具与权限（tools/*、knowledge/tool.py）——⚠️ P0 缺陷 + 权限策略可集中化

**P0 缺陷（实测确认）**：
- `tools/document/tools.py:33,51` 与 `tools/case_library/tools.py:33,54`：`_ALLOW = lambda _request: PermissionDecision(...)`，把**可调用对象**传给 `FunctionTool(permission=...)`。
- 【实测】官方 `FunctionTool.permission` 类型是 `PermissionDecision | None`；`check_permissions()` 原样返回 `self._permission`。运行时验证：传 lambda 时返回 `function`，**不是** `PermissionDecision`。
- 影响【推断】：`read_requirement` 因 `is_read_only=True` 走权限决策矩阵第③步「只读快速通道」提前放行，lambda 不会被消费——**侥幸能跑**；`save_authored_case` 是写工具，DEFAULT 模式下走到第④步 `check_permissions`，权限引擎拿到函数对象读 `.behavior` 会出错。当前生产用例编写是桩（§3.9）所以未爆雷，**一旦接真模型即触发**。
- 正确写法仓库里已有：`tools/adb/tools.py:104` 传的是 `PermissionDecision` 实例。**最佳方案**：两处 lambda 改为实例（一行级修复，走 OpenSpec fix）。

**权限策略集中化（P2）**：
【文档】[权限系统概述](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/permission-system/overview)：官方无人值守推荐 **`DONT_ASK` 模式 + 显式 allow_rules**（保留工具安全网、从不打扰用户），策略集中在 `AgentState.permission_context`；BYPASS 需自配 deny_rules 护栏。
现状：每个工具硬编码 ALLOW，等于把策略散在工具装配里，权限上下文全程默认。功能上可用，但：① 策略不可按角色/环境切换；② 验收者「只挂只读工具」是装配纪律，官方 **EXPLORE 模式**（写操作自动 DENY）可作第二道防线。
**最佳方案**：平台角色装配时显式设置 `PermissionContext`（执行者 DONT_ASK+allow_rules 或维持工具级 ALLOW；验收者叠加 EXPLORE），工具级 `permission` 保留为兜底。是否调整「验收者只读靠装配交集」的红线口径，列为决策项。

**FunctionTool 其余用法**✅：`is_read_only`/`is_concurrency_safe` 静态标记、docstring 生成 schema、`ToolChunk` 流式工具（adb 截图）均与 [Python 工具](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/tool/python-tool) 一致。官方还有 `check_read_only(tool_input)` 动态只读判定（按入参决定），adb 工具当前静态标记已够用，暂无必要。

### 3.8 RAG 知识库（knowledge/*）——✅ 扩展路径合法；存储与集成有官方替代件

- **自研 `SQLiteVectorStore`**：走的是官方「自定义向量数据库」扩展点（继承 `VectorStoreBase` 七方法 + async context），合法【文档】[RAG·自定义拓展](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/rag)。但官方已有**本地文件型**实现：`QdrantStore(path=...)`（本地磁盘模式，无需服务）与 `MilvusLiteStore(uri="./x.db")`，另有 `:memory:` 模式适合测试。自研余弦**全表扫描**在小库可用，规模上去后性能与召回都不如官方 ANN 实现。
  **最佳方案**：知识库挂载评测（Recall@k/MRR，见 knowledge/AGENTS 与 add-knowledge-auto-eval）通过后，把存储切到 `QdrantStore(path=...)` 或 `MilvusLiteStore`，删除手写 store；`KnowledgeIndexer` 的增量签名逻辑（mtime/size/chunker 版本）是官方没有的自研价值，**保留**。代价：新增 `qdrant-client` 或 `milvus-lite` 依赖；「整目录可删」性质不受影响。
- **检索工具 vs 官方 `RAGMiddleware`**【文档】：官方 agentic 模式暴露的 `search_knowledge` 工具与自研 `knowledge/tool.py` 几乎同构（模型自主决定何时检索、可限定库子集、自动列库描述），还支持 `rerank_model` 重排（尽力而为、失败回退向量序）与 static 注入模式。
  **但**：`RAGMiddleware` 是能力型中间件（`list_tools` 扩展能力），与 ae_harness「能力型中间件一律禁止」红线直接冲突；自研只读工具形态是**现行规则下的正确选择**。
  **最佳方案**：维持工具形态接回角色（按 knowledge/AGENTS 的局部可选导入路径）；若未来想要官方重排/多库混合能力，两条路：a) 提变更申请放开 RAGMiddleware 准入；b) 在自研工具内借鉴官方重排思路（额外一次模型调用，成本需入账）。**不自行选择，列决策项**。
- **解析器**：官方有 `PDFParser/WordParser/ExcelParser/PPTParser/ImageParser`，自研只扫 `.md/.txt`。产品手册若是 PDF/Word，扩格式只需换官方 parser，不动架构。
- **嵌入用量代理 `UsageRecordingEmbedding`**✅：透传 `__call__` 记 token，与官方 `EmbeddingModelBase` 契约一致；官方嵌入模型自带分批/重试/缓存【文档 [嵌入模型](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/model/embedding)】，代理不干扰这些机制。

### 3.9 目标/团队流水线（goal_case.py / team_breakdown.py）——⚠️ 生产是桩，官方件未接

【实测】生产调用方 `backend/apps/task_list/task_runner.py`：
- `_finish_goal._attempt` **忽略 prompt、恒返回 `passed=True` + 硬编码一行用例**——用例编写根本没跑模型；
- `_finish_team` 只对任务正文做 JSON 校验，没有 TeamPipeline、没有模型调用。
而 `goal_case.py` 手写「退回理由拼进 prompt 再试」循环，与【文档】[目标流水线](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/pipeline/goal) 的 `GoalPipeline(executor, verifier, max_iters)` 语义重复（官方验证者是普通 Agent，结论走结构化输出，可带工具真验证）。模块 docstring 写「生产调用方传入官方 GoalPipeline」，与实测不符——**意图与实现脱节**。
**最佳方案**：用例编写真正落地时，在 `backend_bridge/workflow/` 装配官方 `GoalPipeline`（执行者/验收者经 `create_agent`，验收者只读工具交集），`run_goal_case` 的手写循环要么删除、要么降级为纯测试缝（不得在生产路径与 GoalPipeline 叠加成双重退回循环）。需求拆解同理接 `TeamPipeline`【文档 [团队流水线](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/pipeline/team)】。这符合 backend_bridge「禁止第二套编排循环」红线精神。

### 3.10 会话与状态（backend_bridge/session.py）——✅ 运行姿势正确；持久化是官方给的升级路

现状：同一连接键复用同一 Agent 实例（上下文连续），每轮 `reply_stream(UserMsg)` + recorder + 报告——与【文档】[运行智能体](https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/run-agent) 一致。设备序列号随每轮消息注入而非改工具全局状态，干净。
差距：`_SESSIONS` 是进程内存字典，Django 进程重启/多 worker 即丢会话。
【文档】官方「持久化状态」：`AgentState` 全量 JSON 序列化（上下文、压缩摘要、权限规则、工具状态、回复位置），内置 `RedisStorage` 按 `(user_id, agent_id, session_id)` 组织；**平台已退役 Redis**，但存储后端可自定义。
**最佳方案**：engines 侧在每轮结束把 `agent.state` 序列化随结果交出（不写库，守红线），后端落 DB；恢复时反序列化传入 `Agent(state=...)`。这是官方多会话服务的基础件，也为 SOP 跨进程续跑（§3.6）铺路。列为 P2 决策项（涉及后端表结构与引擎结果契约）。

---

## 四、保持现状的部分（审计确认无需动）

| 用法 | 结论 |
| --- | --- |
| `create_agent` 唯一出口 + 角色三要素 + observers 显式入参 | 与官方装配模型兼容，仓库红线自洽 |
| `GoveeChatFormatter` 覆写公开 `format()` | 合法定制 |
| `reply_stream` 事件消费 + 自研 recorder/HTML 报告 | 官方无等价报告件，自研合理 |
| `KnowledgeIndexer` 增量签名（mtime/size/chunker 版本） | 官方没有的自研价值 |
| `UsageRecordingEmbedding` 用量代理 | 契约一致，服务记账 |
| SOP `run_sop` 薄封装 | 未重写编排，符合官方与红线 |
| `fake_world.py` 同名假工具（评测） | 测试缝，不进生产 |
| `agentscope.setup_logger` 日志引导 | 官方 API |

---

## 五、优先级与落地顺序建议（全部走 OpenSpec，本次未动代码）

1. **P0**：修 `permission=lambda` 缺陷（document/case_library 两处，改传 `PermissionDecision` 实例；补一条「写工具权限检查返回类型」单测）。
2. **P1**：重试单层化（方案 A：模型层 `max_retries` 调低 + 保留中间件流式兜底）；govee 模型类换 `_get_disable_thinking_kwargs` 扩展点（先真网关实测 SOP 结构化路径）。
3. **P1**：取消机制改官方 `task.cancel()`（先提变更申请：异常口径与 middleware 条款字面冲突）。
4. **P1**：用例编写/需求拆解接官方 `GoalPipeline`/`TeamPipeline`（替换生产桩与手写循环）。
5. **P2**：SOP 报告分块改消费 `SOP_STEP_STARTED/ENDED`；`InjectionConfig.timezone` 定 Asia/Shanghai；`context_size` 暴露。
6. **P2**：知识库评测通过后切官方本地向量库；会话状态持久化（engines 交出序列化状态、后端落库）。
7. **P2/决策后**：权限上下文集中化（DONT_ASK/EXPLORE）；官方预算中间件准入；RAGMiddleware 准入；formatter A/B。

---

## 六、需要需求方决策的清单

| # | 决策项 | 选项 | 触及红线？ |
| --- | --- | --- | --- |
| 1 | P0 lambda 缺陷是否立即开 OpenSpec fix | 修 / 暂缓（用例编写未接真模型前不爆雷） | 否 |
| 2 | 重试单层化选 A 还是 B；模型层 `max_retries` 定多少 | A（推荐）/ B | 否（可靠性准入内） |
| 3 | 取消改官方 `task.cancel()`：`RunCancelled` 保留为边界包装还是改记 `CancelledError` | 保留包装（推荐，不动异常登记表）/ 改口径 | **是**：middleware/AGENTS 异常条款字面口径，需变更申请 |
| 4 | 是否引入官方 `ReplyBudgetControlMiddleware`（token 加权+优雅收尾）作为第四类中间件准入 | 引入（与硬中止并用）/ 不引入 | **是**：能力型中间件禁令，需变更申请 |
| 5 | 是否启用 `ModelConfig.fallback_model` 备用模型 | 启用 / 不启用 | **是**：middleware/AGENTS「换动作需单独立项」 |
| 6 | 验收者只读是否叠加官方 EXPLORE 权限模式（第二道防线） | 叠加 / 维持纯装配交集 | 部分：backend_bridge 装配规则口径，建议请示 |
| 7 | 知识库接回角色时用自研工具（现行规则）还是申请 RAGMiddleware 准入 | 自研工具（推荐，合规）/ 申请准入 | 后者**是**：需变更申请 |
| 8 | 向量库是否切官方 QdrantStore/MilvusLiteStore（新增依赖） | 切 / 维持自研 SQLite | 否（knowledge 领域内） |
| 9 | 会话状态持久化（后端新表/字段 + 引擎结果契约扩展） | 做 / 暂缓 | 否，但涉及后端契约，需 OpenSpec propose |
| 10 | `create_agent` 暴露 ContextConfig/ReActConfig/InjectionConfig 可选入参 | 暴露 / 只定 timezone 最小改 | 部分：agents/AGENTS「第四样东西」口径，建议请示 |
| 11 | 对话页 formatter A/B（MultiAgent vs Chat，缓存成本） | 评测后定 / 维持现状 | 否（不动计费规则，只观测） |

---

## 七、引用（全部 2.0.9 中文站）

- 配置智能体：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/configure-agent
- 运行智能体（含持久化状态）：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/run-agent
- 中断智能体：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/agent/interrupt-agent
- 大语言模型：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/model/llm
- 嵌入模型：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/model/embedding
- 中间件（内置件与自定义）：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/middleware
- 标准作业流程：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/sop
- 权限系统概述：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/permission-system/overview
- Python 工具：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/tool/python-tool
- RAG：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/rag
- 目标流水线：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/pipeline/goal
- 团队流水线：https://docs.agentscope.io/zh/versions/2.0.9/building-blocks/pipeline/team
- 发布说明（#2140 思考模式修复、#1730 统一重试、#1816 重复工具报错提示）：https://docs.agentscope.io/zh/versions/2.0.9/release-notes

> 诚实声明：§3.2 govee 阶梯覆盖范围、§3.2 formatter 缓存影响、§3.7 权限引擎对非法返回值的具体报错形态为【推断】，已标注需实测；其余结论均有文档原文或安装包实测支撑。本报告未改动任何代码与规则文档。