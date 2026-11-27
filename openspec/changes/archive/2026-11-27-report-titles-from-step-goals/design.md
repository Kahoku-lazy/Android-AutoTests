## Context

- 报告页头是渲染器里写死的一行 `<h1 class="wb-title">AGENT 执行报告</h1>`（`engines/ae_harness/event/render_aligned.py`），渲染时只拿得到 `document`（`run` / `input` / `replies` / `summary` / `steps`），渲染器不碰数据库。
- 两条产出链写进 `run` 的字段都不含标题：任务报告是 `role / agent / model / api_key_env / serial / sop_name / sop_description / roles`（`bound_sop._run_meta`），助手报告是 `role / agent / model / api_key_env / assistant_id / thread_id`（`assistant_threads`）。侧栏「任务」框显示的是 `input.user_message`，在任务报告里是「本次要操作的设备 serial 是…」。
- 步骤名有两个编译入口，都把 `subject` 拼成「用例标题 · 第 N 步」：平台用例 `case_manager.api_rows.compile_automation_cases`、评测题库 `eval.case_run.compile_case_yaml`。而 `agent-sop-workflow` 规格写的是「`subject` 是执行角色这一步要做的动作」——当前实现与规格背离。
- 模型自述的 `### 目标：` 行不是可靠标题源：本机两轮快照用例（4 步）里出现 1 次缺失、1 次残留上一步目标；音乐用例（5 步）恰好全对。所以它只能做参考，不能当唯一来源。

## Goals / Non-Goals

**Goals:**

- 页头能看出这份报告属于哪个任务 / 哪个会话，且不打断品牌观感。
- 报告区每一步的标题提供区分信息（该步要做什么），序号只由手绘徽标表达一次。
- 旧记录与新记录都只显示一个步骤号，不出现「第 N 步…第 N 步」。
- 步骤 `subject` 回到规格已定义的语义，下游（任务摘要、BUG 单、评测提示词）一并变干净。

**Non-Goals:**

- 不改阶段页标题格式（仍是「第 N 步 · 步骤名」）。
- 不加「模型自述目标 vs 步骤目标」的偏差标记（后续单独立项）。
- 不改前端报告列表、不改报告的内容源与页签结构。
- 不重写已落盘的历史报告 HTML。

## Decisions

**D1 页头用方案 C：品牌小标签 + 主标题。** 12px 手写体 `AGENT 执行报告` 作 kicker，24px 手写体主标题跟在其后，通过状态与五个页签位置不变。备选 A（主标题同行 14px 副标题）层级弱、备选 B（整行替换品牌）会丢失品牌识别，均不采用。

**D2 标题内容走 `run.report_title`，取值有回退链。** 任务报告：`task.title` → 为空取 `case_title` → 再空取空串；助手报告：`thread.title` → 为空取助手 `display_name` → 再空取空串。不用 `input.user_message`：任务报告里它是 serial 开场说明，助手报告里是用户那句话，长度与语义都不像标题。

**D3 标题在生成报告时写进记录，而不是渲染时查库。** 报告是自包含 HTML，离开平台也要能读；渲染层保持零 DB、零 `django` 依赖（`engines/` 红线）。为此 `run_bound_sop` 增加可选入参 `report_title`，`_run_meta` 写进 `run`；助手侧在 `AlignedRun.begin` 的 dict 里直接补字段。

**D4 步骤 `subject` 改为该步动作，用例标题挪到 `description` 首行。** 两个编译入口都改成「去 `动作：` 前缀 + 压成单行」；`description` 首行加 `用例：<标题>`，动作 / 断言 / 页面锚点原样保留，验收语义不变。这是把实现改回 `agent-sop-workflow` 已规定的语义，不是新规则。

**D5 渲染层做兜底与历史兼容。** 新增 `_step_goal(step)`：`subject` 不带尾缀时直接用它；带「 · 第 N 步」尾缀（历史记录）时改用 `description` 的「动作：」行，缺该行再退回去掉尾缀的文本；`subject` 为空回退「第 N 步」。报告区标题不再拼 `第 {position} 步 · `，阶段页由 `_stage_step_title()` 拼「第 N 步 · 目标」。分组键改成步骤序号（`step:{position}`）而不是标题文字，避免两步同名时被并成一卡。正文文本卡里 `### 目标：…` 行用 `_GOAL_LINE` 剥掉（已绑定步骤的回复也要剥），避免标题与正文各说一遍。

**D6 页头溢出规则。** 主标题 `white-space: nowrap` + `max-width` + `text-overflow: ellipsis`，`title` 属性给全文；品牌小标签 `12px`、主标题 `24px`，分别落在「字号三档」的 12px 与页头档位。

**D7 兼容范围。** 旧 `*.html` 不重写；只有被重新渲染的记录（新运行）会用到新规则。旧 `.aligned.json` 若被再次渲染，D5 的「动作行兜底」保证不出现双序号、也不会把同一用例的多步并成一卡。没有 `report_title` 的旧记录（含旧渲染器）仍显示 24px 品牌标题，与改动前一致。

## 模块防火墙自检

- 新增 `run.report_title` 只是运行记录里的一个字段：`task_runner` 通过既有 `run_bound_sop(...)` 入参传入，`engines/` 不 import `django` 与 `apps.*`。
- 助手侧改动在 `backend/apps/ai_assistant/services/assistant_threads.py` 内，读写自身 `AIAssistantThread` 字段，不新增跨 App import。
- 渲染层仍是纯函数：无 DB、无跨模块调用。

## Risks / Trade-offs

- [任务标题常等于工作流名，可能与用例名不同] → 回退链优先任务标题（与列表行一致），缺失才用用例标题；如需强制用例名，后续只改取值优先级。
- [旧记录的下游文案（任务摘要 / BUG 单）里的 subject 仍带后缀] → 本次只在报告渲染层剥离；新运行的记录已干净，旧记录不重算，避免触碰历史数据。
- [模型自述目标与步骤标题不同步] → 明确接受：标题以步骤目标为准，自述只作为过程文本；需要偏差可视化时另立变更。
- [长中文标题在手写体里读起来偏花] → 单行省略 + `title` 全文；不会换行挤压页签。

## Migration Plan

- 无库表迁移：`run.report_title` 只存在报告记录文件里。
- 上线即生效于新生成的报告；回退 = revert 本单提交，已生成 HTML 不受影响。

## Open Questions

- 页头是否同时露设备 serial（例如主标题右侧的 12px 灰字）——等页头标题落地后再看，不影响本单。
