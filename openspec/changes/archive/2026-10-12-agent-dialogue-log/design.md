## Context

见 proposal.md - Why。过程日志仍由 `AgentProcessLog` 按天写入 `logs/sop-YYYYMMDD.log`。用量与费用已在 `SopRunner._record_call` 按次算好。对话稿是平行的另一份文件，不改这两处的对外行为。

## Goals / Non-Goals

**Goals:**

- 在 `engines/agents/messaging/` 新增一个模块，负责组块并追加 JSONL。
- SOP 运行时把已有事件和已算出的费用交给该模块，产物落在 `logs/agent_logs/`。

**Non-Goals:**

- 不生成 HTML，不改终端 `ConsoleRenderer` 输出。
- 不改 `logs/sop-*.log` 的行格式、按天切分和落点。
- 不把计费规则搬进新模块；费用由调用方传入。

## Decisions

### 新模块 `dialogue.py`，不扩展过程日志

对话稿的目录、文件粒度和行形状都和过程日志不同。放进 `process_log.py` 会把两种契约缠在一起。新模块只依赖同包的返回文本清洗，对外提供按块写入，以及消费 AgentScope 事件流的入口。

备选：继续只写过程日志，调试时自己解析竖线行。否决，因为组块、上下文拆分和信息栏都不是那份日志的职责。

### 一行一个 JSON 对象（`.jsonl`）

路径为 `logs/agent_logs/<run-id>.jsonl`。`<run-id>` 默认 `sop-` + 运行开始的北京时间 `YYYYMMDD-HHMMSS`，调用方也可传入。选 JSONL 是为了边跑边追加、用编辑器就能尾随；整份 JSON 数组每次都要重写文件。扩展名用 `.jsonl`，目录仍是用户指定的 `logs/agent_logs/`。

每行字段：

- 公共：`kind`（助手 / 工具 / 用户 / 上下文 / 汇总）、`ts`（`YYYY-MM-DD HH:MM:SS.mmm`）、`role`、`scope`（没有步骤时为空字符串）
- 助手：`content`、`model`、`tokens`（`input` / `output` / `cache_hit`）、`cost`、`duration_sec`
- 工具：`name`、`input`、`state`、`output`
- 用户 / 上下文：`content`
- 汇总：`calls`、`tokens`、`cost`、`duration_sec`

### 一次模型调用合成一块助手

思考增量和可见输出先缓冲，在该次模型调用结束时写成一块，并带上调用方传入的费用。耗时优先用调用开始与结束事件上的时刻之差；没有时刻则用本模块收到这两类事件的本地时间差；仍无法计算则为 `null`。这样信息栏和正文在同一行，调试时不用自己配对。

### 工具按调用标识配对，说明拆成上下文

`tool_call_id` 把入参和返回合成一块。返回文本里的 `<tool-instructions>...</tool-instructions>` 与 `<system-reminder>...</system-reminder>` 抽成紧随其后的上下文块，工具块的 `output` 不再包含这些片段。图片二进制不入文件，沿用现有「返回文本里的截图路径」清洗。

### SOP 只负责投递，不负责组块

`SopRunner` 在开跑时创建该模块实例（目录 `logs/agent_logs`），把启动输入写成用户块；步骤开始时再写一块用户块（正文为事件里的步骤名）。事件仍先走现有记录器写过程日志，再交给新模块。模型调用结束时把 `_record_call` 已经算好的三项费用之和传进去。运行结束写汇总块。写入异常吞掉并打 warning，与过程日志相同。

备选：让 `EventStreamRecorder` 内部再写一份。否决，因为费用和耗时不在那个记录器里，塞进去会让过程日志记录器依赖计费。

## 模块防火墙自检

- 不触碰 `apps/`：无跨 App import，无 ORM 写，无 `api.py` 调用。
- 新模块只位于 `engines/agents/messaging/`，SOP 运行器位于 `engines/agents/role/`，二者同属引擎包。
- 不新增前端，不写数据库，不改仪表盘。
- 费用数字由 `SopRunner` 传入，新模块不 import `billing` 以外的计费实现，也不 import 平台模块。

## Risks / Trade-offs

- [助手块要等该次模型调用结束才落盘，思考不能像过程日志那样逐段实时出现] → 调试实时性仍看 `logs/sop-*.log`；对话稿保证一块配齐信息栏。
- [工具返回格式变化导致说明拆不干净] → 只认约定的两个标签；认不出时整段留在工具块，不丢文本。
- [JSONL 被人手改坏一行会影响以后的 HTML] → 本次不读回这个文件；写入侧每行独立序列化。

## Migration Plan

无数据迁移。新目录首次运行时自动创建。回滚时停用 SOP 对新模块的调用即可，已写出的 `logs/agent_logs/*.jsonl` 可直接删，不影响过程日志。
