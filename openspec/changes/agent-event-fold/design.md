## Context

见 proposal.md 的 Why。当前 `DeepSeekBilling.cost()` 在返回前把三项金额收成 4 位 `float`。`AgentEventsShow.show(event, buf, models)` 用同一份缓冲写 `logs/agents/agent_events.log`，调用点只有工作流里的事件循环。`engines` 不得 import `apps`。

## Goals / Non-Goals

**Goals:**

- 一次模型调用只产生一组 8 位 `Decimal` 费用，日志打印与结构化记录共用。
- `show()` 签名不变。折叠无 I/O，接收方由调用方绑定；默认接收方丢弃记录。
- 行为以 `specs/agent-event-fold/spec.md` 与 `specs/agent-role-billing/spec.md` 为准。

**Non-Goals:**

- 不建表、不写 `apps`、不改仪表盘与 `apps/ai_assistant/deepseek_billing.py`。
- 不恢复角色上的计费入口。主规格里「角色按模型类型匹配计费」仍描述已不存在的调用路径，本设计不实现它。
- 不改 token 行的百万格式，不改思考 / 工具全文日志的措辞，只改费用数字的小数位。

## Decisions

### D1：费用返回 `Decimal`，量化到 8 位

`cost()` 继续用现有价目、高峰与节假日规则，精确金额用 `Decimal` 计算，再 `quantize` 到 `0.00000001`（`ROUND_HALF_UP`），返回 `(Decimal, Decimal, Decimal)`。日志用这组数格式化成 8 位小数加「元」。

备选：日志仍打印 4 位、记录保留 8 位。否决。那是两套展示，小额在日志里仍会变成 0，和「只算一次」的对账目的相反。

备选：返回未量化的精确值。否决。规格要求固定 8 位，调用方不应各自取位。

### D2：一次分派，同时产出日志行和记录

新增纯折叠：输入一条事件和可变状态，输出本条要写的日志行、要交出的记录，以及拼完才出现的图片 base64。`show()` 只做三件事：调用折叠、`write_line`、把记录交给已绑定的接收方。

缓冲键从 `show()` 的各个分支收进折叠状态。外部仍传入同一个 `dict`，`show(event, buf, models)` 不用改调用方。

备选：在现有每个分支末尾直接组记录。否决。分派会写两遍，`messages.py` 会超过单职责，折叠也无法脱离日志做测试。

### D3：模块边界

| 模块 | 职责 |
| --- | --- |
| `engines/agents/messaging/billing.py` | 价目与 `cost()`，返回 8 位 `Decimal`。另提供本次取价快照（模型、三项单价、倍率、是否高峰），供记录带走，不在这里写存储 |
| `engines/agents/messaging/record.py` | 结构化记录的数据结构，无 I/O |
| `engines/agents/messaging/fold.py` | 状态与 `step`：20 类事件的落与不落、角色继承、增量拼接、日志行文本 |
| `engines/agents/messaging/messages.py` | `AgentEventsShow` 编排；`ReplyStreamParser` 仍留在此文件 |
| `engines/agents/event_sink.py` | 接收方协议、`bind_sink` / 取当前接收方、默认空实现 |

折叠不读取任务号。`task_id`、`step_seq` 由以后的平台接收方在交出时从上下文盖上。本变更的空接收方不盖这些字段。

### D4：接收方失败不打断运行

`show()` 调用接收方时捕获异常，写一条警告日志，然后返回。文本日志在调用接收方之前写出，避免接收方失败把已确定的日志行吃掉。

### D5：图片只在结束记录上交出

数据块与工具返回的 base64 在折叠状态里拼接。结束记录把媒体类型和完整字符串交给接收方。文本日志继续只写类型和长度。本变更不做缩略图、哈希或去重。

## 模块防火墙自检

- 不新增跨 App import。折叠与计费只在 `engines/agents` 内。
- 不 import 其它 App 的 service / runner / consumer。
- 本变更没有 INSERT / UPDATE / DELETE。
- 不改前端，不改仪表盘。
- 接收方协议定义在引擎，平台实现留到后续落库变更，由任务运行器绑定，避免引擎依赖 `apps`。

## Risks / Trade-offs

- [费用行从 4 位变成 8 位，对照旧日志的脚本会失配] → 措辞不变，只放宽小数位；测试改为断言 8 位文本。
- [主规格「角色按模型类型匹配计费」的示例仍是 4 位结果] → 角色已不再计费，本变更不改该需求。以后若恢复，必须直接返回 `cost()` 的 8 位数，禁止再取位。
- [`apps/ai_assistant/deepseek_billing.py` 仍按 `float` 收到 4 位，且不算法定节假日] → 它只服务没有明细的历史任务。新链路不调用它，避免两套价目在同一次调用里混用。
- [折叠与日志行生成放在同一模块，文件变长] → 日志行是记录的投影，拆出去会让同一事件的措辞和落行规则分开改。控制在折叠模块内，编排模块保持很薄。

## Migration Plan

无数据迁移。发布后新跑出的费用日志为 8 位。回滚时恢复 `cost()` 的 4 位 `float` 与只写日志的 `show()` 即可，没有库表要回退。
