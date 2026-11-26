## Why

工作流一旦发布，任务提交就改从「发布快照」读角色配置；但快照里没有 `assistant_id` / `run_name` / `base_url`，执行端 `_binding()` 第一行就 `KeyError: 'run_name'`，任务在 0 秒内被判失败（任务 248、249 现场复现）。发布这个动作等于把「能跑的路」换成了「必崩的路」。

## What Changes

- 发布工作流时，两侧快照补齐运行身份：`assistant_id`、`run_name`（发布时的名片显示名，按既有规则在同名时给验收侧加后缀）、`base_url`；提示词、模型、厂商、工具等既有字段口径不变。
- 新增一次性数据迁移：给库里已有的工作流发布版本补上这三个字段（只补缺、不覆盖已有值，不动提示词/模型/工具），让已发布版本与引用它的历史任务（含 248/249 重跑）恢复可执行。
- 补功能级回归用例：发布 → 提交任务 → 执行端按该版本解析出可用的角色绑定。

## 关联文档

无 PRD 条目：本改动来自 2026-11-25 现场故障（任务 248/249 提交后 0 秒失败、`reason='run_name'`）的排障结论，属缺陷修复，不对应既有 PRD 需求编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `assistant-release`: 「发布冻结当前运行内容」补充工作流版本必须冻结两侧运行身份字段；新增「历史工作流版本补齐运行身份字段」这条一次性修复要求。

## Impact

- 后端：`backend/apps/ai_assistant/api.py`（快照组装）、`backend/apps/ai_assistant/services/sop_workflows.py`（同名后缀规则提取为共享函数）、新增迁移 `0089_backfill_workflow_release_binding.py`。
- 数据：`ai_assistant_releases` 中 `target_kind='workflow'` 的历史 payload 被补字段（可空跑、可重复执行）。
- 接口：无新增/变更端点；`POST /api/ai/sop-workflows/{id}/publish/` 的响应形状不变。
- 执行链：`backend/apps/task_list/task_runner.py` 不改，靠快照补全恢复；`engines/` 不改。
- 测试：新增 `tests/ai_assistant/api/test_workflow_release_binding.py`；不得回归 `tests/ai_assistant/api/test_release.py`、`tests/task/api/test_task_submit_sop.py`、`tests/task/api/test_task_submit_platform_cases.py`。
