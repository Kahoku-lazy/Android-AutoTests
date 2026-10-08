# 设计：规划输出去掉 goal 字段

## Context

- **契约现状**：`Plan`（`engines/ai/workflow/workflow.py:69-73`）= `goal: str = Field(default="")` + `steps: list[Step]`；`Step` = `action` + `assert`（alias `assert`）+ `log_check`。`WorkflowResult.plans` 直接放 `plan.model_dump(by_alias=True)`。
- **提示词现状**：`PLANNER_PROMPT` 的「输出字段」列了 `goal` 与 `steps`；「案例」示例为 `{"plan": {"goal": …, "steps": […]}}`。
- **`goal` 的消费方（实测全仓）**：
  - 引擎内**无任何逻辑**依赖 `plan.goal`（只有 `Plan` 定义处与我的评测工具 `plan_text()`）；
  - 前端 `helpers/task-detail.ts`：`planGoalText()` = `plan?.goal || detail?.goal || ""`（详情页副标题），以及旧协议分支用 `plan.goal` 兜底合成一步；两者**都已有回退**；
  - 前端类型 `shared/types/ai.ts:278` 的 `TaskRunPlan.goal: string`；
  - 存量任务记录的 `plans[].goal` 仍在数据库里。
- **规格现状**：`ai-platform-task` 的场景写着"planner 产出至少一个 GoalPlan（含 goal/steps/verification）"——其中 `verification` 早已不在契约里（历史遗留），`goal` 本次要去掉。
- **同名概念要分清**：输入侧 `TaskRequest.goal`（四键 JSON 的「任务目标」）与任务表 `goal` 字段是**需求本身**，本单不动。
- 已知既有行为：pydantic v2 默认 `extra='ignore'`，模型若仍输出 `goal` 会被忽略而不报错。

## Goals / Non-Goals

**Goals:**

- 规划输出契约只含 `steps`：提示词、契约、规格三处一致。
- 存量记录与旧协议仍然可读（前端不报错、不空白）。
- 评测口径随契约收紧（关键词必须在步骤里出现）。

**Non-Goals:**

- 不动输入侧目标（`TaskRequest.goal` / 任务表 `goal` / 四键 JSON）。
- 不改 `Step` 的字段与 `log_check` 语义、不改执行 / 验收契约。
- 不为"模型偶尔仍输出 goal"加校验或报错（默认忽略即可）。
- 不清理前端旧协议分支（`legacyStringSteps` 等）——属既有兼容逻辑，本单只让类型如实。

## Decisions

**D1 只删输出侧的 `goal`，输入侧一概不动。**

两个 `goal` 语义不同：输入侧是需求，输出侧是回述。只删后者；`proposal.md` 与本设计都显式写明，避免实现的同学误改输入链路。

**D2 从 `Plan` 删除字段，而不是保留可选空字段。**

保留可选字段会让 `plans` 载荷与前端类型里永远挂着一个恒为空的键，等于没删。删除后模型若偶发输出该键，pydantic 默认忽略，解析不受影响。

**D3 前端类型放宽为可选，渲染逻辑不改。**

存量记录仍有 `plans[].goal`；把类型改成必填就是在对旧数据说谎，改成可选既如实又保住旧记录显示。渲染侧 `planGoalText()` 的回退链（plan.goal → 任务目标）已存在，新记录自动落到任务目标，页面不会空白——故本单**不改渲染逻辑**（改它反而增加风险）。

**D4 规格 delta：整块 MODIFIED，且不改场景名。**

上一次归档时踩过坑：`openspec archive` 把"改场景名"判为丢场景而拒绝。故本单原样保留场景名（`单目标平台任务` / `失败重试`），只改需求正文与场景内文；同时顺手删掉早已不在契约里的 `verification` 表述——把那句错话留在规格里，等于下次又有人按它实现。

**D5 评测工具的关键词口径收紧为"只看 steps"。**

`plan_text()` 原先把 `goal` 也拼进比对文本；删掉 goal 后若仍拼它只会得到空串。改为只拼 `steps` 的 `action` 与 `assert`——这意味着"关键词必须真的出现在步骤里"（比原先更严格，属预期收紧）。

## 模块防火墙自检

- 跨 App import：无（引擎内部契约 + 前端类型 + 评测工具）。
- 写库路径：零写库；无迁移（存量记录不动）。
- 前端：只改类型声明，不改请求与渲染逻辑；无新增 HTTP 出口。
- 引擎边界：改动在引擎内部契约与其提示词常量，不新增对外依赖。

## Risks / Trade-offs

- [存量任务的详情页副标题变空] → 回退链已存在（D3）；关单时以"包含 goal 的旧 plans 载荷"为输入核对渲染路径（前端既有用例 `task-detail.spec.ts` 的 fixtures 本身就带 goal，可作证据）。
- [模型仍输出 goal 导致解析失败] → pydantic 默认忽略未知键；另在单测里断言"带 goal 的模型输出仍能解析出只含 steps 的 Plan"。
- [规格改场景名被归档拒绝] → D4：保留场景名，仅改正文与场景内文。
- [评测用例因口径收紧而失败] → 属预期：删掉 goal 后关键词必须在步骤里出现；关单时实跑一遍评测，若某用例关键词确实只曾出现在 goal 里，则**修用例期望**（而不是放宽口径），并在用例注释里写明原因。
- [误改输入侧 goal] → D1 + 关单核对：`TaskRequest.goal`、四键 JSON、任务表字段的 `git diff` 必须为空。

## Migration Plan

1. 提示词（输出字段 + 案例）→ 契约（`Plan` 删字段）→ 评测工具（`plan_text`）→ 前端类型（可选）。
2. 同步测试：4 个后端用例文件的 `Plan(goal=...)` 构造 + 评测单测。
3. 规格 delta。
4. 验证：相关单测、评测实跑（确认端到端仍通过）、`manage.py check`、ruff、边界检查、前端 typecheck 与相关 vitest。
5. 回滚：纯代码改动、无数据迁移；`git revert` 单次提交即可（旧记录本来就兼容）。
