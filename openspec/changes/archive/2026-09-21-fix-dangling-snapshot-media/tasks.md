## 1. 后端：删除时保全被引用的媒体

- [x] 1.1 `apps/device_inspector/api.py` 新增 `_media_referenced(screenshot_path, thumbs_dir_rel)`：`Page.screenshot_path` 精确匹配 + `Element.thumbnail_path` 前缀匹配（跨 App 只读 Model）；验证：集成测试 `test_delete_snapshot_keeps_media_referenced_by_locator` 等 3 例通过
- [x] 1.2 `delete_snapshot` 调整为「先判定 → 未引用才 `delete_snapshot_files` → 再删记录」，保留分支写 `logger.info`；验证：集成测试断言「记录已删 + 截图与缩略图仍在」与「记录与文件都删」两条路径均通过
- [x] 1.3 fail-closed：判定抛错时不删任何文件；验证：集成测试 `test_reference_check_failure_keeps_everything`（monkeypatch 判定抛 `RuntimeError`）→ 断言快照记录、截图、缩略图三者都还在

## 2. 前端：失效媒体降级

- [x] 2.1 `ScreenshotView.vue`：新增 `shotFailed` + `onShotError`，`screenshotPath` 变化时复位；失效时走既有空态但文案为「截图已失效」+「该页面的截图文件已不存在，请重新获取或换一份快照回看」；验证：真机打开截图已失效的页面 #39 → `screen-img` **0** 个、`.no-signal__title` = 「截图已失效」（与「暂无页面快照」区分）、**0** pageerror（不再是空白画面）
- [x] 2.2 `StructureAnalysisPanel.vue`：新增 `brokenThumbs`（按 `_rowKey`）与 `enlargeBroken`，两处 `<img>` 加 `@error`；验证：真机页面 #39 → 缩略图列 `img.sap-thumb` **0** 个 / `.sap-thumb-empty` **7** 个（仍可点击）、放大预览 `.sap-enlarge-missing` **1** 个且 7 个明细字段照常显示
- [x] 2.3 正常路径回归：快照 #345（99 元素 / 98 带缩略图 / 媒体 HTTP 200）→ 手机屏幕 `screen-img` 1 个、缩略图渲染 6 个 + 占位 1 个（该行本就无缩略图）、无失效空态；验证：真机读数 `temps/dbg-thumbs.mjs`

## 3. 测试

- [x] 3.1 新增 `tests/graybox/integration/test_inspector_snapshot_media.py`（3 例，marker `integration` + `device_inspector`，`django_db` + `override_settings(MEDIA_ROOT=tmp_path)`）；验证：`python -m pytest tests/graybox/integration/test_inspector_snapshot_media.py -q` → **3 passed**；`-m device_inspector` → 3 passed / 296 deselected

## 4. 门禁与归档

- [x] 4.1 `openspec validate fix-dangling-snapshot-media --strict`；验证：valid（1 个新 capability + 1 条新增要求）
- [x] 4.2 `python manage.py check`（0 issues）+ `python -m ruff check`（All checks passed）+ `ruff format --check`（2 files already formatted）；验证：见读数
- [x] 4.3 `python -m pytest tests/graybox -q -m device_inspector`；验证：3 passed
- [x] 4.4 `npm run lint:styles`（LINT_EXIT=0）+ `npx vite build`（退出码 0，1m 52s）+ `npx vitest run tests/device-inspector`（3 passed）；验证：见读数
- [x] 4.5 真机走查（失效页面 + 正常快照）；验证：`temps/inspector-stale-media-check.mjs` 与 `temps/dbg-thumbs.mjs` 读数，0 pageerror
- [x] 4.6 归档：新建主规格 `openspec/specs/device-inspector-snapshots/spec.md`（1 requirement / 3 scenarios）+ `device-inspector-page` 写回「失效媒体降级显示」（第 278 行，3 scenarios）；验证：两份规格结构完整
