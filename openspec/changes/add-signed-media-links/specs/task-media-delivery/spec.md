## ADDED Requirements

### Requirement: 单图短时签名直链

系统 SHALL 提供 `POST /api/tasks/{task_id}/media/{media_id}/link/` 签发单张截图的直链。该接口 MUST 要求登录，并 MUST 校验任务对当前用户可见；任务不可见或图片不属于该任务时 MUST 返回 404。响应 MUST 为 `{status: true, data: {url, expires_at}}`，其中 `url` MUST 指向 `GET /media/signed/{task_id}/{media_id}/{expires}/{signature}/`，`expires` 为 Unix 秒。

签名 MUST 使用服务端密钥对 `task_id:media_id:expires` 计算 HMAC-SHA256。链接 MUST 在 `expires` 之前有效，有效期 MUST 不超过 1 小时；签名不存在、签名不符或已过期时 MUST 返回 403。图片行不存在或文件缺失时 MUST 返回 404。直链 MUST 只返回该 `media_id` 的字节，并 MUST 沿用 `Content-Type: image/webp`、`ETag` 与命中 `If-None-Match` 时的 304 语义。

#### Scenario: 签发后浏览器可直接打开

- **WHEN** 已登录用户对可见任务的截图调用签发接口，并在浏览器新标签打开返回的 `url`
- **THEN** 返回 200、`Content-Type: image/webp` 与可解码的 WebP 字节

#### Scenario: 链接过期

- **WHEN** 当前时间晚于链接中的 `expires`
- **THEN** 返回 403，不返回图片字节

#### Scenario: 签名被篡改或换一张图

- **WHEN** 修改链接中的 `signature`，或把同一签名用到另一个 `media_id`
- **THEN** 返回 403，不返回图片字节

#### Scenario: 不可见任务不能签发

- **WHEN** 用户请求另一个用户任务的截图链接
- **THEN** 返回 404

#### Scenario: 直链沿用缓存语义

- **WHEN** 用仍然有效的直链再次请求并带上上一次返回的 `ETag`
- **THEN** 返回 304，且不返回图片字节
