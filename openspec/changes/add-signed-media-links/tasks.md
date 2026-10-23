## 1. 后端签名与接口

- [x] 1.1 `settings.py`：新增 `MEDIA_LINK_SECRET`（缺省回退 `DJANGO_SECRET_KEY`）与 `MEDIA_LINK_TTL_SECONDS`（默认 900，限制 60–3600）。验证：`manage.py check`。**验证结果**：配置已生效，`manage.py check` 无问题。
- [x] 1.2 新增 `backend/apps/task_list/media_links.py`：`sign()` / `verify()` / `build_path()`；HMAC-SHA256、`compare_digest`、过期判断。验证：单测覆盖正常、过期、篡改、换 media_id。**验证结果**：11 个用例覆盖签发、过期 403、篡改 403、换图 403、TTL 上限 3600。
- [x] 1.3 `api.py`：抽出 `media_payload()` 与 `_visible_media()`；新增 `create_task_media_link()`（可见性校验 + 签发）与 `get_media_by_id()`。验证：现有取图测试全绿。**验证结果**：`test_task_media.py` 8 passed。
- [x] 1.4 `views.py` + `urls.py`：新增 `POST /api/tasks/{id}/media/{id}/link/`（JWT，返回 `{url, expires_at}`）与 `GET /media/signed/{task}/{media}/{expires}/{signature}/`（`AllowAny` + 签名校验，403/404 语义）。验证：接口测试覆盖签发、直接打开、过期、篡改、越权、304。**验证结果**：新增 `media_views.py` 承载两个视图；`test_task_media_links.py` 11 passed。
- [x] 1.5 `backend/config/urls.py`：在 DEBUG 静态路由之前注册签名路由。验证：直链在 `DEBUG=True` 下命中视图而不是静态 404。**验证结果**：真实服务 `curl` 直链返回 `200 image/webp`，篡改签名返回 `403`。

## 2. 前端入口

- [x] 2.1 `frontend/src/modules/task-list/api/tasks.ts`：新增 `createTaskMediaLink()`。验证：typecheck。**验证结果**：`vue-tsc --noEmit` 通过。
- [x] 2.2 `TaskMediaThumb.vue`：图片加载完成后显示「在新标签打开」，点击签发并导航；失败静默关闭窗口。验证：组件单测 + typecheck。**验证结果**：`TaskMediaThumb.spec.ts` 2 passed（成功导航、失败关窗）；prettier/typecheck 通过。

## 3. 验证与门禁

- [x] 3.1 后端测试：`tests/api/test_task_media_links.py`（新增）与现有 `test_task_media.py` 全绿。验证：pytest。**验证结果**：19 passed。
- [x] 3.2 手工直链：对本机一张图签发并 `curl` 打开，确认 `200 image/webp`；篡改 `403`。验证：命令输出。**验证结果**：`/media/signed/142/1541/<expires>/<sig>/` → `200 image/webp`；替换签名为全 0 → `403`。
- [x] 3.3 静态与规格门禁：`ruff check` / `ruff format --check` / `openspec validate add-signed-media-links --strict`；OpenAPI 基线补上两个新端点。验证：退出码 0。**验证结果**：ruff 全过；openspec valid；基线新增 `link` 与 `signed` 两条路径。另发现新增非 `/api` 路由会让 drf-spectacular 重算公共前缀、改写全部 operationId/tag，已在 `SPECTACULAR_SETTINGS` 固定 `SCHEMA_PATH_PREFIX = "/api"`（独立提交 `fix(api)`），干净检出生成结果与基线逐字节一致。
