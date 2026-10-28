## 1. 存储模块

- [x] 1.1 新增 `backend/apps/task_list/media_storage.py`：`encode(image_b64)`（720 WebP q75 + 原图 sha256）、`LocalMediaStorage.save/open/exists/delete_task/delete`、`TASK_MEDIA_DIR` 读取、路径穿越防护、原子写入。验证：新增单测覆盖编码尺寸/格式、写入后读取一致、越界 key 返回 None。**验证结果**：`tests/api/test_media_storage.py` 4 passed（720 长边、WebP、sha256、越界拒绝）。
- [x] 1.2 `backend/config/settings.py` 新增 `TASK_MEDIA_DIR = DATA_DIR / "task_media"`（env 可覆盖）。验证：`python manage.py check`。**验证结果**：System check identified no issues。

## 2. 写读路径

- [x] 2.1 `models.py`：`TaskMedia` 加 `storage_key`；生成迁移。验证：`makemigrations --check` 与测试库迁移通过。**验证结果**：`0002_taskmedia_storage_key` 已应用；`makemigrations --check` 输出 No changes detected。
- [x] 2.2 `event_store.py`：`_media_id` 改用 `media_storage.encode`，`_thumbnail` 移入 `media_storage.py`。验证：`tests/api/test_task_event_store.py` 全绿。**验证结果**：5 passed（含 `image/webp`、`storage_key`、文件存在）。
- [x] 2.3 `api.py`：`store_task_media` 先按 sha 去重，再落盘并写 `storage_key`；`get_task_media` 返回字节（优先文件、回退 `thumb_b64`）；`delete_task` / `clear_agent_tasks` 删除任务目录。验证：`tests/api/test_task_media.py` 断言 WebP 字节、文件存在、删任务后目录消失。**验证结果**：8 passed（含旧行回退、迁移命令、对账命令）。
- [x] 2.4 `views.py`：取图端点按新返回值输出字节，`Content-Type: image/webp`、ETag/304/immutable 保持。验证：端点测试通过。**验证结果**：`test_owner_gets_webp_bytes_with_cache_headers` 与 ETag/404/401 用例通过。

## 3. 迁移与对账

- [x] 3.1 新增 `migrate_task_media_to_disk` 命令：把 `thumb_b64` 存量转成 WebP 文件并写 `storage_key`、清空 `thumb_b64`；支持 `--dry-run`、可重复执行。验证：对本机存量跑 dry-run 与实跑，行数与文件数一致，取图可读。**验证结果**：dry-run 1,379 张 / 44.00 MB；实跑 1,379 张；`D:\Govee\data\task_media` 1,379 个文件、15.0 MB；1,379 行 `storage_key` 非空、`thumb_b64` 全空。
- [x] 3.2 新增 `reconcile_task_media` 命令：删除 DB 中不存在的孤儿文件、报告缺失文件的 DB 行；支持 `--dry-run`。验证：造一个孤儿文件与一条缺失行，命令分别识别。**验证结果**：真实数据 dry-run `0 orphan / 0 missing`；单测造孤儿+缺失后命令正确清理并在 stderr 报告。

## 4. 验证

- [x] 4.1 报告与图片链路：`tests/api/test_task_event_flow.py`、`test_task_media.py`、`test_task_event_store.py` 全绿。验证：pytest 输出。**验证结果**：23 passed（含 storage 测试共 27）。
- [x] 4.2 体量复测：迁移后 `task_media` 表大小、`DATA_DIR/task_media` 占用、取图耗时。验证：脚本输出。**验证结果**：表 **53.0 MB → 0.36 MB**（+0.2 MB 索引）；图片文件 **15.0 MB**（原 base64 文本 44 MB）；单张读取返回 `RIFF`/`image/webp`。
- [x] 4.3 静态与规格门禁：`ruff check` / `ruff format --check` / `openspec validate store-task-media-on-disk --strict`。验证：退出码 0。**验证结果**：ruff 全过；openspec valid；OpenAPI 基线只改 `task_media` 一条路径的格式与描述。
