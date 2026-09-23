## Why

C 方案（`decouple-locator-media-from-snapshots`）落地后缺一个**运维闭环**：

1. **存量页面仍指向检查器媒体路径**：6 个已保存页面里的 `screenshot_path` / `thumbnail_path` 依旧在 `inspector/**`（当时明确不做成批回填）。它们现在靠「删除时判定引用」保命，语义上仍与检查器耦合。
2. **重复导入会产生孤儿副本**：`locator/pages/<id>/` 下按 upsert 键命名的副本，在元素集合变化后会留下不再被任何行引用的文件（当时登记为「孤儿回收另做」）。
3. 这两件事都需要**能在部署环境访问 `MEDIA_ROOT` 的一次性工具**，而不是每次靠人工 shell。

## What Changes

- 新增管理命令 `python manage.py maintain_locator_media`（`apps/element_locator/management/commands/`）：
  - **默认 dry-run**：只统计与报告，不写文件、不改 DB；
  - `--apply` 才落盘；`--only backfill|prune` 可只跑一半；
  - **backfill**：把仍指向 `inspector/**` 且源文件存在的页面截图与元素缩略图复制到 `locator/pages/<page_id>/` 并改指副本（源文件**不删**，可能仍被快照引用）；源缺失则跳过并计数；
  - **prune**：删除 `locator/pages/**` 下**不再被任何页面或元素引用**的文件，并清理空目录；`inspector/**` 永不触碰；
  - 输出 `scanned / copied / repointed / skipped_missing / orphans_deleted / bytes_freed` 计数。
- **BREAKING**：无

## 明确移出本变更范围

- 不改导入路径（`import_snapshot_page` 已按 C 方案复制）
- 不做自动定时清理（是否定期回收属运维策略；本命令可被 cron/手工调用）
- 不删除 `inspector/**` 下的任何文件（那是检查器快照的资产）
- 不恢复已丢失的媒体

## 关联文档

- 需求编号：`PRD-03-设备检查器`（运维工具，无应用行为契约变化，故 `skip_specs`）
- 上游变更：`2026-09-21-decouple-locator-media-from-snapshots`（C 方案）、`2026-09-21-fix-dangling-snapshot-media`（删除侧保全）
- 语义依据：`device-inspector-snapshots`「导入到元素定位时复制媒体到元素定位自有目录」（本命令把该口径补到存量数据上）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯运维工具；应用行为契约已由 `device-inspector-snapshots` 定义，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- 新增 3 文件：`apps/element_locator/management/__init__.py`、`management/commands/__init__.py`、`management/commands/maintain_locator_media.py`
- 测试：新增 `tests/graybox/integration/test_locator_media_maintenance.py`（4 例）
- 运行影响：dry-run 零副作用；`--apply` 会写 `locator/pages/**` 并改 `el_pages.screenshot_path` / `el_elements.thumbnail_path`
- 迁移：无