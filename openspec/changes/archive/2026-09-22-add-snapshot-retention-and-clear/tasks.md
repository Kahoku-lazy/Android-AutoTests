## 1. 后端：保留上限与自动淘汰

- [x] 1.1 抽出共用的媒体安全删除帮手（判定 → 保留被引用文件 → 删记录），`delete_snapshot` 改为调用它且行为不变。验证：`tests/graybox/integration/test_inspector_snapshot_media.py` 既有 6 条用例全绿
- [x] 1.2 在 `api.py` 登记保留上限常量（10）并实现「淘汰该用户最早的多余快照」，在 `capture_snapshot` 落库成功后调用。验证：新增用例断言「第 11 条出现后仍为 10 条且删掉的是最早一条」「未超上限时不删任何记录」
- [x] 1.3 淘汰路径复用媒体保全：被元素定位引用的媒体在淘汰后仍存在。验证：用例断言记录消失但截图 / 缩略图文件仍在
- [x] 1.4 `list_snapshots` 条数封顶为保留上限（请求 `limit=100` 也只回上限条），`total` 仍为真实总数。验证：用例断言最多 10 条且 total 为真实总数
- [x] 1.5 淘汰只作用于调用者自己：他人快照不受影响。验证：用例断言发起采集的用户名下减少、另一用户的记录数不变

## 2. 后端：一键清空端点

- [x] 2.1 `api.clear_snapshots(user_id)`：删除该用户全部快照并返回删除条数，复用媒体保全帮手。验证：用例断言「清空后该用户 0 条」「返回条数 = 清空前的条数」「无快照时返回 0」「他人在场时不被删」
- [x] 2.2 视图与路由：`DELETE /api/inspector/snapshots/clear/` → `{deleted}` 信封响应。验证：HTTP 用例断言 200 + 信封 + 归属隔离；路径与前端 `api.ts` 调用一致（`test_api_path_callers` 通过）
- [x] 2.3 文档：`dev_docs/DEV_TEST/接口文档/API-设备检查器.md` 总览 8 → 9 端点，补「一键清空」小节，并在列表小节写明「最多返回上限条、total 为真实总数」

## 3. 前端：一键清空入口

- [x] 3.1 `api.ts` 增 `apiClearSnapshots()`（DELETE，唯一 HTTP 出口）；`store.clearSnapshots()` 调用后刷新列表并把分层数据、快照元信息与选中元素一起复位。验证：store 用例断言「成功后列表为空、分层状态复位」「失败时给出可读原因且状态不被清空」
- [x] 3.2 抽屉新增「一键清空」按键：二次确认（文案写明全部历史与未被引用的媒体不可恢复）、确认后调用清空端点、无快照时禁用。验证：用例断言按键存在且空列表时不可用；确认文案含「不可恢复」
- [x] 3.3 移除抽屉里「已显示最近 N 条」的截断提示（列表封顶后该分支恒不成立）。验证：抽屉对总数只呈现「共 N 条」

## 4. 存量清理与门禁

- [x] 4.1 一次性清空既有快照（按用户逐个调用清空），记录清理前后条数与媒体文件数。验证：`Snapshot.objects.count() == 0`；元素定位侧 2 个页面 / 16 个元素仍引用的 `inspector/` 媒体文件仍在
- [x] 4.2 后端门禁：`python manage.py check`、`makemigrations --check`、`ruff check` + `format --check`、`pytest tests/graybox -q`、`python tools/gen_arch_stats.py --check-boundaries`。验证：全部通过
- [x] 4.3 前端门禁：`npm run lint:styles`、`npx vue-tsc --noEmit`、`npx vitest run`、`npx vite build`。验证：全绿（既有无关报错如实记录）
