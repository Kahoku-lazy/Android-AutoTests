## Context

执行链路的现有治理是三层的：单步 token 预算（一次答复 600,000 加权 token）→ 一次答复的 ReAct 轮次（`max_iters=60` + `structured_output_grace_iters=5`）→ 任务级运行预算（600 次模型调用 / 7200 秒）。动机见 `proposal.md - Why`。

关键约束：

- 第一层由 `engines/agents/middleware/budget.py` 装配 `ReplyBudgetControlMiddleware`；耗尽时它在 `on_reasoning` 里把 `tool_choice` 覆盖为 `none`，而 SOP 引擎在结构化输出未满足时会持续要求调用 `GenerateStructuredOutput`。两者优先级由中间件包在内层决定，仓库无法通过配置调和。
- 第三层是仓库自己的 `event_sink` 计数，与中间件无关，语义是「整轮停」。
- handover 的唯一入口是执行者提示词（`config/data/prompts/UI_EXECUTOR_PROMPT.md`），由 `role_sys_prompts.py` 加载；字段名 `handover` 由 agentscope 的 `_Handover` 模型定义，属于外部依赖，不随本变更修改。
- `handover_self_declares_incomplete` 的退回词表不含「未达成」（已有单测 `tests/graybox/unit/test_handover_guard.py` 断言），所以「如实写未达成」不会触发退回。

## Goals / Non-Goals

**Goals:**

- 删掉单步 token 预算，消除「禁用工具」与「必须交卷」的互斥死锁。
- 让单步收敛只由轮次决定，并把这条口径写进规格与提示词，避免下次再被当作「调个参数」处理。
- 把 handover 收窄成执行者能稳定交付的两块：操作步骤（含 `action_time` 原文）+ 最终结果。
- 保持任务级兜底与 handover 守卫不变，降低回归面。

**Non-Goals:**

- 不改 agentscope 的 SOP 引擎、`_Handover` schema、守卫的退回词表与退回次数。
- 不调整 `max_iters` / `structured_output_grace_iters` 的数值，也不新增环境变量开关。
- 不改任务级预算（`SOP_MAX_MODEL_CALLS` / `SOP_MAX_RUN_SECONDS`）。
- 不改事件折叠、计费、前端任务清单与报告展示。

## Decisions

### 1. 删除预算模块，而不是给它加开关或改收场策略

备选与取舍：

- **撞线后放行一次「无工具交卷」**：需要在 `ReplyBudgetControlMiddleware` 之后覆盖 `tool_choice`，等于与外部库的中间件顺序博弈；且预算仍会在第 7–14 轮禁掉所有操作工具，正常步骤照样做不完。
- **保留但不强制 `none`（改 `auto`）**：工具可继续调用，预算就退化成一条无效提示，留着只会误导。
- **删除**：单步收敛本来就该由轮次表达；删掉后不存在「工具被禁但必须交卷」的状态。

因此删除 `budget.py`、装配项、包导出与 `.env.example` 中的变量说明。环境变量退役不报错、不生效。

### 2. 单步上限沿用 60 轮（+5 轮结构化宽限）

实测 TASK-177 的 step2「预约定时」正常通过用了 34 轮，若降到 30 会误杀正常长步骤；60 是本仓库既有取舍（`executor-handover-guard` 规格已要求 `max_iters >= 60`）。本次不改数值，只把「轮次是唯一单步上限」写进规格与设计说明。

### 3. 任务级运行预算保持不动

它与单步语义正交，只在整轮失控时触发；TASK-177（255 次调用 / 923 秒）并未触发，说明它没有造成本次失败。保留它可以避免「删了单步预算后完全没有总量兜底」。

### 4. handover 只写两块，且与守卫词表对齐

格式（写进提示词）：① 本步做了什么——每次点击 / 长按 / 拖动的 `action_time`（工具返回原文），按序逐条，含输入或开关改动；② 最终结果——「达成」或「未达成」开头，一句话写清设备与页面状态。

保留「未完成 / 尚未 / 未点击 / 请下一步」禁令：这些词仍会被 `IncompleteHandoverGuard` 退回；而未达成时改用「未达成」，既如实、又不触发退回。这样「如实交卷」与「守卫」不再互斥。

### 5. 只改提示词文件，不改 schema

`_Handover` 在 agentscope 内，改它等于改外部依赖；提示词才是模型实际读到的契约，也是 `role_sys_prompts.py` 的唯一真相源。

### 6. 删除两份未被引用的重复提示词副本

`config/data/prompts/EXECUTOR_PROMPTS_MD.md` / `VERIFIER_PROMPTS_MD.md` 与 `UI_EXECUTOR_PROMPT.md` / `UI_VERIFIER_PROMPT.md` 字节完全相同，全仓无引用。若只改前者不改后者，副本会立刻变成过期契约；因此随本次一并删除。

## 模块防火墙自检

- 跨 App import：无。本变更只在 `engines/agents/**`、`tests/**`、`.env.example`、`openspec/**` 内。
- 写库：无。不触碰任何 `api.py`、不新增 ORM 写入。
- 前端：无改动。
- 新增依赖：无。

## Risks / Trade-offs

- [单步最坏成本上升] 删除预算后，一次尝试可能跑满 65 轮 × 约 90k 输入 token ≈ 5.8M token → 任务级 600 次调用 / 7200 秒兜底仍在；轮次是硬上限，不会再出现「撞线后空转 52 轮」的死锁（本次 73% 的消耗正是它）。
- [长步骤触顶] 极少数步骤可能超过 60 轮 → 保留 5 轮结构化宽限；真触顶时按角色配置调 `max_iters`，而不是恢复 token 预算。
- [提示词与守卫再次漂移] → 单测断言两块结构与「未达成不被退回」，把口径钉在测试里。
- [旧变量残留] 部署机 `.env` 仍写着 `AGENT_REPLY_TOKEN_BUDGET` → 装配不再读取，无运行时报错；`.env.example` 删除说明，避免新人误以为有效。
- [文档滞后] 故障复盘文档记录了「预算 600k」的旧口径 → 复盘文档保留（历史证据），由本次规格与设计说明承接新口径。

## Migration Plan

1. 删除 `engines/agents/middleware/budget.py`，同步 `assembly.py` / `middleware/__init__.py`。
2. 改 `UI_EXECUTOR_PROMPT.md` 的 handover 段与自检条款；删除两份重复副本。
3. 更新 `.env.example` 与相关单测。
4. 跑 `tests/graybox/unit` 中中间件装配、模型重试、提示词纪律、handover 守卫四组单测；再跑一次真机短用例确认执行者能正常交卷。
5. 回滚：`git revert` 本变更提交即可（无数据迁移、无 schema 变更）。
