## Context

见 proposal.md 的实测数据。现有实现的两个约束决定了方案：

1. 截图字节只存在 `task_media.thumb_b64`（720px JPEG 的 base64 文本），报告接口把它内联成 `data:` URI；没有第二次读取路径。
2. 前端 JWT 只走 `Authorization` 头（`backend/gateway/middleware.py`），`<img src>` 无法携带该头，所以"直接给 img 一个 URL"这条路走不通。

## Goals / Non-Goals

**Goals:**

- 任务流程报告不再内联图片：134 的 5.91MB 载荷降到只含文本。
- 截图按需取：可见才请求、缓存可复用、越权取不到。
- 采集上限从 40 提到 300，多用例任务不再"只有第一条用例有图"。

**Non-Goals:**

- 不落原图、不做原图放大（仍是 720px 缩略图）。
- 不做执行中的实时推送（WS/SSE 仍是 0 生产点）。
- 不改测试报告列表/详情页的图片能力（那两处本来就不渲染截图）。
- 不改变量任务的既有图片行（历史被丢弃的图无法恢复）。

## Decisions

### 1. 报告只给 `media_id`，字段名从 `thumb` 改掉

`_item()` 用 `event.media_id` 填 `media_id`，删掉 `_thumb()`。刻意**不保留** `thumb` 兼容字段：留着就会有人继续内联 base64，载荷问题原样回来。发布顺序上后端先上、前端后上时，旧前端只是不显示图片（`item.thumb` 为 undefined），不会报错。

### 2. 字节端点用 DRF 视图 + `HttpResponse`，不走全局信封

`GET /api/tasks/{task_id}/media/{media_id}/` 返回 `image/jpeg` 原始字节。全局 `{status, data}` 信封有既定的"文件下载例外"，媒体字节按同一口径处理，并在 OpenAPI 里声明成 `binary`。

鉴权与归属：JWT 由既有中间件处理；视图内用 `filter_agents_for_user` 判任务可见性，任务不可见与 `media_id` 不属于该任务一律 404（不区分"无权"与"不存在"）。

缓存：`ETag` 取图片行上的 `sha256`（内容寻址，天然不变），`Cache-Control: private, max-age=31536000, immutable`；`If-None-Match` 命中直接 304。`private` 是因为不同用户对同一任务的可视性不同。

备选：
- **给 `<img>` 一个带签名 token 的 URL**：要多一条短期签名链路，且 token 会进浏览器历史与日志，收益不如 blob。
- **把 base64 继续内联但压缩到每步一张**：治不了"总量随任务长度线性增长"。

### 3. 前端用 axios 取 blob + IntersectionObserver 懒加载

新增 `TaskMediaThumb`（task-list 私有组件）：`IntersectionObserver` 进视口 → `getTaskMedia(taskId, mediaId, etag)`（axios，带 JWT）→ `URL.createObjectURL`；卸载或换图时 `revokeObjectURL`。加载中显示固定尺寸占位（避免滚动抖动），失败隐藏图片。

为什么不用 `<img loading="lazy">`：它只解决"何时发请求"，但 `<img src>` 带不上 JWT，仍会被 401。

### 4. 上限 300，而不是无限

300 张 × 720px JPEG@80（约 30–90KB）≈ 9–27MB/任务的库内体积；配合 sha256 去重（同一画面只存一份），实测 134 的 124 张截图里不同画面远少于 124。300 覆盖了本轮所有多用例任务（135 共 191 张截图）。不做的替代方案是"按步骤只留首尾两张"，但流式写入拿不到"最后一张"的预知，且会丢掉中间取证画面，收益不抵损失。

### 5. 不改 `_item()` 的 `count == 1` 条件

合并后的增量行本来就不该配图；图片只挂在非增量的工具返回结束事件上，这个条件保持原样。

## 模块防火墙自检

- 视图只分发：取图逻辑放 `api.get_task_media()`，视图不直写 ORM。
- 前端只经本模块 `api/tasks.ts` 调 `/api/tasks/*`，不新增跨模块 import。
- 不新增 App、不新增表、不涉及数据库迁移。

## Risks / Trade-offs

- [每个可见图一次额外请求] → 只对进视口的项发；`immutable` + `ETag` 让重复浏览走缓存（304）。
- [`task_media` 表体积上升（上限 40 → 300）] → 只存缩略图；如需收敛，后续按任务创建时间做保留期清理，本次不做。
- [旧前端在新后端上不显示图] → 图片区静默消失，事件时间线不受影响；前后端同批发布即可。
- [blob 泄漏] → 组件卸载与 media 变更时 `revokeObjectURL`。

## Migration Plan

1. 后端先发布：报告改字段、新端点上线、上限提高；旧前端只是看不到图。
2. 前端随后发布：切到 `TaskMediaThumb`。
3. 回滚：前端回滚会回到"没有图"（旧字段已不存在），接口无破坏性变更（仅移除字段），无需数据迁移。

## Open Questions

无。
