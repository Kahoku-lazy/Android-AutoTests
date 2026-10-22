## 1. 后端：报告只下发引用

- [x] 1.1 `backend/apps/task_list/task_reports.py`：`_item()` 用 `event.media_id` 填 `media_id`（无图为 `null`），删除 `_thumb()`；`python -m pytest -c tests/pytest.ini tests/api/test_task_event_flow.py` 通过
- [x] 1.2 新增单测断言报告里没有 `thumb` 与 `data:image`，且 `media_id` 与媒体行一致（134 载荷 5.91MB → 1.25MB）

## 2. 后端：截图字节端点

- [x] 2.1 `backend/apps/task_list/api.py` 新增 `get_task_media(user_id, task_id, media_id)`：校验任务可见性与图片归属
- [x] 2.2 `views.py` 新增 `TaskMediaAPIView`（`HttpResponse` + `Content-Type: image/jpeg` + `ETag` + `Cache-Control` + `If-None-Match` → 304 + `@extend_schema` 二进制响应）；`urls.py` 注册 `tasks/<int:task_id>/media/<int:media_id>/`
- [x] 2.3 接口测试：可见用户 200、304、越权/不存在 404、未登录 401；`python -m pytest -c tests/pytest.ini tests/api/test_task_media.py` 5 项通过

## 3. 后端：采集上限 300

- [x] 3.1 `api.store_task_media` 上限 40 → 300（常量 `TASK_MEDIA_LIMIT`），去重与"只存缩略图"不变
- [x] 3.2 改写 `tests/api/test_task_event_store.py::test_media_cap_and_cascade_delete` 为 300 张上限；pytest 通过

## 4. 前端：懒加载取图

- [x] 4.1 `frontend/src/modules/task-list/api/tasks.ts` 增加 `getTaskMedia(taskId, mediaId)`（`responseType: "blob"`）
- [x] 4.2 新增 `frontend/src/modules/task-list/components/TaskMediaThumb.vue`：IntersectionObserver 懒加载、object URL、加载占位、失败隐藏、卸载释放
- [x] 4.3 `TaskDetailPage.vue` 用该组件替换 `<img :src="item.thumb">`；`npx vue-tsc --noEmit` 退出码 0、`npm run build` 随门禁通过

## 5. 门禁与归档

- [x] 5.1 重新生成 `openspec/openapi.yaml` 基线（新增 `/api/tasks/{task_id}/media/{media_id}/`，`task_media`）
- [x] 5.2 `python run.py check` 22/22 阻塞项通过；`openspec validate task-media-delivery --strict` 通过；全量 `unit or integration` 44 项失败与改动前逐条同文件一致（新增失败 0，通过数 369 → 375）
- [x] 5.3 归档变更并提交
