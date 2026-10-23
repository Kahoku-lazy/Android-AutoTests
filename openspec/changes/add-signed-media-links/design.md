## Context

现有取图端点 `GET /api/tasks/{id}/media/{id}/` 依赖 JWT 中间件识别用户，地址栏无法直接访问。`/media/` 已经是网关的公开前缀（DEBUG 下由 Django 提供上传文件），可以复用它承载签名直链，避免把 `/api/tasks/*` 变成有条件公开。

## Goals / Non-Goals

**Goals:**

- 登录用户能为单张截图签发 15 分钟直链，浏览器新标签直接打开。
- 不改变现有 JWT 取图、报告与缓存语义。

**Non-Goals:**

- 不做整任务/整报告批量分享，不做免登录访问全部截图。
- 不引入 Cookie 会话或 OAuth。
- 不做访问审计、下载计数与防盗链（单图短时已经足够）。

## Decisions

**1. 直链挂在 `/media/signed/...`，而不是 `/api/...`。**

`/media/` 已在 `PUBLIC_PREFIXES`（Django 静态上传文件），签名视图设置 `AllowAny` 并在视图内校验签名与过期。这样不必把 `/api/tasks/*` 变成“带 `?t=` 就跳过 JWT”的宽口子，风险面最小。

**2. 签名放路径，不放查询串。**

`/media/signed/<task>/<media>/<expires>/<signature>/`：路由参数直接校验，不经查询解析；代价是签名会出现在访问日志与浏览器历史里——短 TTL、单图绑定、不可跨图复用，可接受。

**3. HMAC-SHA256 + `expires` 秒级时间戳。**

密钥取 `MEDIA_LINK_SECRET`，未配置时回退 `DJANGO_SECRET_KEY`；TTL 取 `MEDIA_LINK_TTL_SECONDS`（默认 900，限制 60–3600）。校验用 `hmac.compare_digest`，`expires` 早于当前时间即拒绝。换密钥会让所有已发链接立即失效，这是预期行为。

**4. 返回相对 URL。**

请求经过 Vite 代理后 Django 看到的 Host 是 `localhost:8766`，`build_absolute_uri` 会生成局域网打不开的地址。接口只返回 `/media/signed/...`，前端用 `new URL(path, window.location.origin)` 补全，局域网访问时自动是当前主机名。

**5. 复用现有字节响应与前端组件。**

后端抽出 `media_payload()` 与 `_media_response()`，签名端点与 JWT 端点的 `Content-Type` / ETag / 304 / `immutable` 完全一致。前端 `TaskMediaThumb` 增加一个按钮：同步开空窗口，拿到链接后再导航，避免异步 `window.open` 被拦截。

## 模块防火墙自检

- 新增 `media_links.py` 为纯签名工具；`api.py` 负责可见性校验；`views.py` 只分发与组装响应。
- 签名路由在根 `urls.py` 注册，视图仍属于 `task_list`；无跨 App import。

## Risks / Trade-offs

- [链接被转发] → 15 分钟自动失效，且只能看单张图。
- [密钥轮换失效] → 预期；文档说明。
- [访问日志留下签名] → 短时且单图，风险有限；若不接受，可改为 Cookie 方案。
- [签名路由与 DEBUG 静态 `/media/` 冲突] → 显式路由在 `static()` 追加之前注册，优先匹配。
