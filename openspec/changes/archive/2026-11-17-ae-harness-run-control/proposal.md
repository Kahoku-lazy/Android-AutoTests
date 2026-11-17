## Why

`engines/backend_bridge` 现在能跑单角色与 SOP，但比 `engines/agents` 少三样**生产必需**的运行时保障：

| 缺什么 | 后果 |
| --- | --- |
| 模型调用重试 / 备用模型 | 一次 429 或超时就让整条 SOP 失败，前面几步白跑 |
| 预算停止（调用次数 / 时长上限） | 模型陷入循环时能烧掉几千万 token |
| 取消 | 长任务无法中止，用户只能等 |

`engines/agents` 里这三样都有（`middleware/model_retry.py` 503 行、`event_sink` 的 `MAX_MODEL_CALLS` / `MAX_RUN_SECONDS`、`platform_run` 的 `request_cancel`）。

## What Changes

- 在 `engines/ae_harness/middleware/` 新增两个模块：
  - `retry.py`：模型调用重试——错误分类、指数退避、**流式已产出不重放**。
  - `control.py`：运行预算（模型调用次数、墙钟秒数）与取消令牌；超预算抛 `BudgetExceeded`，被取消抛 `RunCancelled`。
- **修订中间件红线**：原来只允许「只读观测中间件」，现扩为三类，并把准入清单写进 `middleware/AGENTS.md` 与 `agents/AGENTS.md`。
- `engines/backend_bridge` 的单角色入口与 SOP 入口都接受可选的预算与取消令牌，默认不启用（不传则行为与现在一致）。

**明确不做**：不动 `engines/agents`；不做备用模型自动切换（本期只做重试，回退单独评估）；不接任务链路。

## 关联文档

- 需求来源：需求方「与 agents 对比，按补齐短板这个思路去改」。
- 红线修订：[`engines/ae_harness/agents/AGENTS.md`](../../../engines/ae_harness/agents/AGENTS.md) 红线 2、[`engines/ae_harness/middleware/AGENTS.md`](../../../engines/ae_harness/middleware/AGENTS.md) 准入清单。
- 受影响主 spec：新建 `ae-harness-run-control`。
- 相关既有能力：`ae-harness-observe-hooks`（观测中间件，本变更不改它）、`backend-bridge-agent` / `backend-bridge-sop`（消费方）。

## Capabilities

### New Capabilities

- `ae-harness-run-control`: 模型调用重试、运行预算、取消三件事的口径与边界。

### Modified Capabilities

- `ae-harness-observe-hooks`：中间件准入从「只有只读观测」扩为三类（只读观测 / 可靠性 / 运行控制），观测条款本身不变。

## Impact

- 代码：新增 `engines/ae_harness/middleware/{retry,control}.py`；`backend_bridge` 的 `session.py` / `workflow/roles.py` 增加可选控制参数。
- 依赖方向不变：`backend_bridge → ae_harness`。
- 行为默认不变：不传预算与取消令牌时，调用链与现在完全一致。
- 测试：新增 `tests/engines/ae_harness/unit/test_retry_middleware.py`、`test_run_control.py`。
