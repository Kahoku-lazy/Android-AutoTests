## Why

任务详情页里"执行过程的截图"大面积看不到。实测两个正在跑/刚跑完的任务：

| 任务 | 截图事件 | `task_media` 行 | 报告里有图的用例分布 |
|---|---|---|---|
| 134 | 124 | **40** | 用例1：69 张；用例2：2 张；用例3–7：0 |
| 135 | 191 | **40** | 用例1：60 张；用例2–7：**0** |

两个原因叠加：

1. **采集上限 40 张**（`store_task_media` 满 40 后新图直接丢弃），所以长任务从第 41 张不同画面起全部没有图，后面的用例更是一张不剩。
2. **图片以 base64 内联在报告 JSON 里**（只有 `thumb` 一个字段可用），134 的 `/api/tasks/134/report/` 载荷 **5.91MB**、其中 base64 占 40%。这既让页面首屏背着几 MB 的 JSON，也让"多存一些图"变得不可行——上限一提，载荷就失控。

## What Changes

- **报告只下发布局**：`GET /api/tasks/{id}/report/` 的每个事件项由 `thumb`（`data:image/jpeg;base64,...`）改为 `media_id`（整数或 `null`），不再内联任何图片字节。
- **截图改为独立端点**：新增 `GET /api/tasks/{id}/media/{media_id}/`，返回 JPEG 字节；要求登录、校验任务归属，带 `ETag`（内容 sha256）与 `Cache-Control: private, max-age=31536000, immutable`，命中 `If-None-Match` 返回 304。
- **采集上限 40 → 300**：仍按内容 sha256 去重，仍只存 720px 缩略图；上限从"一段任务就爆"改为"覆盖整轮多用例任务"。
- **前端懒加载**：新增 `TaskMediaThumb` 组件，进入视口才请求字节、拿到后转 object URL，卸载时释放；加载中占位、失败不占版面。

## Capabilities

### New Capabilities

- `task-media-delivery`：任务截图媒体的下发契约——报告只给引用、字节走独立鉴权端点、前端按需懒加载。

### Modified Capabilities

- `agent-task-event-store`：图片采集上限由 40 张改为 300 张，去重与"只存缩略图、不存原图"的规则不变。

## Impact

- 后端：`backend/apps/task_list/{api,task_reports,views,urls}.py`；`openspec/openapi.yaml` 基线随新端点更新。
- 前端：`frontend/src/modules/task-list/api/tasks.ts`、新增 `components/TaskMediaThumb.vue`、`TaskDetailPage.vue`。
- 契约：任务流程报告的 `items[].thumb` 字段**移除**，改为 `items[].media_id`；前端同步切换（后端先发布不会让旧前端崩溃，图片区只是不显示）。
- 数据：无迁移；历史任务的 `task_media` 行继续可用（按 `media_id` 取图），但超过 40 张时被丢弃的历史图片**无法恢复**。
