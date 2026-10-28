# task-media-delivery Specification

## Purpose
定义任务截图媒体从前端可见到落库的交付契约：任务流程报告只携带图片引用，图片字节走独立的鉴权端点按需获取，采集按内容去重、不设张数上限。

## Requirements

### Requirement: 任务流程报告只携带图片引用

`GET /api/tasks/{task_id}/report/` 的每个事件项 MUST 用整数 `media_id` 表示它关联的截图（无图时为 `null`），MUST NOT 内联 `data:` 形式的 base64 图片，MUST NOT 携带 `thumb` 字段。同一事件只对应一张图。

#### Scenario: 有图的事件只给引用

- **WHEN** 某条工具返回结束事件关联了一张缩略图，读取该任务的流程报告
- **THEN** 该项的 `media_id` 为该图片行的整数编号，响应体内不出现 `data:image` 与 `thumb` 字段

#### Scenario: 无图的事件给空引用

- **WHEN** 某条事件没有关联图片
- **THEN** 该项的 `media_id` 为 `null`

#### Scenario: 报告体量只含布局与文本

- **WHEN** 一个含 900 条事件、70 张缩略图的任务请求流程报告
- **THEN** 响应体不含任何图片字节，体量由事件文本决定

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

### Requirement: 前端按需加载截图

任务详情页 SHALL 在事件项进入可视区域时才请求该图片字节，并在组件卸载时释放 object URL；加载期间 SHALL 显示占位，加载失败 SHALL 隐藏图片本身而不阻断事件时间线。页面 MUST NOT 在打开时一次性请求全部截图。

#### Scenario: 首屏只加载可见截图

- **WHEN** 打开一个含 900 条事件、大量截图的任务详情页
- **THEN** 只对进入视口的事件项发起图片请求，其余项不发请求

#### Scenario: 图片请求失败不影响时间线

- **WHEN** 某张图的请求返回 404 或网络错误
- **THEN** 该事件项仍正常显示文字内容，图片区域不出现破图图标

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
