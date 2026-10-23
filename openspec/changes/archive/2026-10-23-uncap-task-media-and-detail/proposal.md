# 取消截图张数上限并按全文展示事件明细

## Why

长任务看到一半开始没有图：每个任务只存 300 张唯一截图，实测任务 142 在开跑 42 分钟后额度用尽，之后 419 次截图全部丢弃，01:49 的步骤在报告里一张图都没有。同时事件明细被硬截到 240 字：一条 `GenerateStructuredOutput` 的 `args` 有 2,831 字，页面上只剩到「结论：达成……先关→开」就断了，看起来像结论没输出完整。

## What Changes

- **BREAKING**（数据量）：截图采集不再有张数上限。仍按任务内 `sha256` 去重、仍只存 720px JPEG 缩略图、仍不存原图；超过 300 张后新图照常入库，事件拿到图片引用。
- 事件明细不再截断：`item.detail` 完整下发文本块的全文、工具入参全文、工具结果全文；只保留去回车与去首尾空白。
- `data.task.result` 仍按 240 字摘要，避免报告头部无意义膨胀（页面不展示该字段）。
- 清理 `TASK_MEDIA_LIMIT` 常量与相关分支；历史任务中已被丢弃的截图不补。

## 关联文档

无关联 PRD：本次为缺陷修复（截图丢失 + 明细截断），验收以「任意截图事件都有 media_id」「明细长度等于原文长度」为准。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-event-store`: 移除「图片上限 300」要求，改为不设张数上限，去重与缩略图规则不变。
- `agent-task-flow-report`: 新增「事件明细完整展示」要求，明细不再截断。

## Impact

- 后端：`backend/apps/task_list/api.py`（删除上限常量与判断）、`backend/apps/task_list/task_reports.py`（明细去截断）。
- 前端：不改；`TaskMediaThumb` 已经按视口懒加载，图片变多不会一次性拉取。
- 数据：`task_media` 行数不再封顶。按实测 785 次截图、单张约 26 KB 估算，一个多用例任务约 20 MB；这是「不丢图」的代价，需要关注表体积与备份。
- 契约：`items[].media_id` 与 `detail` 字段名不变；`detail` 长度变长，响应体量随文本内容增长（gzip 后传输）。
- 测试：`tests/api/test_task_event_store.py`、`tests/api/test_task_event_flow.py`。
