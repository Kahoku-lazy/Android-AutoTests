# 稳定任务详情页加载：报告瘦身 + 代理容错

## Why

任务详情页打开一次要等十几秒，后端一重启还会弹出 `Request failed with status code 500`。实测任务 141 有 147,850 条事件，`build_task_flow` 单次 10.2 秒、载荷未压缩约 8.7 MB，其中 94.7% 是流式增量 `ToolCallDeltaEvent`，它们的 `payload` 报告根本不用；而这条 500 并不是报告接口报的，是 Vite 开发代理在后端热重载空窗期连不上 8766 时自己回的空 body 500，页面无法区分"后端挂了"和"接口错了"。

## What Changes

- 报告接口改为只读渲染所需列：事件表查询不再取整行模型，也不读取流式增量的 `payload`；增量仍按原规则合并并用 `count` 表示次数。
- 报告响应契约不变：`{status, data}` 信封与 `data.task` / `data.rounds` / `data.cases` / `data.conclusion` 的字段和语义保持原样。
- Vite 开发代理新增上游不可用分支：连接被拒绝/重置时返回 `503` 和 `{status: false, message}`，不再回空 body 的 500；后端自身返回的 5xx 原样透传。

## 关联文档

无关联 PRD：本次是缺陷修复（报告接口性能 + 开发代理容错），不新增产品能力，验收以性能基线与错误语义为准。

## Capabilities

### New Capabilities

- `frontend/dev-proxy`: 开发代理把 `/api`、`/media` 转发到 Django 时，上游不可用的失败语义（503 + 可读原因），与后端 5xx 的透传边界。

### Modified Capabilities

- `agent-task-flow-report`: 新增报告接口的取数范围与耗时上界要求，明确增量载荷不参与读取与传输。

## Impact

- 后端：`backend/apps/task_list/task_reports.py`（事件取数与行对象）、`backend/apps/task_list/views.py` 不变；测试 `tests/api/test_task_event_flow.py`、`tests/api/test_task_api_paths.py`。
- 前端：`frontend/vite.config.js`（代理错误处理）；不涉及页面组件与业务代码。
- 契约：`/api/tasks/{id}/report/` 响应字段不变，仅服务端取数方式与体积变化；OpenAPI 基线不变。
- 不涉及数据库迁移、依赖新增与计费逻辑。
