## Context

- 现状：执行与验收的编排是引擎自己写的循环（`workflow` 里的 `_run_step`：开日志窗 → 执行 → 读窗 → 验收 → 未通过则带 `actual` 回灌重试，最多 `max_loops` 次），步骤推进、重试计数、进度快照、失败收敛都由引擎维护。
- 依赖现状：已安装 `agentscope 2.0.7.post1`，**不含** `agentscope.sop`（实测 `ModuleNotFoundError`）；`requirements.txt` 写的是 `agentscope>=2.0.7.post1`（下限，非锁定）。
- 目标版本现状：`agentscope 2.0.9` 的 wheel 内含 `agentscope/sop/`（`__init__` / `_engine` / `_schema` / `_state` 四个文件）。已逐项核对 2.0.9 仍保留我们用到的全部导入面：`Agent` / `ContextConfig` / `ReActConfig`、三个凭证类、三个 ChatModel、消息块（`DataBlock` / `ThinkingBlock` / `ToolCallBlock` / `ToolResultBlock` / `UserMsg`）、事件流（思考 / 工具调用 / 工具返回 / 模型调用结束等）、`reply_stream(..., yield_final_msg=)`、`GoalPipeline` / `PipelineProtocol`。
- SOP 的关键形态（读 2.0.9 wheel 源码得到，非文档推测）：`SOPStep(subject, description, executor, verifier=None, max_attempts=3)`；执行者一次尝试必须交出 `_Handover`（**字段是 `handover: str`，只传文本**）；验证者给出 `_Verdict(passed, message)`；被驳回时交付清空并回到 `PENDING` 重做；`SOPEngine(sop, state)` 逐序推进并按 `SOPRunState` 推算 `SOPPhase`；执行者 / 验证者只需满足 `AgentLike`（即实现 `reply_stream` 的 `PipelineProtocol`）。
- 我们的角色不是裸 `Agent`，而是 `AgentRole` 包一层 `Agent`（装配提示词、工具子集、媒体落点、过程日志），对外是 `ask()` / 各角色 `run()`。

## Goals / Non-Goals

**Goals:**

- 执行与验收合成一个步骤单位，编排交给框架的 SOP；引擎不再维护同职责的自建循环。
- 保留平台特有职责与既有对外口径：步骤输入前缀、设备日志证据开窗 / 读窗、执行侧点击证据、验收关键词回填、按角色用量与费用、步骤过程记录的键、`logs/agents.log` 过程日志。
- 一次运行的状态成为可序列化数据，支持保存后续跑。

**Non-Goals:**

- 不改三角色的提示词输出契约（执行三字段 / 验收五字段）。
- 不改设备动作工具、元素定位、日志证据判定口径。
- 不引入 SOP 服务端形态（在线人工验收、跨进程队列）。
- 不把规划模型塞进 SOP 步骤：规划仍是运行前的输入生产者。

## Decisions

**D1 采用官方 SOP，而不是继续用自建循环。**
理由：这正是「执行 + 验收 + 驳回次数」的官方形态，且带可持久化状态与步骤级事件；文档与框架同源，后续升级不用再对齐自研语义。备选：保留自建循环（重复造轮子、状态不可续跑）。

**D2 依赖升级到含 SOP 的版本（当前 2.0.9），并把「升级可行性」作为第一步任务。**
理由：`requirements.txt` 本就是下限；已核对导入面保留。**不兼容时的回退路径**：停在 2.0.7，在引擎内自建同形步骤层（同名接口：步骤基类 / 步骤 / 引擎 / 运行状态），既有编排仍换成步骤化，只是实现归我们；将来升级官方 SOP 时替换实现层即可。备选：一直停在 2.0.7 直接自建（少一次升级，但失去官方状态模型与事件）。

**D3 执行者 / 验证者以 `AgentLike` 适配器接入，平台职责留在适配器内。**
理由：SOP 只要求 `reply_stream`，而我们的角色已经包了 Agent；适配器可以把「步骤输入前缀 + 日志证据 + 点击证据 + 关键词回填 + 用量聚合」全部留在引擎侧，同时满足框架契约。备选一：把 `AgentRole` 直接实现 `reply_stream`（角色基类被框架契约污染，且角色要感知 SOP 的交付 / 结论 schema）；备选二：用官方 `SOPStep` 的裸 `Agent`（丢掉我们全部平台职责，不可行）。

**D4 交付只传文本（框架限制），验收画面由验证者自己截图 + 既有证据块提供。**
理由：`_Handover.handover` 是 `str`，图片无法随交付传递；而我们的验证者本来就要求自己 `screenshot_page` 截一次，且日志证据 / 点击证据由平台装配。因此改造后验收的输入口径变为「交付文本 + 证据块 + 自截图」，与既有的「执行侧截图 + 证据块 + 自截图」相比少一张执行侧图片——需在回归里确认判定不退化。备选：把执行侧截图以 base64 塞进交付文本（污染交付、且与「日志不含二进制」的既有口径冲突，否决）。

**D5 步骤驳回上限对齐现有 `max_loops`。**
理由：不改变用户可见的重试次数语义；`max_loops` 继续由平台配置下发。

**D6 运行状态落点由调用方注入（沿用过程日志的注入方式）。**
理由：引擎零平台依赖；平台可把它与既有任务进度合并落库，落点与是否落盘由平台决定，本单只要求「可序列化 + 可重建」。

## 模块防火墙自检

- 引擎新增 / 改动只依赖 AgentScope 与标准库；运行状态与过程日志落点继续由 `TaskRequest` 注入，MUST NOT import 平台模块。
- 平台侧沿用既有 `engine_adapter` / `api.py` 路径，不新增跨 App import，不新增写库路径。
- 前端不参与本单（任务详情页与进度口径不变）。
- 无新增跨模块依赖。

## Risks / Trade-offs

- [升级 AgentScope 可能影响平台其它链路（模型调试页已退役，主要风险在引擎与工具装配）] → 第一步就是升级兼容性验证：装 2.0.9 后跑引擎与相关单测 + 一次真机冒烟；不通过则走 D2 的回退路径，不进入后续任务。
- [交付只传文本可能让验收判定退化（少一张执行侧截图）] → 回归项显式比较改造前后同一批步骤的验收结论；若出现退化，则把执行侧截图路径写进交付文本并在验收输入里附带该路径对应的图片（平台侧装配，不进交付）。
- [适配器把两套契约（我们的角色输出 schema 与框架的交付 / 结论 schema）绑在一起，容易出现「模型没给出结构化输出」的空交付] → 明确空交付与空结论都记一次驳回（框架语义），并在适配器里把我们的 JSON 解析失败如实转成「无交付 / 无结论 + 原因」，不编造结论。
- [挂起与恢复（工具授权 / 外部执行）在本平台的工具集里目前不触发，但升级后可能出现新的挂起点] → 本单只要求状态可序列化与重建；出现挂起时如实记为对应阶段，不强行续跑。
- [步骤定义与保存的状态不匹配会抛错] → 平台侧同一任务运行期间不允许重规划；如确需重规划则视为新运行。

## Migration Plan

1. 依赖升级与兼容性验证（导入面 + 引擎单测 + 真机冒烟）；不通过则回退并改走自建同形步骤层。
2. 引擎：新增执行者 / 验证者适配器；用 SOP 构建步骤并驱动 `SOPEngine`；手写重试循环退役。
3. 引擎：步骤级进度事件与运行状态接入既有 `on_progress`；任务结果与过程记录口径保持。
4. 平台：确认任务进度与结果落库口径不变；运行状态如需落盘，落点走注入。
5. 回归：引擎单测（推进 / 驳回 / 上限 / 状态往返）+ 平台任务链路单测 + 真机一次任务冒烟（含驳回重试一次）。

回滚：还原引擎的编排实现与依赖版本；任务数据与既有过程记录不受影响（改造前后记录键一致）。

## Open Questions

- 运行状态是否需要落盘到平台（与现有任务进度合并，还是仅内存 + 日志）：不影响本单规格与任务拆分，落地时按平台现状决定。
- 是否要把「上游步骤的交付」展示到任务详情页：本单不做（详情页仍只展示步骤与执行结果、证据）。

## 实施记录（2026-10-09 apply）

### 接入方式：官方 `SOPStep` + 两处文案钩子覆盖（不是自定义步骤）

`engines/ai/workflow/sop_step.py` 的 `ExecutionSOPStep` 继承官方 `SOPStep`，编排（按序推进、
驳回计次、用尽即失败）完全由 `SOPEngine` 负责；只覆盖两个「问什么」的钩子：

1. `_brief`：执行侧输入前缀（serial / 步骤序号 / 三字段契约 / `<feedback>` 回灌）本来就在
   `ExecutorRole.run` 里拼。框架默认提醒是英文 SOP 文案且会重复一遍步骤描述，会成为第二份
   指令；因此 `_brief` 只产出平台口径的重试段落，`ExecutorAdapter` 再从这段文本里取回灌原因。
2. `_question`：框架的交付契约 `_Handover.handover` 只有 `str`（设计 D4 已记录「图片无法随交付
   传递」）。执行侧截图（DataBlock）不在交付里，验收画面由验证者自己截图 + 平台装配的日志/
   点击证据提供，因此不把交付文本塞进验收输入。

**没有改成「继承 `SOPStepBase` 的自定义步骤」**：框架的交付 / 结论契约放得下我们的证据装配——
交付文本 = 执行三字段 JSON、结论 = `{"passed", "message": actual}`，而 `structured_schema=`
与 `yield_final_msg=` 两个关键字都被适配器的 `reply_stream` 接受。

### 平台事实的落点：`ExecutionStepState`（`state_type`）

`SOPStepRunState` 的引擎子类 `ExecutionStepState` 额外记执行三字段、验收结论、验证截图、
日志证据、点击证据（全部 JSON 可表达）。它随 `SOPRunState` 一起序列化；重建运行时不重放已完成
步骤也能读回这些事实（单测 `test_step_state_keeps_platform_facts_through_engine_rebuild`）。
运行中的可变黑板（含 DataBlock 句柄与用量基线）另放 `StepAttemptSink`，不与持久化状态混在一处。

### 与设计的偏差（如实记录）

1. **交付只剩文本，截图不在交付里**：`_Handover.handover` 是 `str`，因此 `state.submission`
   只有 `TextBlock`（执行三字段 JSON），不含 DataBlock；执行侧截图仍由平台的验收输入口径提供
   （`sink.exec_screenshot` 直接进 `VerifierRole.run`），与 D4 的预判一致。
2. **状态里的步骤记录类型不随 `model_dump_json` 往返**：`SOPRunState.steps` 声明为
   `SerializeAsAny[SOPStepRunState]`，`model_validate_json` 还原成基类实例（额外字段因
   `extra="allow"` 仍在）。真正的类型还原发生在 `SOPEngine.__init__`（按 `state_type` 逐条
   `model_validate`），因此续跑路径没问题；但外部若直接读 `model_validate_json` 的结果，
   拿到的是基类实例。
3. **续跑的第一轮会重跑该步的第一次尝试**：框架语义是「没写结论的尝试不算数」，上次被驳回后
   保存的状态里 `submission=None`、`verifications` 已有条目，重建后仍从新的一次执行开始
   （进度、尝试序号的连续性由 `verifications` 条数承载）。
4. **运行状态落盘未接**：`DeviceExecutionWorkflow(run_state=...)` 已可注入与续跑，
   `engine.py` 目前仍传空（D6 说落点由平台注入）；平台侧接续跑不在本单范围内。

