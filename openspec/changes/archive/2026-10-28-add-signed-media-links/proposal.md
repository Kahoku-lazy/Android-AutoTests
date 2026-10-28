# 截图短时签名直链

## Why

在浏览器地址栏直接打开 `/api/tasks/{id}/media/{id}/` 会 401：该端点只认 `Authorization: Bearer <JWT>`，而浏览器地址栏发不出这个头；页面里的 `blob:` 地址只对当前页面有效，复制到新标签或别的机器就打不开。局域网里想直接看图、或把某张图贴到别处，需要一条带签名的短时直链。

## What Changes

- 新增登录后可调用的签发接口 `POST /api/tasks/{task_id}/media/{media_id}/link/`，返回 `{url, expires_at}`；`url` 是相对路径，前端按当前 origin 补全。
- 新增签名直链端点 `GET /media/signed/{task_id}/{media_id}/{expires}/{signature}/`：用服务端密钥对 `task_id:media_id:expires` 做 HMAC-SHA256，默认 **15 分钟**有效；过期或签名不符返回 403，图片不存在返回 404。
- 直链沿用现有字节语义：`Content-Type: image/webp`、ETag、304、immutable 缓存；不泄露其它图片。
- 前端缩略图新增「在新标签打开」按钮：先调用签发接口，再用新窗口打开直链。
- 原有 `GET /api/tasks/{id}/media/{id}/`（JWT + 任务可见性）保持不变。

## 关联文档

无关联 PRD：本次为图片交付方式的补充，验收以「登录可签发、浏览器可直接打开、过期/篡改被拒」为准。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `task-media-delivery`: 新增「单图短时签名直链」要求（签发接口、签名端点、过期语义）。

## Impact

- 后端：`backend/config/settings.py`（`MEDIA_LINK_SECRET` / `MEDIA_LINK_TTL_SECONDS`）、新增 `backend/apps/task_list/media_links.py`、`api.py`、`views.py`、`urls.py`、`backend/config/urls.py`（签名路由挂在已被中间件放行的 `/media/` 下）。
- 前端：`frontend/src/modules/task-list/api/tasks.ts`、`components/TaskMediaThumb.vue`（新标签打开）。
- 契约：新增两个端点，进入 OpenAPI 基线；现有报告与取图契约不变。
- 安全：直链短时、单图绑定、不可篡改；不改变现有 JWT 体系，不引入 Cookie 会话。
