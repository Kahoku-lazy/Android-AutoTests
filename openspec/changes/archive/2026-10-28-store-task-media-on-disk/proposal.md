# 任务截图改为本地文件存储（WebP）

## Why

截图字节一直躺在 MySQL 的 `task_media.thumb_b64` 里：1,379 张图就让这张表占 53 MB，备份、主从和查询都被图片字节拖累。永久保留 + 不设张数上限之后，这个量只会持续变大；而 `DATA_DIR` 已经指向 `D:\Govee\data`，磁盘才是放图片的合适位置。

## What Changes

- 截图字节改存本地文件：`DATA_DIR/task_media/<task_id>/<sha256>.webp`；`task_media` 只保留元数据与 `storage_key`，不再存 base64。
- 缩略图格式由 JPEG 改为 **WebP（质量 75，长边 720）**；同一批实测体积约为 JPEG 的 44%。
- 取图端点 `GET /api/tasks/{task_id}/media/{media_id}/` 的鉴权、`ETag`、304、`immutable` 语义不变，`Content-Type` 改为 `image/webp`。
- 删除任务时一并删除该任务的文件目录；新增两个管理命令：存量迁移 `migrate_task_media_to_disk`、文件与数据库对账 `reconcile_task_media`。
- `thumb_b64` 分两阶段下线：本变更先并存（读取优先文件，缺失时回退旧列），验证后再单独删除该列。

## 关联文档

无关联 PRD：本次为存储结构调整，验收以「DB 不再存图片字节」「取图字节与 WebP 格式正确」「删任务不残留文件」为准。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-task-event-store`: 图片从「存 720px JPEG 缩略图字节到数据库」改为「存 720px WebP 文件 + 数据库只存元数据与 storage_key」。
- `task-media-delivery`: 取图端点的 `Content-Type` 由 `image/jpeg` 改为 `image/webp`，其余缓存与鉴权语义不变。

## Impact

- 后端：新增 `backend/apps/task_list/media_storage.py`；改 `api.py`、`event_store.py`、`views.py`、`models.py`、`settings.py`；新增两个 management command 与迁移。
- 数据：`task_media` 加 `storage_key`；存量 1,379 行迁到文件后清空 `thumb_b64`；图片文件落在 `DATA_DIR`，随任务删除清理。
- 前端：不改（`TaskMediaThumb` 用 blob，格式透明）。
- 备份：DB dump 从 53 MB 级降到约 1 MB；图片目录直接增量复制。
- 不做：保留期/自动删除（永久保留）、不存原图、不引入对象存储/CDN。
