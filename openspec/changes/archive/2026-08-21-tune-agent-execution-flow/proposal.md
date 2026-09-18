## Why

上一 change 新增的 `sleep` 工具**没有进入智能体 04 的工具箱**：智能体的 26 条 AITool 记录是早前 `migrate_platform_tools` 回填的（早于 sleep 存在），而有记录时 `_resolve_enabled_tools` 只注入记录里的名字——新工具不会自动出现（17:02 构建日志 `tools=25` 实锤）。结果 AI 仍只能裸轮询：连续 9 次 `get_run_status`（无任何等待），再加 capture_page、重存用例、重跑，20 轮预算烧光，回复被截断（"已达最大推理次数"）；随后模型又走向另一极端——不再轮询、转而提示"您可以稍后问我进度"。根因是缺三个要素：**工具未注入 + 无系统提示词约束流程（system_prompt 为空）+ max_iters=20 预算过紧**。

## What Changes

1. **P0** 回填：重跑 `python manage.py migrate_platform_tools`——为 active 智能体补上缺失的 `sleep` 工具记录。
2. **P0** 智能体 04 配置：写入执行 SOP 系统提示词（run_test → sleep 10s → get_run_status 循环至终态（≤8 次）→ get_run_results 总结；禁止连续查询/改用例/重复执行；2 分钟未到终态则报告当前状态并说明可稍后再问）；`max_iters` 20 → 40。
3. **P1** `apps/ai_assistant/agent_scope/tool_registry.py`：`get_run_status` 描述补"运行中禁止连续查询，两次查询之间必须用 sleep 等待"。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.5（能力开关/AITool 逐工具）、§2.6（SSE 流式对话）、§4.2（构建口径）
- `apps/ai_assistant/AGENTS.md`（Tool 只调模块 api、SSE 双边契约）
- 现场证据：17:02 构建日志 `tools=25`、`ai_messages` 对话 211（msg 411 blocks：9 连查无 sleep）、`ai_agents` #10（system_prompt 为空、max_iters=20）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 智能体配置调优 + 回填 + 描述文案：无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`apps/ai_assistant/agent_scope/tool_registry.py`（1 处描述字符串）
- 数据：`ai_tools` 补 sleep 记录；`ai_agents` #10 的 system_prompt/max_iters
- 测试范围：`manage.py check` + ruff + 真实对话端到端（"执行 TC-NAV-004" 一轮完成、不触达 max_iters、最终报告 pass）
