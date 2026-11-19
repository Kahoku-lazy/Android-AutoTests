## Context

`agentscope` 的中间件钩子里，`on_model_call(agent, input_kwargs, next_handler)` 是**唯一能包住单次模型调用**的钩子，参数与返回值形状：

- 返回 `ChatResponse`（非流式）或 `AsyncGenerator[ChatResponse]`（流式）；
- 是 `async` 方法，注册后由框架 `await`。

`engines/agents` 的 `model_retry.py` 已在同一钩子上实现了 503 行的重试 + 备用模型；本变更只取其中**重试**部分，故意不做备用模型切换（那需要重建模型客户端，属另一个决策）。

现有 `ae_harness/middleware/` 只有 `observer.py`（只读观测）。

## Goals / Non-Goals

**Goals:**

- 一次模型调用失败可重试，且流式不重放。
- 一次运行有次数/时长上限，超限即停且异常可识别。
- 长任务可被外部取消，异常与预算区分。
- 三件事都以中间件挂载，默认关闭。

**Non-Goals:**

- 不做备用模型自动回退。
- 不改 `engines/agents`。
- 不做断点续跑（那是任务链路的事）。
- 不做设备锁（属后端）。

## Decisions

### D1. 两个模块，按“可靠性 / 运行控制”分工

| 模块 | 内容 | 为什么单独 |
| --- | --- | --- |
| `middleware/retry.py` | `is_transient_model_error`、`RetrySettings`、`ModelRetryMiddleware` | 它只做「失败再试一次」，不改变动作 |
| `middleware/control.py` | `RunBudget`、`CancelToken`、`BudgetExceeded`、`RunCancelled`、`BudgetMiddleware`、`CancelMiddleware` | 它只做「提前中止」，与重试是两种语义 |

不合并成一个「治理中间件」：两者失败语义相反（一个要继续、一个要停），合在一起会让调用方分不清。

### D2. 流式：只在首块之前重试

`on_model_call` 可能返回异步生成器。做法是把生成器包一层：

```python
started = False
async for chunk in stream:
    started = True
    yield chunk  # 一旦产出过，后续失败不再重试
```

理由：已显示的文本无法撤回，重放会让用户看到重复内容。这与 `engines/agents` 的「流式不重放」一致。

### D3. 错误分类只按「值得重试」的黑白名单

白名单：`429 / 500 / 502 / 503 / 504`、`TimeoutError`、`ConnectionError`、异常类型名含 `RateLimit` / `Timeout` / `APIConnection`。
黑名单（即使命中白名单也立即抛）：`400 / 401 / 403 / 404 / 422`，异常类型名含 `Authentication` / `PermissionDenied` / `NotFound` / `BadRequest` / `Validation`。

黑名单优先：宁可少重试，不要把参数错误重试三次。

### D4. 退避参数走环境变量，有硬上限

`AE_MODEL_MAX_ATTEMPTS`（默认 3，上限 8）、`AE_MODEL_BACKOFF_BASE`（默认 0.8 秒）、`AE_MODEL_BACKOFF_MAX`（默认 8 秒）。退避 = `min(base * 2**(n-1), max)` 加 ±20% 抖动。

硬上限防止有人把重试次数调成无限、把退避调成半小时。

### D5. 预算在 `on_model_call` 入口检查

次数与时长都在**调用前**判定，超限立即抛 `BudgetExceeded`。不在 `on_reply` 判，因为一次 reply 里可能有多轮模型调用。

### D6. 取消用 `threading.Event`，不用 asyncio 原语

理由：SOP 在独立线程里跑（`run_task_async` 那种模式），跨线程置位用 `threading.Event` 最直接；`asyncio.Event` 无法从别的线程安全置位。

### D7. 两个异常类，登记在子 AGENTS

`engines/AGENTS.md` 有「禁止随意新增自定义异常」的红线，因此这两个类必须先在 `ae_harness/AGENTS.md` 立项登记：

| 异常 | 语义 | 调用方怎么用 |
| --- | --- | --- |
| `BudgetExceeded` | 预算耗尽 | 记为「超预算中止」，不是失败 |
| `RunCancelled` | 被外部取消 | 记为「用户取消」 |

两者都继承 `RuntimeError`，便于现有 `except Exception` 兜底。

## 模块防火墙自检

| 红线 | 是否触碰 | 说明 |
| --- | --- | --- |
| `engines/` 零 `django.*` / `apps.*` | 否 | 只依赖标准库 |
| 中间件只做观测 | **是（修订）** | 红线扩为三类，已写进两份 AGENTS |
| 能力型中间件 | 否 | 不挂工具、不加记忆 |
| 新增异常类 | **是（登记）** | 两个类在子 AGENTS 立项 |

## Risks / Trade-offs

- **重试会放大 token 消耗**：失败重试要重发上下文。用硬上限（最多 8 次）+ 黑名单（参数错不重试）压住。
- **预算中止会让运行「半途而废」**：已产出的报告与用量仍保留，调用方按 `BudgetExceeded` 记「中止」而非「失败」。
- **取消只能在下一次模型调用前生效**：一次模型调用本身不可中断（框架不支持），最长延迟 = 一次调用的耗时。
- **两个异常类进入公共面**：调用方要 `except` 它们；写进 AGENTS 并配单测，避免后人各自造新的。

## Migration Plan

1. 先加两个中间件与单测，默认不挂载 → 现有行为零变化。
2. `backend_bridge` 的会话与 SOP 入口加可选参数；不传时链路不变。
3. 回滚：删除两个模块与可选参数即可。

## Open Questions

- 备用模型回退要不要做？它需要「换模型重建客户端」，与「重试同一动作」不是一回事，建议单独评估。
- 预算上限的默认值由谁定：调用方（后端按任务类型配置）还是引擎给默认？本期只做「可设置」，不给默认上限。
