## Context

图片字节当前存在 `task_media.thumb_b64`（base64 TEXT），写入路径是 `TaskEventSink._media_id → api.store_task_media`，读取路径是 `TaskMediaAPIView → api.get_task_media`。`DATA_DIR` 已可指向外部盘（本机 `D:\Govee\data`），磁盘空间 76 GB。

## Goals / Non-Goals

**Goals:**

- 图片字节离开 MySQL，DB 只留元数据；取图端点契约除 `Content-Type` 外不变。
- 存 720px WebP（q75），比 JPEG 小约 56%。
- 存量 1,379 张可平滑迁移，迁移期间读路径不中断。

**Non-Goals:**

- 不存原图、不做衍生图多尺寸。
- 不设保留期、不自动删除（永久保留）。
- 不引入 MinIO/S3/CDN；但存储接口留好替换点。
- 本次不删 `thumb_b64` 列（两阶段下线）。

## Decisions

**1. 新增 `media_storage.py` 作为唯一存储入口。**

`LocalMediaStorage` 提供 `save(task_id, sha256, data) → storage_key`、`open(storage_key) → bytes | None`、`exists(key)`、`delete_task(task_id)`。路径固定为 `TASK_MEDIA_DIR/<task_id>/<sha256>.webp`，写入用临时文件 + `os.replace` 原子替换。将来换 S3 只替换该模块实现，`api.py`/视图不动。

`encode(image_b64)` 负责解码、转 RGB、长边 720 缩略、WebP q75；`sha256` 仍取**原图字节**（与现有去重、ETag 语义一致），文件内容为 WebP。

**2. 数据库只留 `storage_key`。**

`TaskMedia` 加 `storage_key`（`<task_id>/<sha256>.webp`）。新行 `thumb_b64` 置空；读取优先 `storage_key`，为空时回退 `thumb_b64`（迁移窗口与旧数据）。`media_type` 新行写 `image/webp`。

**3. 两阶段下线 `thumb_b64`。**

第一阶段：加列、迁移命令把存量写文件并清空 `thumb_b64`，读路径带回退。验证一轮后单独变更 `ALTER TABLE DROP COLUMN`。回滚只需保留旧列与 DB 备份。

**4. 删除任务即删目录；对账命令兜底。**

`api.delete_task` 先删库再删目录；`clear_agent_tasks` 收集任务号后逐个删目录。文件删除失败不会回滚业务删除，由 `reconcile_task_media` 清理孤儿文件、报告缺失文件。

## 模块防火墙自检

- 只改 `task_list` 内部：`media_storage.py`、`api.py`、`event_store.py`、`views.py`、`models.py`、管理命令；无跨 App import。
- 图片文件读写集中在 `media_storage`，视图仍只分发、写库仍走 api。

## Risks / Trade-offs

- [WebP 兼容性] → 目标浏览器均为 Chromium/Edge；`TaskMediaThumb` 用 blob，与格式无关。
- [迁移中断/重复执行] → 命令按 `storage_key` 已存在则跳过，可重复执行；先 `--dry-run`。
- [DB 删除成功但文件删除失败] → 对账命令按目录与 DB 比对，清理孤儿文件。
- [路径穿越] → `open` 解析后校验必须位于 `TASK_MEDIA_DIR` 之内；`sha256` 只接受 64 位十六进制。
- [旧行回退] → `thumb_b64` 非空时继续可读；迁移命令跑完并验证后再删列。
