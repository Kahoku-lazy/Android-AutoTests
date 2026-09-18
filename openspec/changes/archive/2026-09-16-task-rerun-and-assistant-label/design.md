## Context

现有 `create_task` + `dispatch_device` 已能新建并调度。列表 `serialize_agent_task_row` 不含助手名。`AITask` 有 `agent` FK。看板线路名存在 `route_configs.device_control.name`。失败卡仅有「详情」。

## Goals / Non-Goals

**Goals:**

- 失败任务克隆新建（标题/目标/附件/设备/agent），原记录不动
- 列表 `assistant_name` 每次序列化从当前线路名读取
- 失败卡「重新执行」后刷新列表可见新卡

**Non-Goals:**

- 不重放原任务 result / token
- 不改详情页过程日志结构
- 不在运行中/成功卡提供重跑（本期仅失败）
- 不为助手名加任务表新列（改名同步靠读当前配置）

## Decisions

### D1 克隆走现有 create_task + dispatch

`POST /api/ai/agent-tasks/{id}/rerun`（owner/可见权限对齐删除）。api 读原任务字段 `create_task(...)`，再 `dispatch_device(serial)`。原 status/result 不 UPDATE。

**备选**：重置原任务为 pending。否决：用户明确要求不覆盖。

### D2 助手名实时派生

`serialize_agent_task_row` / detail 增加 `assistant_name`：`(agent.route_configs.device_control.name or "").strip() or agent.name`。列表已有 agent FK，可用 `select_related("agent")`。

**备选**：任务表存 snapshot。否决：改名无法同步历史卡。

### D3 按钮范围

仅 `failed` 展示「重新执行」。成功/运行中不加。

## 模块防火墙自检

- 写库只经 `api.py`（clone + 原 create_task）
- 不跨 App import service/runner；调度仍本模块 `dispatch_device` → `task_runner`
- 前端只走 `/api/ai/agent-tasks*`
- 不新增 WS

## Risks / Trade-offs

- [同设备仍有 running，新任务排队] → 与新建任务相同，可接受
- [原设备已离线] → 仍用原 serial 创建；调度失败行为与现网 pending 一致，不在本期改拒绝策略
- [列表 N+1] → `select_related("agent")`

## Migration Plan

无表迁移。回滚：去掉端点与按钮、序列化字段可忽略。

## Open Questions

无。重跑范围按用户点选的失败卡限定为失败态。
