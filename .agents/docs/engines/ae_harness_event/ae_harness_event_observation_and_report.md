# ae_harness/event · 运行观测与报告
> 归属模块：`engines/ae_harness/event` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/event/record.py`、`engines/ae_harness/event/render.py`、`engines/ae_harness/event/render_aligned.py`、`engines/ae_harness/event/usage.py`、`engines/ae_harness/event/raw.py`、`engines/ae_harness/event/aligned.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

## 职责

为任意智能体提供**运行观测**：把 `reply_stream` 的事件记成结构化数据，再渲染成统一格式的报告。

```text
event/
  record.py         AgentEventRecorder：事件 → RunRecord + JSONL
  render.py         HtmlReportRenderer：RunRecord → HTML（过渡入口，未接对齐记录的路径仍在用）
  render_aligned.py AlignedReportRenderer：aligned.json → HTML（按官方内容块渲染，已接两条路径）
  render_blocks.py  报告渲染件：事实表 / JSON 高亮 / Markdown（四页签共用）
  usage.py          TokenUsage / UsageSummary / summarize：一次调用一条的用量记录
  raw.py            RawEventDump：事件 → 全量 raw.jsonl（实时流，调试用）
  aligned.py        AlignedRun：事件 → aligned.json（官方 Msg 结构 + 观测 + 信封）
```

## 报告渲染（两条入口）

| 入口 | 数据源 | 用在 |
| --- | --- | --- |
| `AlignedReportRenderer.save(document, path)` | 对齐记录的 `replies[].msg.content` | 助手对话、UI 执行智能体 |
| `HtmlReportRenderer.save(record)` | `RunRecord.steps` | SOP / goal / team（尚未产出对齐记录，过渡期保留） |

对齐入口的口径（对应 `ae-harness-report-render` 的四条新增需求）：

1. **唯一数据源是内容块**：报告正文按 `thinking` / `text` / `tool_call` / `tool_result` / `hint` 的顺序渲染，不再从事件行或步骤列表二次推导块内容。
2. **工具配对按块身份**：`tool_result.id` 与 `tool_call.id` 相同即同一张卡；结果缺失时单独成卡并标注「结果缺失」。
3. **未知块降级**：不认识的块类型渲染成通用区块（标题 + 原文摘要），不丢弃、不中断。
4. **用量与耗时取自记录**：`msg.usage` 与 `summary.cost_s`；缺失时显示「未知」，渲染期不再重算。
5. **视觉契约不变**：三层折叠（阶段 → 角色 → 内容块）默认收起、子目标手绘序号、字号三档、左栏三成可拖拽，均沿用 `render.py` 的样式与脚本。
6. **媒体**：按内容块里的 URL 读取后缩放内嵌（长边 1600、JPEG）；超过单图 4 MB 时退化为「只显示路径与尺寸」。
7. **空记录**：没有任何回复时报告显示「无内容」，不生成空壳分区。
8. **呈现口径（2026-11-25）**：正文与平台同一支 `HarmonyOS Sans SC`（同源加载 `/fonts/harmonyos-sans/`，`file://` 回落系统字体）；语义字段用 `render_blocks.facts()` 一行一条；JSON 用 `json_block()` 缩进高亮；模型文本用 `markdown()` 渲染。四页签共用这三件渲染件，口径见下节。



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

## 报告结构（五个页签）

| 页签 | 内容 | 回答什么问题 |
| --- | --- | --- |
| 报告 | 按内容块叙述（子目标 → 角色卡 → 内容块） | 这次跑出了什么 |
| 概览 | `run` 运行环境（字段一行一条）、`input` 输入条件（提示词全文/工具 schema/用户消息）、用量卡（token + 缓存命中条）、逐次调用宽表、结果（Markdown）、四条产物路径、schema 与事件数；SOP 记录额外一张「步骤结论」卡 | 这次跑的是什么环境 |
| 阶段 | 单角色：准备（序号 01）→ 每轮一个阶段（02…）→ 收尾；SOP：每步一个阶段（01…）→ 角色卡 → 轮次卡 → 收尾。阶段头复用手绘序号，阶段体为事实表 + 链路卡（推理 / 请求 / 返回 / 压缩 / 权限 / 执行） | 模型是怎么一步一步走的 |
| 事件流 | 每个事件一行头（时刻 + 类型徽章 + 事件名）+ 字段事实表；增量事件默认折叠、行内短值截断 | 原始流长什么样 |
| 原始记录 | `run` / `input` / （SOP）`steps` / `observations` / `summary` 分段成卡，段内 JSON 高亮缩进；小段默认展开，超 20000 字截断并注明 | 当时到底写了什么 |

四页签共用 `render_blocks.py` 的三件渲染件，禁止各页签各写一套：

| 渲染件 | 产出 | 用法 |
| --- | --- | --- |
| `facts(rows)` / `fact(label, value)` | `.facts` / `.fact`：标签 12px/700 + 「：」，值 14px，一行一条 | 运行环境、阶段事实、事件字段、步骤结论 |
| `json_block(value)` / `json_value(value)` | `.json`：缩进 + 键/字符串/数字/字面量四类着色；能解析的 JSON 字符串自动解析；超 20 行折叠 | 入参、结果、`state`、`wire`、原始记录 |
| `markdown(text)` | `.md`：标题/加粗/列表/表格/引用/代码渲染，`html=False` 转义原始 HTML | 最终文本、报告区文本与思考块、用户消息 |


阶段边界：单角色取自观测里的 `reply` / `reasoning`，**不依赖文本里的 `### 目标`**（模型不写标记也不会错位）；SOP 取自运行期步骤事件（见下节「SOP 的增量字段」），缺 `steps` 段时自动退回按轮。角色块用卡片样式 + 折叠箭头旋转，避免“看不出能展开”；SOP 的步骤卡在标题右侧带「通过 / 未通过」状态牌，未通过时卡内列出验收者给的失败说明与期望结果。

### 页头与步骤标题

页头是两段式：12px 品牌小标签 `AGENT 执行报告` + 24px 主标题，主标题取 `run.report_title`。取值为空时（例如本地调试直接渲染一份记录）只显示品牌标签，不显示空标题行。主标题单行省略、悬停可看全文，标题文本按 HTML 转义。任务侧的标题来自任务标题，助手侧来自会话标题（空则助手名），都由产出方在生成报告时写进记录，渲染层不查库。

报告区分组标题就是该步目标（`subject`），前面只有手绘序号，不再拼「第 N 步 ·」；正文文本块里作为导航标记的 `### 目标：…` 行会被剥掉，避免与分组标题重复。历史记录里 `subject` 若仍带「· 第 N 步」后缀，渲染时改用该步 `description` 里的「动作：」行作标题，保证同一序号只出现一次，也避免同一用例的多个步骤被同名合并成一个分组。分组按「第几步」而不是按标题文字归并。阶段页保持「第 N 步 · 目标」。

## 观测覆盖范围（对齐框架全部可观测位置）

`ObservationMiddleware` 接的是框架中间件提供的全部位置，只读、原样透传。`aligned.json` 的 `observations` 段按发生顺序记录：

| `kind` | 来源位置 | 记录什么 |
| --- | --- | --- |
| `reply` | `on_reply` | 整轮回复开始/结束、上下文条数、总耗时、输入消息条数与角色、是否要求结构化输出 |
| `reasoning` | `on_reasoning` | 每轮推理开始/结束、轮次号、`tool_choice`、耗时，并附 **状态快照**（`session_id`、`reply_id`、上下文条数、计划任务全字段、压缩摘要正文、权限模式与规则计数） |
| `model_call` | `on_model_call` | 本次实际发送的消息全量（`capture_messages` 开启时）、消息条数、序列化字符数、可用工具名、`tool_choice`、当前模型、状态快照；**图片对账**：`framework_images`（框架消息里的图片数）、`images_sent`（实际发送数）、`images_dropped`（通道是否丢图），并在首次出现图片时附一份 payload 摘要 `wire` |
| `model_call_return` | `on_model_call` | 返回耗时、是否流式、失败原因 |
| `system_prompt` | `on_system_prompt` | 最终交给模型的 system prompt 全文与长度 |
| `compress_context` | `on_compress_context` | 压缩前后条数、是否真压缩、触发比例、上下文窗口、阈值、注入指令、耗时 |
| `acting` | `on_acting` | 工具名、入参、分片数、最终状态、耗时 |
| `permission` | `on_check_permission` | 工具名与权限判定结果（只读，不改判定） |

报告新增「链路」页签，按观测顺序渲染：回复 → 推理 → 请求（含 system prompt 全文与消息全量）→ 返回 → 压缩判定 → 权限判定 → 工具执行。链路视图不再从事件流反推输入，两者互补：事件表达「产出了什么」，观测表达「模型收到了什么、框架判定了什么」。

## 模型输入能力：以框架模型卡为准（视觉输入踩坑记录）

创建模型时 MUST 用 `ChatModelBase.list_models()` 取同名模型卡的 `input_types` 传给 formatter，未声明时回落到 `["text/plain"]`。**不传的后果**：formatter 的 `supported_input_media_types` 为空，所有图片块被静默丢弃——工具结果里的截图会被替换成一句「image file is returned and saved locally at: <本机路径>」，模型只看到路径，于是反复声明“看不到图”，转而用字节数与 md5 猜测页面。

官方模型卡口径（2.0.12）：`deepseek-flash` 声明 `text/plain + application/x-thinking + image/jpeg|png|gif|webp`；`deepseek-chat`、`deepseek-reasoner` 只声明 `text/plain`。链路页签的「图片(框架) / 图片(实际发送) / ⚠ 通道丢弃图片」三行就是对账入口。

## 对齐官方结构的运行记录（aligned.json）
`AlignedRun` 是运行记录的**主产物**：它按 AgentScope 2.0.12 的三层结构（`Msg` → 内容块 → 事件）组织一份 JSON，并用官方 `Msg.append_event()` 完成折叠——折叠逻辑不再由本仓库自己实现。

```text
logs/agents/assistants/<assistant_id>/<thread_id>/<时间戳>/
├── <时间戳>_<角色>.aligned.json   主记录：run / input / replies / observations / summary / events
├── <时间戳>_<角色>.jsonl          记录器：报告口径的块级折叠 + summary
├── <时间戳>_<角色>.raw.jsonl      实时事件流：一行一个框架事件，可 tail
└── <时间戳>_<角色>.aligned.media/ 事件里的图片按 sha256 落文件
```

文件结构（`schema: "agentscope.run/1"`）：

| 段 | 内容 | 对应官方概念 |
| --- | --- | --- |
| `run` | 角色、agent 名、模型、密钥环境变量名、serial / 助手与线程标识 | 无（本仓库信封） |
| `input` | `system_prompt`、`tool_schemas`、`user_message` | 模型输入条件 |
| `replies[]` | 每个 `reply_id` 一条：`{reply_id, agent, msg, unfolded}`，`msg` 是官方 `Msg`（`content` 为内容块列表、`usage` 为累计用量） | `Msg` + 6 类 Block |
| `observations[]` | 中间件钩子采样（`system_prompt` / `compress_context` / `model_call` / `model_call_return`） | 无（本仓库扩展） |
| `summary` | 耗时、最终文本、tokens、逐次 usages、三条产物路径 | 无（本仓库派生） |
| `events[]` | 全部官方事件按发生顺序排列（含 delta），`event_count` 为总数 | `AgentEvent` |

两条硬口径：

1. **折叠只走官方 API**：`replies[].msg` 由 `Msg.append_event()` 累积而成，单条事件折叠失败时记入该 reply 的 `unfolded`，不让整份记录失败。前端渲染与报告读取可以直接消费 `msg.content`，与官方「一个 Msg = 一条回复 = 一个气泡」对齐。
2. **图片以 URL 源留在事件里**：二进制写 `*.aligned.media/<block_id>_<sha256前8>.<ext>`，事件里 `data` 置空、`url` 指向该文件（`URLSource`）。这样事件仍然能被 `TypeAdapter(AgentEvent)` 重新校验，可回放；裸文件名或自定义 dict 会让官方 schema 校验失败。

接入范围：助手对话 `backend/apps/ai_assistant/services/assistant_threads.py` 的 `_reply`（`capture_messages=True` 常开）、UI 执行智能体 `engines/backend_bridge/session.py` 的 `run_turn`（由调用方经 `run_ui_task(..., capture_messages=True)` 打开）、SOP 编排 `engines/backend_bridge/workflow/bound_sop.py` 的 `run_bound_sop`（同样 `capture_messages=True`）。

### SOP 的增量字段（可选键，缺省即单角色口径）

SOP 一份记录里有两个角色、多个步骤，因此在对齐记录上**只加可选字段**（`schema` 仍是 `agentscope.run/1`，缺这些键时报告走单角色按轮逻辑）：

| 键 | 内容 |
| --- | --- |
| `run.roles[]` | `{name, role, model, api_key_env}`，`role` 取 `executor` / `verifier` |
| `run.report_title` | 报告页头主标题；任务侧写任务标题，助手侧写会话标题（空则助手名），缺省空串 |
| `input.roles[]` | 每个角色的 `system_prompt` 与 `tool_schemas`；`input.system_prompt` / `input.tool_schemas` 保留为单角色兼容位 |
| `replies[].role` | 该回复属于哪个角色，渲染器优先用它判断「执行者 / 验收者」，不再靠名字里有没有 `verif` 猜 |
| `steps[]` | `{index, subject, description, passed, attempts, message, expected, reply_ids}`；`subject` 是该步目标（动作），不带用例标题与序号；`reply_ids` 把回复挂到步骤上 |

步骤边界来自运行期的 `CustomEvent`（`SOP_STEP_STARTED` / `SOP_STEP_ENDED`），由 `bound_sop` 在事件流里计数并用 `AlignedRun.bind_step_reply()` 绑定回复；报告不再从回复文本里猜阶段。步骤结论（`passed` / `attempts` / `message`）只有 `run_sop` 返回后才知道，所以由调用方在 `run_sop` 结束后调 `AlignedRun.set_steps()` 再落盘——这也是 `run_sop` 只透出事件、把渲染权交回调用方的原因。

无 `msg` 的 `replies[]` 行是「未归属任何回复的事件」（例如步骤事件）的统计行，渲染器会跳过它，不参与侧栏「回复」计数。

## 实时事件流（raw.jsonl，调试用）

`RawEventDump` 把**每个框架事件**按原样逐行落盘，只服务 `tail` 与排障；观测记录现在只进 `aligned.json`，不再混进这条流。

```text
├── <时间戳>_<角色>.raw.jsonl      一行一个事件，首尾为 dump_begin / dump_end
└── <时间戳>_<角色>.raw.media/     事件里的图片按 sha256 落文件
```

每行固定五段：

| 字段 | 口径 |
| --- | --- |
| `seq` | 本文件内自 1 单调递增，含 `dump_begin` / `dump_end` |
| `at` | 框架事件的 `created_at`；事件没有时用本地钟 |
| `recv_ms` | 送达记录器的相对毫秒，**只用于排查滞后**（工具执行期间事件成批送达，`recv_ms` 与 `at` 能差出整段工具耗时） |
| `type` | 框架事件类名（`ToolCallDeltaEvent` 等），首尾两行为 `dump_begin` / `dump_end` |
| `fields` | 事件 `model_dump()` 的全量字段，**不截断、不挑字段**（`reply_id`、`block_id`、`tool_call_id`、`metadata`、`url` 全留） |

`dump_begin` 带本轮元信息（角色、agent、serial、模型、密钥环境变量名、工具 schema 清单、用户输入）；`dump_end` 带耗时、最终文本、summary、逐次 usages 与产物路径。

观测行（`kind`）仍在 raw 里可用——只要调用方把 `ObservationMiddleware.attach` 到 `RawEventDump.emit`；默认路径改为写 `aligned.json`，raw 保持纯事件流。

**图片 base64 不进任何 `.jsonl` / `.aligned.json`**：raw 里 `data` 换成 `{saved_to, chars, bytes, sha256}`（`inline_media=True` 才内联），aligned 里换成 `URLSource`。这不是放宽红线 3，而是把二进制挪到旁路。

## 红线（AI 禁止事项）

1. **禁止引用任何具体工具名** —— 工具特有的展示只能由调用方通过 `step_extras` 注册，不得写进本目录。
2. **禁止修改 Agent** —— 只读 `agent.state` 与事件流，不得调用 `reply` / `reply_stream` 之外的能力，也不得改变 Agent 行为。
3. **禁止在 JSONL 里写图片 base64** —— 图片只在 `RunRecord.steps[].images` 里停留于内存，日志保持十几 KB；`raw.jsonl` 同此口径，二进制落 `*.raw.media/` 并在行内留引用。
4. **禁止硬编码阶段标记** —— 正则必须可配置，本目录的默认值只服务一种约定。
5. **禁止把报告路径写死** —— 目录由调用方传入，本目录不假设仓库结构。

## 扩展点

`HtmlReportRenderer(step_extras={工具名: 渲染函数})`，渲染函数签名：

```python
def render_xxx(step: StepRecord) -> str: ...
```

返回值直接插入页面，函数内部自行转义。没注册的工具走默认展示。
