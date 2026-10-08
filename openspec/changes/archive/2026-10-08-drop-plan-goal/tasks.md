## 1. 提示词与契约

- [x] 1.1 `engines/ai/agents/config.py` 的 `PLANNER_PROMPT`：「输出字段」删掉 `goal：一句话总目标`（只保留 `steps` 及其子字段说明）；「案例」示例改为 `{"plan": {"steps": [...]}}`（不再含 goal）。验证：grep 该提示词内不再出现 `goal`，且输出格式约束仍写明"只输出一个 JSON 字符串"。**验证结果**：输出字段改为「steps：操作步骤列表（**只输出步骤，不要回述目标**）」；案例示例已去掉 goal；提示词内除输入侧「任务目标」（四键 JSON 的键名，属输入、保留）外无 `goal` 字样；输出格式约束未动。
- [x] 1.2 `engines/ai/workflow/workflow.py` 的 `Plan` 删除 `goal` 字段（只留 `steps`），类 docstring 同步。验证：`Plan(steps=[...])` 可构造且 `model_dump()` 不含 `goal` 键；带 `goal` 的模型输出仍能解析（pydantic 默认忽略未知键）。**验证结果**：`Plan` 只剩 `steps`，docstring 写明"只含步骤、不回述目标"；新增单测 `test_parse_plan_ignores_legacy_goal_key` 断言"模型仍输出 goal 时照常解析，且解析结果 `model_dump()` 不含 goal"。

## 2. 消费方同步

- [x] 2.1 评测工具 `apps/ai_assistant/management/commands/planner_eval.py`：`plan_text()` 只拼 `steps` 的 action 与 assert（不再读 `plan.goal`）。验证：评测单测通过；用桩 plan 断言关键词只从步骤里命中。**验证结果**：`plan_text()` 改为只拼步骤；18 项评测单测全绿（含关键词正反用例）。
- [x] 2.2 前端 `frontend/src/shared/types/ai.ts`：`TaskRunPlan.goal` 改为可选（旧记录仍带该键，新记录没有）。验证：`npm run typecheck` 通过；`task-detail.spec.ts`（fixtures 带 goal）与相关用例全绿——渲染逻辑不改。**验证结果**：类型放宽为 `goal?: string` 并加注释说明缘由；`npm run typecheck` 无错误；`tests/ai-assistant/p0/task-detail.spec.ts` **11 项全绿**（其 fixtures 本身就带 `plans[].goal`，等于用存量形状验证了兼容性）；prettier/eslint 通过。**渲染逻辑未动**。
- [x] 2.3 后端用例同步：`test_ai_verifier_output_contract.py`、`test_ai_workflow_progress.py`、`test_ai_workflow_log_evidence.py`、`test_ai_planner_eval.py` 中构造 `Plan(goal=…)` 的地方去掉该参数（**断言不改**）。验证：这些文件全绿。**验证结果**：四处已同步（verifier 契约 3 处、log evidence 4 处、progress 1 处、planner_eval 桩工厂 1 处）。**一处例外如实登记**：`test_ai_workflow_progress.py` 原有一行断言是"`plans[0].goal == '启动'`"，它断言的正是本次删掉的字段，必须改为"`plans[0]` 不再含 goal"——这是被删字段的必然同步，不是放宽断言；其余断言逐字未改。相关文件合计 **66 项全绿**。

## 3. 规格

- [x] 3.1 delta（`ai-platform-task` 的「平台任务按三模型工作流执行」，MODIFIED 整块、场景名不变）：场景中"planner 产出至少一个 GoalPlan（含 goal/steps/verification）"改为只含步骤（`action`/`assert`/`log_check`），并删去早已废弃的 `verification` 表述。验证：`openspec validate` 通过，且归档时该需求更新成功、无"丢场景"报错。**验证结果**：`openspec validate --strict` 通过；归档时 `~ 1 modified` 成功、两个原场景名（`单目标平台任务` / `失败重试`）保留，未触发"丢场景"拦截（该坑上一次踩过，本次刻意保留场景名）。

## 4. 验证

- [x] 4.1 相关后端用例最小集：上述 4 个文件 + `tests/arch/test_channels.py`。验证：全绿（不发起全量回归）。**验证结果**：连同 `test_ai_debug_assembly_entry.py`、`test_ai_executor_log_check.py` 共 **66 passed**（5.46s）。
- [x] 4.2 端到端实证（真实调用，属预期费用）：`python manage.py planner_eval --cases tests/ai_planner/cases/planner.yaml --repeat 1 --tag drop-goal`。验证：硬性 7/7（口径已收紧为只看 steps）；报告里 plan 载荷**不含 goal**；如实记录通过率与费用。**验证结果**：**硬性 7/7**、总费用 **¥0.0930**（7 条）；报告 `tests/reports/planner_eval/drop-goal-20261008-124559.md` 内 `"goal"` **零命中**（plans 只有 steps）；关键词覆盖在新口径下全部命中（说明关键词确实落在步骤里，不再借 goal 兜底）。附带观察：删掉 goal 后 `single-step` 用例由 2 步收敛为 1 步（不再多写一段目标回述）。
- [x] 4.3 输入侧零改动核对：`git diff` 中 `TaskRequest.goal`、四键 JSON 构造、任务表 `goal` 相关文件（`engines/ai/base.py`、`apps/ai_assistant/api.py` 的 `build_planner_user_input`、`models`/`serializers`）**必须为空**。验证：逐项核对通过。**验证结果**：本次改动清单只含 `engines/ai/agents/config.py`（提示词）、`engines/ai/workflow/workflow.py`（契约）、`apps/.../planner_eval.py`（评测口径）、`frontend/src/shared/types/ai.ts`（类型）、4 个测试文件与变更文档；`engines/ai/base.py`、`apps/ai_assistant/api.py`、`models/*`、`serializers.py` **均不在清单内** → 输入侧与任务表字段零改动。
- [x] 4.4 静态与自检：`python manage.py check` + 门禁范围 `ruff check` / `ruff format --check`；前端 `npm run typecheck` + 相关 vitest。验证：全部通过。**验证结果**：`ruff check apps/ config/ gateway/ shared/ models/ engines/` → All checks passed；改动文件 `ruff format --check` → 5 files already formatted；`manage.py check` 无问题；前端 `vue-tsc` 无错误 + `task-detail.spec.ts` 11 项全绿。
- [x] 4.5 边界检查：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。**验证结果**：`✅ 模块边界检查通过 — 零违规`。
- [x] 4.6 关单与归档：汇总改动清单、实跑结果与费用；`openspec validate` 通过后归档（delta 并入 `ai-platform-task`）。验证：`openspec validate "2026-10-08-drop-plan-goal"` 通过并完成归档。**验证结果**：validate --strict 通过；已归档（`ai-platform-task` 更新 1 条需求）。
