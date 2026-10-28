# 设计：家电测试用例编写任务（Agent-02）

## Context

现有任务链是「设备执行」单一路径：`TaskSubmitAPIView` 只接受 YAML + 设备，`task_runner` 只跑 `run_platform_sop`，报告只展开设备用例轮次。引擎侧已有 `CaseAuthoringWorkflow`、`build_case_writer` / `build_case_verifier` 与 `build_run_input`（见 `engines/agents/workflow/case_authoring_workflow.py`），但没有平台入口。

## Goals / Non-Goals

**Goals**

- 用 `task_kind` 把两种任务分开，设备执行路径零行为变化。
- Agent-02 从 AI 助手可见、可配置；新建任务按 Agent 类型切换表单。
- 文档解析复用现有 `attachments.parse_document_bytes`（markitdown）。
- 用例结果进入任务清单与测试报告详情。

**Non-Goals**

- 不把生成的用例自动导入用例管理库。
- 不新增独立任务表、独立报告表或独立前端页面。
- 不做多轮对话式需求澄清；一次上传、一次生成。

## Decisions

### D1 用 `task_kind` 而不是 Agent 名称判断

`AIAgent.task_kind` 决定新建任务类型，`Task.task_kind` 做快照。理由：名称可改，路由配置可增删；类型是稳定契约。迁移种子 Agent-02 时同时写 `route_configs.case_authoring` 供卡片展示，但执行分流只认 `task_kind`。

### D2 任务清单改为「可见 Agent 的全部任务」

原实现只列 `get_platform_agent()` 的任务，Agent-02 任务不会出现。改为 `filter_agents_for_user` + `Task.objects.filter(agent__in=agents)`，与报告列表、详情报告使用同一可见性口径。对普通用户仍是平台 Agent 范围，对超管增加 Agent-02。

### D3 用例编写任务不占设备槽位

`dispatch_case_authoring` 直接把 pending 置 running 并起线程，不走 `dispatch_device`。理由：没有设备，也不该阻塞设备队列。一次任务一个线程，失败后可重跑。

### D4 结果写 `Task.result` JSON，不新增结果表

`Task.result` 已经是 TextField，报告/详情已有 `parse_task_result`。用例文档全文、判决、摘要放同一个 JSON；列表只取 `summary`，详情才下发 `document`。避免为一次性文档新增表与迁移。

### D5 报告用独立分支返回文档

`build_task_flow` 在 `task_kind=case_authoring` 时返回 `document` / `documents` / `verdicts`，`cases` 与 `rounds` 为空。前端用 `marked` + `DOMPurify` 渲染 Markdown；设备任务分支完全不动。

### D6 前端按 Agent 类型切换新建表单

`useTaskPublish` 计算 `isCaseAuthoring`，表单只渲染对应字段；切换 Agent 时只清理与目标类型不兼容的字段（选 Agent-02 清 YAML/设备/指定用例，选设备 Agent 清文档）。提交仍走同一个 `/api/tasks/submit/` multipart 接口。

## Risks / Trade-offs

- [用例文档很长，`Task.result` 与报告 JSON 变大] → 需求正文在 `build_case_requirement` 截断到 8 万字；报告详情按需返回全文，列表只取摘要。
- [后台线程无取消语义] → 关闭任务时先置 `cancelled`，线程结束时看到终态跳过回写；本轮执行仍会跑完，后续可接 asyncio 取消。
- [markitdown 解析质量依赖文档] → 解析失败返回 400，不创建任务；上限 20MB / 5 份。
- [Agent-02 模型由引擎常量决定，不读 DB 模型] → 与现有设备角色一致；DB 的 `model_name` 只用于展示，后续要改为按 Agent 配置执行需单独变更。

## Migration Plan

1. 应用 `ai_assistant.0061`（加字段 + 种子 Agent-02）与 `task_list.0004`（加字段）。
2. 部署后端与前端；旧任务 `task_kind` 默认 `device_control`，读取不受影响。
3. 回滚：反向迁移删除 Agent-02（无任务时）并移除字段；或保留字段、把 `task_kind` 全部视作 `device_control`。

## Open Questions

无。
