# engines/ae_harness/event AGENTS.md

## 职责

为任意智能体提供**运行观测**：把 `reply_stream` 的事件记成结构化数据，再渲染成统一格式的报告。

```text
event/
  record.py   AgentEventRecorder：事件 → RunRecord + JSONL
  render.py   HtmlReportRenderer：RunRecord → HTML
  usage.py    TokenUsage / UsageSummary / summarize：一次调用一条的用量记录
```

## 用量采集口径

1. **一次模型调用一条**：每次模型调用结束产出一条 `TokenUsage`，同轮多次调用各自成条，**禁止**合并或加总。
2. **缓存是输入的子集**：`cache_input_tokens` 已含在 `input_tokens` 里，汇总时**禁止**把两者相加；`cache_creation_input_tokens` 单独统计，不进其它三项。
3. **密钥绑在角色上**：`role_api_keys` 是「agent 名 → 密钥环境变量名」的固定绑定；每次模型调用按 `reply_id` 反查它属于哪个角色，再取该角色的密钥。**禁止**按 reply 顺序猜角色、也**禁止**给整轮安一个标签。只记环境变量名，**禁止记录密钥明文**。
4. **落盘可复算**：逐次调用的密钥名写进 `ModelCallEndEvent` 行，汇总行写 `api_key_env`（兜底值）与 `by_api_key_env`（实际分组）。只读 JSONL 就能按密钥复算，不必依赖内存对象。
5. **本层不读配置**：绑定由创建层产出后传入，本层**禁止** import `agents` 或读配置文件（保持观测层零内部依赖）。角色未登记绑定时回落到兜底标签，其余照常产出。
6. **时间不伪造**：绝对时刻由本轮起始墙钟加相对偏移算出；起点未知时给空串，**禁止**用当前时间冒充。

每轮任务一个目录：

```text
logs/20261113_143234/
├── 20261113_143234_ui_executor.jsonl
└── 20261113_143234_ui_executor.html
```

## 记录保真度（全量模式）

`AgentEventRecorder(..., full=True)`，**默认开启**。全量模式 = **字段全 + 不截断 + 仍按块折叠**。

| 项 | 全量模式 | 关闭后 |
| --- | --- | --- |
| 每条事件行 | 补 `created_at`（框架绝对时刻）、`event_id`；`metadata` 非空才写 | 不写 |
| `ReplyStart` / `ReplyEnd` | 补 `session_id` | 不写 |
| `HintBlockEvent` | 补 `source`，`hint` 不截断 | 只写 `hint`，截断 200 |
| 思考块正文 | 不截断 | 截断 600 |
| 工具入参 / 输出 | 不截断 | 截断 4000 |
| 文本块文本 | 不截断 | 截断 4000 |
| `*DeltaEvent` | **仍不落逐条**，只在内存累积成块级结果 | 同左 |
| **关联键** | `tool_call_id`（调用行/结果行）、`block_id`（思考块/文本块行）**两种模式都写**，与开关无关 | 同左 |

判断依据来自实测：一次普通任务 175 条事件里，思考增量占 **80%**，所以「全量」不等于「逐条落 delta」。取不到的字段**不写**，不写空串。

关联键是**身份不是补充**：没有 `tool_call_id`，一次并发多工具的调用与结果只能靠顺序配对，会错配；没有 `block_id`，块无法回溯到框架事件。因此它们不受开关控制。

## 红线（AI 禁止事项）

1. **禁止引用任何具体工具名** —— 工具特有的展示只能由调用方通过 `step_extras` 注册，不得写进本目录。
2. **禁止修改 Agent** —— 只读 `agent.state` 与事件流，不得调用 `reply` / `reply_stream` 之外的能力，也不得改变 Agent 行为。
3. **禁止在 JSONL 里写图片 base64** —— 图片只在 `RunRecord.steps[].images` 里停留于内存，日志保持十几 KB。
4. **禁止硬编码阶段标记** —— 正则必须可配置，本目录的默认值只服务一种约定。
5. **禁止把报告路径写死** —— 目录由调用方传入，本目录不假设仓库结构。

## 扩展点

`HtmlReportRenderer(step_extras={工具名: 渲染函数})`，渲染函数签名：

```python
def render_xxx(step: StepRecord) -> str: ...
```

返回值直接插入页面，函数内部自行转义。没注册的工具走默认展示。
