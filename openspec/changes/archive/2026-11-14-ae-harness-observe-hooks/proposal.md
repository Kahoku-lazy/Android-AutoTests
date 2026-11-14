## Why

事件流能看到「说了什么、调了什么工具、花了多少 token」，但**看不到两件最影响判断的事**：这轮是否压缩过上下文（模型为什么突然忘了前面的事），以及本轮实际组装的 system prompt 是什么（它为什么这样理解任务）。AgentScope 为这两件事提供了 hook，但 `engines/ae_harness/` 一个中间件都没接，导致「智能体做了什么」在关键处是断的。

## What Changes

- 新增 `engines/ae_harness/middleware/` 的**只读观测中间件**：实现 `on_compress_context` 与 `on_system_prompt` 两个 hook，只采样、不改行为。
- `create_agent` 增加**显式观测入参** `observers`，与能力型中间件分开命名；内部只透传给 `Agent(middlewares=...)`。
- 事件层新增 `observations` 入参：把中间件采到的记录写进 JSONL，并挂到 `RunRecord` 上，使观测产物可独立读取、不依赖内存对象。
- 4 个既有入口改为：建观测中间件 → 传给 `create_agent` → 把采到的记录交给记录器。
- `agents/AGENTS.md` 的「装配方式」补上实际入参名；`middleware/__init__.py` 登记导出。

**不做的**：不做能力型中间件（重试、路由、记忆、预算、工具扩展）；不改变任何 hook 的返回值；不采集 `on_model_call` / `on_acting` / `on_reply`（事件流已覆盖）。

## 关联文档

- 需求来源：需求方直接决策——放宽 `agents/AGENTS.md` 红线 2，只放开**只读观测**中间件；观测信息要能回答「智能体运行中做了什么」。
- 平台依据：AgentScope 2.0.9 的中间件 hook（`on_compress_context` / `on_system_prompt`），文档 `building-blocks/middleware`。
- 受影响主 spec：新建 `ae-harness-observe-hooks`。
- 相关既有能力：`ae-harness-token-usage`（同一份 JSONL 与 `RunRecord` 增加一种事件行）、`agent-middleware-assembly`（正式链路 `engines/agents` 的中间件装配，口径不冲突：那边是能力型，这边只读）。

## Capabilities

### New Capabilities

- `ae-harness-observe-hooks`: 在 `engines/ae_harness/` 里为「事件流看不到的两处」提供只读观测，并把采集结果落进既有运行产物。

### Modified Capabilities

无。`ae-harness-token-usage` 的需求不变（JSONL 与 `RunRecord` 只是多一种记录类型，其本身的结构要求不受影响）。

## Impact

- 代码（全部在 `engines/ae_harness/` 内）：
  - 新增 `middleware/observer.py`（观测实现）、修改 `middleware/__init__.py`（导出）
  - 修改 `agents/creator.py`（`observers` 入参）
  - 修改 `event/record.py`（`observations` 入参、观测记录落盘、`RunRecord.observations`）
  - 修改 4 个入口：`assistant/agent_executor.py`、`assistant/agent_verifier.py`、`workflow/sop/runner.py`、`workflow/sop_runner.py`
  - 修改 `agents/AGENTS.md`（装配方式写明 `observers`）
- 依赖方向：`event → middleware`（消费记录）；`middleware` 不导入同包任何模块；`agents` 不导入 `middleware`，只接收一个列表。
- 兼容性：`observers` 默认空、`observations` 默认空，不传时行为与改造前一致。
- 数据量：`on_system_prompt` 按需求存**全文**，每轮约几 KB；一次 5 轮运行约 30 KB，JSONL 会明显变大，属明确取舍。
- 测试：新增 `tests/engines/ae_harness/unit/test_observer.py`；扩展 `test_creator.py`、`test_record_usage.py`。
- 数据与接口：不动数据库、不动后端 API、不动前端。
