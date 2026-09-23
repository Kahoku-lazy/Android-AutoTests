## 1. 导入时复制媒体到元素定位自有目录

- [x] 1.1 `apps/element_locator/api_snapshot.py` 新增 `_copy_into_locator(rel_path, dest_rel)`；验证：四分支齐备（空路径 / 已在 `locator/pages/` 下幂等 / 源缺失告警保留原路径 / IO 失败告警保留原路径）；集成测试覆盖「源缺失」分支
- [x] 1.2 元素缩略图复制：文件名由 upsert 键派生（`el_<安全前缀>_<sha1(rid|bounds)[:8]>.png`）；验证：真机导入后 99 个元素中 98 个副本存在（第 99 个本就无缩略图），格式为 `locator/pages/47/el_<rid>_<hash>.png`；集成测试「重复导入不串图」通过
- [x] 1.3 页面截图复制：页面落库后复制到 `locator/pages/<page_id>/screen.png` 并回写；验证：真机 `PAGE_SHOT = locator/pages/47/screen.png`，文件存在；`curl` 读数 `DIRECT_8766=200 bytes=631625`、`VIA_5173=200 bytes=631625`（同一副本经直连与前端代理均可访问），浏览器侧 0 个 `/media/` 4xx

## 2. 测试

- [x] 2.1 扩展 `tests/graybox/integration/test_inspector_snapshot_media.py` 至 **7 例**（A 组 3 例沿用 + B 组 4 例：导入后路径指向自有目录 / 删源快照后副本仍可用 / 源缺失保留原路径 / 重复导入不串图）；验证：`python -m pytest tests/graybox/integration/test_inspector_snapshot_media.py -q` → **7 passed**；`-m device_inspector` → 7 passed / 296 deselected

## 3. 真机端到端

- [x] 3.1 设备抓快照 `#346`（99 元素）→ 经「保存到元素定位」写入新页面 `#47`（99 元素）→ DB 读数：`screenshot_path = locator/pages/47/screen.png`、元素缩略图为 `locator/pages/47/el_*` 且 98/99 副本在磁盘、副本可访问；验证：`manage.py shell` 读数 + 浏览器 0 个 `/media/` 4xx
- [x] 3.2 **删除源快照 `#346`** 后复核：源截图 `inspector/shots/capture_20260921_175909_813488.png` 与源缩略图目录均**已被清理**（记录不再引用它们，删快照按原规则清理），而页面 `#47` 的副本与记录**完好**；Playwright 回看：`screen-img` 1 个（宽 283px）、缩略图渲染 6 + 占位 1、**0 个 `/media/` 4xx**、0 pageerror；验证：`temps/inspector-decoupled-page-check.mjs` 读数 + 文件系统核对；`curl` 复核源截图 `SOURCE_SHOT=404`、副本 `200`，解耦成立

## 4. 门禁与归档

- [x] 4.1 `openspec validate decouple-locator-media-from-snapshots --strict`；验证：valid
- [x] 4.2 `python manage.py check`（0 issues）+ `python -m ruff check apps/element_locator`（All checks passed）+ `ruff format --check`（2 files already formatted）；验证：见读数
- [x] 4.3 `python -m pytest tests/graybox -q` 全量；验证：**303 passed**（含本单新增 4 例）；`-m device_inspector` 7 passed
- [x] 4.4 `npm run lint:styles`（`LINT_EXIT=0`）+ `npx vite build`（退出码 0，1m 22s）——前端本轮未改，作回归；验证：见读数
- [x] 4.5 归档：`device-inspector-snapshots` 写回第 2 条要求（该 capability 变 **2 requirements / 7 scenarios**）；验证：requirement 行 9 / 28，场景 13/19/24/32/38/44/50
