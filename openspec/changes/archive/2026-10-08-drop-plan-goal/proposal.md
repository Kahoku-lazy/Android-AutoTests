# 规划输出去掉 goal 字段，只保留 steps

## Why

规划模型的输出契约是 `{"plan": {"goal": ..., "steps": [...]}}`，其中 `goal` 只是把**任务自身的「任务目标」再回述一遍**——需求原文已经从输入的四键 JSON（`任务目标`）进来、也已存在任务记录里，前端详情页在拿不到它时会自动回退显示任务目标。回述带来两个实际代价：

1. **容易走样**：模型会顺手改写目标（实测出现过 `goal` 写成「打开 govee 应用并进入设备主页」而需求是「进入设备列表」这类改写），等于在契约里多留一段"可能与需求不一致的自由文本"；
2. **白花输出**：每次都多生成一段重复文本。

用户要求：规划模型输出**只保留 steps**。

**边界说明（重要）**：去掉的是**规划输出里回述目标的那个字段**；输入的「任务目标」（四键 JSON 的 `任务目标` / `TaskRequest.goal` / 任务表的 goal）**保持不变**——那是需求本身，不是重复。

## What Changes

- **规划提示词**：输出字段只列 `steps`（删掉 `goal：一句话总目标`）；案例示例改为 `{"plan": {"steps": [...]}}`。
- **引擎契约**：`Plan` 删除 `goal` 字段——`plans` 载荷从此外只含 `steps`。模型若仍偶发输出 `goal`，按 pydantic 默认行为忽略，不影响解析。
- **前端**：`TaskRunPlan.goal` 放宽为可选。旧任务记录里该键仍在（照常显示），新记录读不到就回退用任务自身的目标——该回退逻辑前端**已存在**，故只需让类型如实反映。
- **评测工具**：关键词覆盖只查 `steps`（不再借 `goal` 兜底），口径随之收紧。
- **规格**：`ai-platform-task` 的「平台任务按三模型工作流执行」需求更新——场景里"planner 产出至少一个 GoalPlan（含 goal/steps/verification）"改为只含步骤（并纠正早已不在契约里的 `verification` 表述）。

## 关联文档

- 关联能力：`ai-platform-task`（其场景描述了 planner 产出的计划形状）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-platform-task`：「平台任务按三模型工作流执行」这条需求的场景文字声明了计划包含 `goal`（以及早已废弃的 `verification`），本次改为只声明步骤——这是**契约级**变化，故本单不设 `skip_specs`，以 MODIFIED 更新该需求（保留全部原场景名，避免归档被判丢场景）。

## Impact

- 引擎：`engines/ai/agents/config.py`（提示词输出字段与案例）、`engines/ai/workflow/workflow.py`（`Plan` 契约）。
- 前端：`shared/types/ai.ts`（类型放宽为可选；渲染逻辑无需改动，回退已存在）。
- 评测工具：`apps/ai_assistant/management/commands/planner_eval.py`（`plan_text` 只看 steps）与其单测。
- 后端测试：4 个用例文件中构造 `Plan(goal=...)` 的地方同步。
- 规格：`ai-platform-task` 1 条需求。
- **不动**：`TaskRequest.goal`、任务表 `goal` 字段、四键 JSON 输入格式、执行 / 验收角色契约、前端页面结构。
- 数据库 / 迁移 / 通道：零改动。存量任务记录的 `plans[].goal` 仍在，前端按可选字段照常读取。
