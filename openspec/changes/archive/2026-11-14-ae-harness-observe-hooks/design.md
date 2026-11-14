## Context

`engines/ae_harness/` 的观测目前完全依赖事件流。AgentScope 2.0.9 的中间件提供 7 个 hook，其中两处信息事件流拿不到：上下文压缩的决策（`on_compress_context`）、每轮最终 system prompt（`on_system_prompt`）。

已核实的框架事实（读源码，非文档推测）：

| 事实 | 依据 |
| --- | --- |
| 中间件只能在 `Agent(...)` 构造时传入 | `Agent.__init__(middlewares=...)` |
| 构造时按 `is_implemented` 一次性分类到各 hook 队列 | `__init__` 里 `self._compress_context_middlewares = [...]` |
| **没有后置注册接口** | `dir(Agent)` 无 middleware / register 方法 |
| `on_compress_context(self, agent, input_kwargs, next_handler) -> None` | `input_kwargs` 含 `context_config`、`instructions` |
| `on_system_prompt(self, agent, current_prompt) -> str` | 变换式；多个中间件串行接力 |
| 上下文消息在 `agent.state.context` | `_compress_context_impl` 里 `len(self.state.context)` |
| 阈值 = `trigger_ratio * model.context_size` | 同上 |

约束（来自 `agents/AGENTS.md`）：能力型中间件一律禁止；只读观测中间件经**显式观测入参**传入，且必须满足「观测中间件准入清单」（不吞异常、不写状态、不改控制流、原样透传）。

## Goals / Non-Goals

**Goals:**

- 让「这轮压缩了吗、压缩前后差多少、阈值多少」和「这轮最终 system prompt 是什么」两件事可被事后回答。
- 观测层保持零同包依赖，只提供入口；落盘与渲染仍归事件层。
- 不传观测中间件时，行为与产物与改造前逐字节一致。

**Non-Goals:**

- 不实现任何能力型中间件（重试、路由、记忆、预算、工具扩展、提示词改写）。
- 不重复采集事件流已有的信息（模型调用、工具、文本、token、耗时）。
- 不引入 OpenTelemetry 或外部追踪后端。
- 不做压缩前后上下文正文的快照（只记条数），避免产物失控。

## Decisions

### D1. 一个中间件类，实现两个 hook

`on_compress_context` 与 `on_system_prompt` 同属「只读观测」，放同一个类里：二者共享同一个记录容器与时间戳格式，拆分只会增加装配参数。类名表达定位（观测），不表达具体 hook。

### D2. 交接方式：可注入回调，默认自有容器

中间件构造时接受可选的 `emit(record)` 回调；不传时写进自己的 `records` 列表。

理由：`create_agent` 是唯一创建出口，而记录器需要 `bundle.api_key_env`，只能在智能体创建**之后**构造——若强制回调，调用方必须在建智能体前就有一个可用的记录器，形成顺序死锁。默认容器解开了这个环，同时保留回调给需要自行路由的场景。

### D3. 压缩观测只读 `agent.state.context` 的条数，不额外数 token

框架在 `_compress_context_impl` 内部用 `model.count_tokens` 估算 token 并比较阈值，观测层若再调一次等于叠加一次模型侧开销，且可能产生网络调用——与「不触碰外部资源」冲突。因此只记条数与阈值参数：**能回答“是否压缩、压缩掉多少条”，不回答“压缩前后各多少 token”**。

### D4. `on_system_prompt` 存全文，不截断

需求方明确选择全文。代价是每轮几 KB、一次 5 轮运行约 30 KB，JSONL 明显变大；接受这个代价，换「提示词一字不差可核对」。不为省体积做截断或摘要——那样会破坏"可核对"这个唯一目的。

### D5. 观测记录作为独立事件类型落进既有 JSONL

事件行用 `event` 字段区分；观测行用固定类型名（如 `observation`）并带 `kind` 子字段（`compress_context` / `system_prompt`）。这样既复用既有落盘通道，又不会被当成 AgentEvent 参与折叠与渲染。

### D6. 装配入参命名 `observers`

区别于能力型中间件（未来若有，命名 `middlewares` 或根本不提供）。入参只做透传：`create_agent(..., observers=[...])` → `Agent(middlewares=[...])`。`agents/` 不 import `middleware`，只接收一个列表，保持「不知道观测实现」的分层。

## 模块防火墙自检

| 红线 | 是否触碰 | 说明 |
| --- | --- | --- |
| 跨 App import / 写库 / 前端 | 否 | 本期不涉及 `backend/` 与 `frontend/` |
| `engines/` 零 `django.*` / `apps.*` | 否 | 观测层只用框架与标准库 |
| 角色层「唯一创建出口」 | 否 | 不新增入口，只给既有出口加一个默认空参数 |
| 角色层「禁止能力型中间件」 | 否 | 只读观测，且已在 AGENTS.md 写死准入清单 |
| 观测层零同包依赖 | 是（新增约束） | `middleware/` 不 import `engines.ae_harness.*`；由测试守护 |

## Risks / Trade-offs

- **`on_system_prompt` 全文让产物变大** → 已接受；若将来过大，可改为「首末 N 行 + 哈希」但会失去可核对性，属另一变更。
- **依赖 `agent.state.context` 这一内部结构** → 属框架实现细节，升级可能变；用 `getattr` 兜底，取不到时记录空值而不是抛错。
- **记录器在智能体之后创建** → 用 D2 的默认容器解开；代价是回调路径与容器路径两种投递方式，需要在测试里都覆盖。
- **同时挂多个观测中间件** → 记录会重复；明确「一次运行只挂一个观测中间件」，由装配方保证。
- **压缩 hook 每轮都触发**（在推理前），会产生大量「未压缩」记录 → 这是有价值的信号（能看出上下文压力），但需要保留；若噪声太大，后续可加「仅在压缩发生时才落盘」的开关。

## Migration Plan

1. 先落中间件与测试（不接入任何入口）：此时产物不变。
2. 再给 `create_agent` 与记录器加入参（默认空）：仍不变。
3. 最后在 4 个入口接上：开始产出观测行。

回滚：入口不再传观测中间件即可，其余代码因默认空而静默失效。

## Open Questions

- 是否要在报告 HTML 里展示观测记录：本期不做，数据已具备。
- 是否给「未压缩」记录加节流/开关：等实测噪声后再定。
