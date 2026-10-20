## Context

见 proposal.md 的 Why。约束来自现有规格，不在本次改写：`agent-role-billing` 的价目与取位、`agent-sop-runner` 的「按该次调用时刻分别计费后再求和」、`agent-dialogue-log` 助手块仍用 `input` / `output` / `cache_hit`。

现状：

- 最终消息的用量在 `Msg.usage`（`input_tokens` / `output_tokens` / `cache_input_tokens`）。一轮里的多次模型调用，以及上下文压缩，已由框架累加在这条消息上。
- `ModelCallEndEvent` 把同名字段铺在事件上，一条事件对应一次模型调用。压缩用量不会出现在这条事件上。
- `reply_usage` 只读消息上的 `usage`。`SopRunner._record_call` 与 `DialogueLog._on_ModelCallEndEvent` 各自 `getattr` 事件字段。
- `DeepSeekBilling.cost(model_name, input_tokens, output_tokens, cache_hit_tokens, created_at)` 位于 `engines/agents/billing.py`。`cache_creation_input_tokens` 不参与计价。

## Goals / Non-Goals

**Goals:**

- `ReplyParser.tokens(result)` 与 `ReplyStreamParser.tokens(event)` 在有用量时都返回 `tuple[int, int, int]`，顺序为输入、输出、缓存命中。
- 流式类对非 `ModelCallEndEvent` 返回 `None`，调用方据此跳过，不记一次调用。
- `SopRunner` 与 `DialogueLog` 改为消费这个三元组，费用仍逐次计算。
- `DeepSeekBilling` 整模块移入 `messaging`，计价函数签名与价目不变。

**Non-Goals:**

- 不把一轮流式事件加总成最终消息的用量。两条路径的合计不必相等：最终消息含压缩用量，结束事件不含。
- 不改 `print_result`、`render_reply_stream`、工具文本清洗三个函数的签名。
- 不改 `engines/ai`。不在旧路径保留 `engines.agents.billing` 再导出。

## Decisions

### 1. 两个类放在 `messages.py`，共用一个整数收口

`ReplyParser` 读 `result.usage` 上的三项。没有 `usage` 时返回 `(0, 0, 0)`。

`ReplyStreamParser` 以 `type(event).__name__ == "ModelCallEndEvent"` 识别结束事件，读事件自身的三项。其它事件返回 `None`。结束事件的字段缺失或为 0 时返回 `(0, 0, 0)`，与「没有这条调用」区分开。

两类都经同一个收口把值收成 `int(... or 0)`，避免一边用对象属性、一边用平铺字段后格式再分叉。不读取 `cache_creation_input_tokens`。

备选：流式类对非结束事件也返回 `(0, 0, 0)`。否决。调用方无法区分「这次调用用量为零」和「这条事件不是调用」，会把文本增量计成一次调用，违反 `agent-reply-usage` 与 `agent-sop-runner`。

备选：用 `isinstance` 对照 AgentScope 的事件类。否决。对话稿测试用的是同名假事件，类名判断与 `SopRunner` 现有写法一致。

### 2. 计费仍在调用方按次进行

解析类只出三元组，不调用 `DeepSeekBilling`。`SopRunner._record_call` 在 `tokens()` 非 `None` 时拆包，再按该事件的 `created_at` 与当次模型名调用 `cost`。`DialogueLog` 把三元组映射回助手块既有的 `input` / `output` / `cache_hit`，费用仍由运行器传入。

`reply_usage` 改为 `ReplyParser().tokens(result)`。`reply_cost` 仍先判断提供商是否为 deepseek，再把三元组和调用时刻交给 `DeepSeekBilling.cost`。`created_at` 缺省时继续取当前北京时间，不把 `None` 直接传给计费对象。

### 3. `billing.py` 作为 messaging 的叶子模块搬迁

文件内容与类 `DeepSeekBilling` 原样移到 `engines/agents/messaging/billing.py`，删除 `engines/agents/billing.py`。该模块只依赖标准库与 `chinese_calendar`，不 import `messages`、`dialogue`、`role`、`workflow`。

`messages.py` 改为 `from .billing import DeepSeekBilling`。`runner.py` 改为从 `..messaging.billing` 导入。`messaging/__init__.py` 导出两个解析类；不从包根再导出 `DeepSeekBilling`，避免 messaging 包初始化去拉计价依赖的方向变模糊。调用方直接 import 子模块。

`engines/agents/AGNETS.md`：计费说明从根目录文件清单移到 `messaging` 目录说明，写明模块为 `messaging/billing.py`。

## 模块防火墙自检

- 不涉及 `apps/` 跨 App import，不新增对 `service` / `runner` / `consumer` / `state_machine` 的跨 App 引用。
- 无 INSERT / UPDATE / DELETE，不经过也不绕过各 App 的 `api.py`。
- 前端不参与，不直连数据库，仪表盘无写操作。
- `engines/agents` 内部依赖方向：`workflow/runner.py` → `messaging`；`messages.py` → `messaging/billing.py`；`billing.py` 不反向依赖 `messages`、`role` 或 `workflow`。`messages.py` 继续不 import `role`。

## Risks / Trade-offs

- [把一轮结束事件加总后再计费，高峰跨时段会算错] → `tokens()` 只服务单条结束事件；`SopRunner` 保持逐次 `cost` 再累加。测试用高峰与空闲各一笔，断言合计等于两笔之和。
- [最终消息用量含压缩，与事件合计不一致，被当成解析错误] → 规格写明两条路径不互相重算。测试分别断言，不做两者相等。
- [搬迁后旧导入 `engines.agents.billing` 失败] → 不留再导出。仓库内调用点只在 `runner.py` 与 `messages.py`，一并改掉。
- [类名判断漏掉子类] → AgentScope 的结束事件类名固定为 `ModelCallEndEvent`，与现有运行器一致。

## Migration Plan

1. 将 `billing.py` 移入 `messaging/`，改 `messages.py` 与 `runner.py` 的导入，删除旧文件。
2. 增加两个解析类，并把 `reply_usage` / `reply_cost`、`SopRunner._record_call`、`DialogueLog._on_ModelCallEndEvent` 接到三元组上。
3. 更新 `AGNETS.md` 与 `messaging/__init__.py` 的导出。
4. 回退：把 `billing.py` 移回 `engines/agents/`，恢复三处字段读取与原导入。解析类可整段删除，`reply_usage` 回到直接读 `usage`。
