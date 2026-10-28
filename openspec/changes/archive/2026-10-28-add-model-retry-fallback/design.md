## 背景

框架两层机制都已存在但不够用：模型层 `ChatModelBase.__call__`（`agentscope/model/_base.py:206`）已有 `max_retries=3` + 固定 `retry_delay=1.0s`，只重试 provider 声明的异常类型，且只包住 `_call_api` 请求建立阶段；智能体层支持 `model_config.fallback_model`（`agent/_agent.py:3301`），但我们建 `Agent` 时没传 `model_config`，因此既没有 agent 层重试也没有备用模型。

## Decisions

### D1 · 只补一层，不重写模型层重试

- **选择**：中间件默认只对同一模型**再试一次**（`AGENT_MODEL_RETRY_ATTEMPTS=2` 表示总调用 2 次），用指数退避（800ms → 8000ms 封顶）；回退发生在这一次也用尽之后。
- **理由**：provider 感知的异常分类（`_get_retryable_exceptions()`）比自研分类准确，重复实现会两层叠加乘积级调用；真正缺的是「限流恢复常需 ≫3 秒」这一段，以及「主模型彻底不可用」的接管。
- **代价**：最坏调用次数 = 模型层 4 × 中间件 2 × 模型数 2 = 16 次；按 1s + 0.8s 的退避算，最坏多出十几秒。相对步级超时与 7200s 任务预算可接受。
- **备选被否**：只给 `Agent` 传 `model_config=ModelConfig(max_retries=..., fallback_model=...)` —— 解决回退，但重试仍是固定 1s、不覆盖流内错误、日志也进不了 `agent_event_log`。

### D2 · 回退只在瞬态故障后触发

配置类错误（401 / 403 / 400 / 参数校验）必须立刻暴露：若在这类错误后静默换模型，密钥配错会被掩盖成「跑得慢一点但成功」。因此回退条件与重试条件同一套分类。

### D3 · 流式只重试「首块之前」

`on_model_call` 拿到的可能是 `AsyncGenerator`（角色 `stream=True`）。实现上用「先取首块」当探针：首块之前抛错可以整次重放；首块之后抛错不能重放 —— 两段内容拼接比直接失败更糟（模型会看到自相矛盾的上下文）。已产出内容后失败按原始异常抛出。

### D4 · 中间件自身无状态

重试计数、当前模型都用局部变量，不写 `agent.state.middle_context`。理由：状态只活在一次 `on_model_call` 里，reply 结束或异常都不需要清理；同一实例可被多个 Agent 共用（与官方 `ReplyBudgetControlMiddleware` 的取舍不同，因为它要跨 reasoning 步骤累计）。

### D5 · 配置走环境变量，不进数据库

备用模型按部署环境配（`AGENT_FALLBACK_MODEL` 等），本变更不新增表字段、不改序列化器、不动前端。理由：这是运维口径（换 provider / 换 endpoint），按智能体配回退模型属另一件事，需要 DB + 接口 + 界面，单独立单再做。默认不启用回退，避免静默改变成本与模型能力。

### D6 · 日志写我们自己的 logger

`agent_event_log.warning(...)`，每条含：模型名、第几次尝试、退避时长、异常类型与消息、是否回退。理由：框架 logger 走 `agentscope._logging`，与平台日志分离，排障时看不到；用我们的 logger 可直接在 `logs/agents/agent_events.log` 里对齐时间线。

## Risks / Trade-offs

- [重试拉长单步耗时] → 上界 8000ms 且次数可配 1 关闭；退避只发生在失败路径。
- [计费与预算口径] → 失败的调用不产生 `ModelCallEndEvent`，因此不计入 `count_model_call()` 也就不计费；重试成功后只计一次。若将来要按「尝试次数」计费，需另立变更（本变更不碰计费）。
- [备用模型能力差异] → 回退模型可能与主模型能力不同（如 FLASH → PRO）；成本变化只在失败时发生，且需显式配置。
- [流式首块探针吞掉首块] → 实现上把首块缓存后原样 yield，顺序与内容不变（`_replay`）。
