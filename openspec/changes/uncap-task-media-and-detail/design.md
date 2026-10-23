## Context

`store_task_media` 在任务已有 300 张不同图片后直接返回 `None`，事件 `media_id` 随之写空。任务 142（12 用例、3.5 小时）共 785 次截图，300 张额度在 01:01:33 用完，之后 419 次截图没有图。明细侧，`_clip` 把每条 `detail` 截到 240 字，而一条 `GenerateStructuredOutput` 的 `args` 有 2,831 字、`handover` 2,794 字，页面上只剩开头。

## Goals / Non-Goals

**Goals:**

- 任意截图事件都能拿到 `media_id`，不再因张数被丢弃。
- 事件明细完整展示原文，不再出现截断省略号。

**Non-Goals:**

- 不做图片保留期/清理策略（本次按“不丢图”优先）。
- 不把历史任务中被丢弃的截图找回来（数据已不存在）。
- 不改图片字节端点、前端懒加载与 `TaskMediaThumb`。
- `data.task.result` 保持 240 字摘要——页面不展示它，避免报告头部随结果文本膨胀。

## Decisions

**1. 直接删除上限，而不是再调大。**

用户明确要求“截图无上限”。保留原有的任务内 `sha256` 去重与 720px 缩略图，只删掉 `TASK_MEDIA_LIMIT` 常量与计数分支。代价是 `task_media` 行数无界：按实测 785 张、单张约 26 KB 估算，一个多用例任务约 20 MB；这是“不丢图”的显式取舍。备选“把上限提到 2000”仍会在更长的任务里丢图，被否。

**2. 明细全量下发，截断只留给 `task.result`。**

新增 `_text(value)`：只做 `\r → 空格` 与 `strip`，不截断；`_detail` 的七处 `_clip` 全部换成 `_text`。`_clip` 仅保留给 `data.task.result`（240 字）。备选“把 `_DETAIL_LIMIT` 调大”治标不治本（2,831 字的入参仍会断），被否；备选“前端展开全文”需要新增字段或端点，改契约且没必要——明细本来就在响应里。

**3. 前端零改动。**

`TaskDetailPage` 已用 `white-space: pre-wrap` 渲染 `item.detail`，`TaskMediaThumb` 已按视口懒加载；图片变多只影响滚动到哪加载到哪。

**4. 同步 `task-media-delivery` 的 Purpose 文案。**

该能力的目的句仍写着“采集上限按覆盖整轮多用例任务来定”，与本次改动冲突。按 OpenSpec 的 Purpose 维护方式直接改主 spec 的 Purpose，不动它的需求列表。

## 模块防火墙自检

- 只改 `backend/apps/task_list/api.py`、`task_reports.py` 与对应测试；无跨 App import、无写库路径变化。
- `store_task_media` 仍在 `task_list/api.py` 内，事件写入链路不变。

## Risks / Trade-offs

- [`task_media` 无界增长] → 已知并接受；单任务量级按 26 KB/张估算，后续若需要控制可另立“保留期/归档”变更。
- [响应体变大] → 明细变长会增大 JSON，但图片仍走独立端点；gzip 后传输，且前端只渲染当前视口。
- [历史截图永久缺失] → 不补；报告中这些事件保持 `media_id = null`，不做假数据。
- [测试里一次建 300+ 行图片] → 用 `bulk_create` 预置，避免逐条调用拖慢单测。
