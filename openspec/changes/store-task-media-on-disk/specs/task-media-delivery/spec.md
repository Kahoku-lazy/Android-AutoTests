## MODIFIED Requirements

### Requirement: 截图字节走独立鉴权端点

平台 SHALL 提供 `GET /api/tasks/{task_id}/media/{media_id}/` 返回该缩略图的 WebP 字节。该端点 MUST 要求登录，并 MUST 校验任务对当前用户可见；任务不可见或图片不属于该任务时 MUST 返回 404，MUST NOT 泄露图片是否存在。响应 MUST 带 `Content-Type: image/webp`、`ETag`（取图片内容的 sha256）与 `Cache-Control: private, max-age=31536000, immutable`；请求头 `If-None-Match` 与该 `ETag` 相同时 MUST 返回 304 且无响应体。

#### Scenario: 可见任务取图成功

- **WHEN** 已登录且拥有该任务的用户请求其中一张缩略图
- **THEN** 返回 200、`Content-Type: image/webp`、可解码的 WebP 字节与 `ETag`

#### Scenario: 重复请求走缓存

- **WHEN** 同一张图再次请求并带上上一次返回的 `If-None-Match`
- **THEN** 返回 304，且不返回图片字节

#### Scenario: 越权与不存在的图都返回 404

- **WHEN** 请求者不拥有该任务，或 `media_id` 不属于该任务
- **THEN** 都返回 404，响应体不包含图片数据

#### Scenario: 未登录被拦截

- **WHEN** 不带 JWT 请求该端点
- **THEN** 返回 401，不返回图片字节
