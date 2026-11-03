## Why

2026-11-03 的 TASK-177（定时任务测试-01）失败暴露出单步 token 预算与 SOP 交卷契约互相打架：预算按 600,000 加权 token 计，执行者每轮都带截图，7–14 轮就撞线；撞线后中间件把 `tool_choice` 强制为 `none` 并注入「不要再调用任何工具」，而该步仍要求用 `GenerateStructuredOutput` 交卷。模型只能把工具调用写成正文里的 `DSML` 标记，框架不认，于是空转到 60+5 轮超限，三次尝试共烧掉约 801 万 token（占全任务 73%）后判失败。

同一份提示词把 handover 写成四段（做了什么、逐条证据、达成/未达成、阻塞与下一步建议），既与「禁止未完成措辞」的硬约束互相拉扯，也让执行者把轮次花在写复盘而不是做操作。

## What Changes

- **移除「单次回复 token 预算」**：不再按加权 token 禁用工具、不再注入收尾提示；`engines/agents/middleware/budget.py` 整体删除，装配入口、包导出与相关环境变量说明同步移除。**BREAKING**：`AGENT_REPLY_TOKEN_BUDGET` / `AGENT_REPLY_INPUT_WEIGHT` / `AGENT_REPLY_OUTPUT_WEIGHT` 三个变量退役，配置了也不再生效。
- **单步上限改为纯轮次控制**：执行者沿用 `max_iters=60` + `structured_output_grace_iters=5`（实测 step2「预约定时」正常通过用了 34 轮，低于 30 会误杀），预算删除后轮次是唯一的单步上限。
- **保留任务级运行预算**：`SOP_MAX_MODEL_CALLS=600` / `SOP_MAX_RUN_SECONDS=7200` 不动，它仍是整轮失控的唯一全局兜底（本次失败并未触发它）。
- **精简 handover 契约**：执行者只交两块 —— ① 本步做了什么：每次点击 / 长按 / 拖动的 `action_time`（点击类工具返回原文），按操作顺序逐条列出；② 最终结果：以「达成」或「未达成」开头，一句话写清设备与页面的实际状态。删除「逐条对照证据」「阻塞与下一步建议」的写法要求；「尚未 / 未完成 / 未点击 / 请下一步」类收尾措辞仍禁止，与 handover 守卫的退回词表保持一致。

## 关联文档

无 PRD 需求编号。本次变更来源于线上任务故障复盘：`dev_docs/DEV_TEST/排查-任务清单失败原因-20261103.md`（TASK-177 时间线、三次撞线与空转轮次的证据）。

## Capabilities

### New Capabilities

（无：不新增能力，只收窄现有执行者的运行治理与交卷契约。）

### Modified Capabilities

- `agent-middleware-assembly`: 删除「单次回复的 token 预算」这条需求；「中间件统一装配入口」的固定顺序与默认集合去掉预算这一环。
- `role-prompt-guardrails`: 执行提示词的 handover 写法条款改为「操作步骤 + 最终结果」两块，保留 `action_time` 原文与未完成措辞禁令。

## Impact

- 代码：`engines/agents/middleware/budget.py`（删除）、`middleware/assembly.py`、`middleware/__init__.py`、`config/data/prompts/UI_EXECUTOR_PROMPT.md`。
- 配置：`.env.example` 中三行预算变量说明删除。
- 测试：`tests/graybox/unit/test_agent_middleware_assembly.py`（默认集合、顺序、预算开关用例）、`tests/graybox/unit/test_model_retry_middleware.py`（依赖预算关闭的用例）、`tests/graybox/unit/test_role_prompt_guardrails.py`（handover 措辞与条款断言）。
- 行为：所有角色不再有单步 token 收敛点；执行者单步最坏消耗由「预算撞线后 52 轮空转」变为「轮次上限 65 轮」，与既有轮次语义一致。任务级兜底不变。
- 不影响：SOP 引擎、handover 守卫的退回机制、事件折叠与计费链路、前端任务清单与报告展示。
