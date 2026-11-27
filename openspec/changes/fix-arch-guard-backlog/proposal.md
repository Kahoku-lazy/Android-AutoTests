## Why

`tests/arch/unit`（契约守护，零 I/O、只读源码）长期挂着 **4 条失败**，在制变更队列已清零，这 4 条是当前唯一挡在「arch/unit 全绿」前面的债。逐条根因（2026-11-27 实测）：

| 守护 | 现象 | 根因 |
|---|---|---|
| `test_api_docs_surface::test_every_operation_has_a_description` | 130 个 operation 没有 description/summary | 2026-11-24 全仓去注释时把视图 docstring 一并删了；drf-spectacular 原先靠 docstring 取说明，`@extend_schema` 只标了 operation_id / responses |
| `test_auth_single_verify::test_deleted_user_still_rejected` | 期望 401，实得 403 | `_disabled_account_response()` 把「用户行不存在」与「账号停用」都当停用处理，统一返回 403 |
| `test_api_path_callers::test_every_caller_path_resolves_to_a_view` | 3 处前端调用在后端无路由 | ① `ai-assistant/api/agents.ts` 整份死代码（无人引用，指向已删除的 `/ai/agents/`）；② `ops-console/api.ts` 用变量拼 URL，守护解析成 `/ops/users/1/1/` |
| `test_view_write_convergence::...[views.py8]` | `task_list/views.py` 直写 ORM | 提交任务后 `task.result=…; task.save()` 两处、清空任务 `Task.objects.all().delete()` 一处写在 View 里 |

## What Changes

- **写库回到 `api.py`**：`task_list/api.py` 新增 `save_task_run_payload(task, payload)` 与 `clear_tasks()`，View 三处直写 ORM 改为调用它们；行为、事务边界、返回值不变。
- **删号即失效**：`_disabled_account_response()` 区分「行不存在 → 401 令牌无效」与「存在但 `is_active=False` → 403 账号停用」，恢复「删号后旧令牌必须失效」的既有语义。
- **前端清理死调用**：删除 `frontend/src/modules/ai-assistant/api/agents.ts`（无人引用）；`setOpsUserOperator()` 把动作写成模板内联三元，与同文件 `setOpsUserActive()` 一致，不再产生无法解析的动态路径。
- **API 文档补说明**：新增 `backend/shared/api_docs.py`，用 drf-spectacular 的 `POSTPROCESSING_HOOKS` 给缺失说明的 operation 补中文 summary（资源标签 + 动作动词的规则表，覆盖不到时回落 `METHOD path`）；在 `SPECTACULAR_SETTINGS` 注册。这样新端点也不会再让文档面出现空说明。

## 关联文档

无 PRD 条目：四条均为既有契约守护的回归修复与技术债清偿，不对应需求编号。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— `api-docs-surface` 的行为要求（每个 operation 有非空中文说明、tag 有中文说明）未变，只是补充说明的机制从「视图 docstring」改为「代码内的统一摘要映射」；`auth-session` 的停用语义未变，删除用户的 401 与停用账号的 403 是原本就区分开的两条。故 `.openspec.yaml` 置 `skip_specs: true`）

## Impact

- **后端**：`backend/apps/task_list/{api,views}.py`、`backend/gateway/middleware.py`、`backend/config/settings.py`、新增 `backend/shared/api_docs.py`
- **前端**：删除 `frontend/src/modules/ai-assistant/api/agents.ts`；`frontend/src/modules/ops-console/api.ts` 一处写法调整
- **接口**：路径、请求/响应形状、状态码语义均不变；唯一可观察变化是「已删除账号的旧 token」从 403 变回 401（更准确），以及 `/api/schema/` 现在每个 operation 都有中文 summary
- **测试**：`tests/arch/unit` 由 4 failed 转全绿；无需新增用例（4 条守护本身就是验收）
- **依赖与迁移**：无
