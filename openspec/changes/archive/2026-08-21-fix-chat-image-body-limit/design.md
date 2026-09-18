## Context

- Django 默认 `DATA_UPLOAD_MAX_MEMORY_SIZE=2.5MB`，项目未覆盖；`chat_stream` 读取 `request.body` 时超过即抛 `RequestDataTooBig`（413 语义），SSE 无法建立。
- 平台图片口径 5MB（PRD-08 F-02-04；前端 `MAX_IMAGE_UPLOAD_SIZE`），base64 膨胀 ≈1.33×。
- 应用层已有解码后 5MB 校验（`_MAX_IMAGE_BYTES`），无需新增校验逻辑。

## Goals / Non-Goals

**Goals:**

- ≤5MB 图片的对话请求能正常进入流式对话；>5MB 图片被应用层友好拒绝（"图片过大"），而非框架层崩溃。

**Non-Goals:**

- 不调整图片 5MB 产品口径；不改前端；不改 multipart 上传（`FILE_UPLOAD_MAX_MEMORY_SIZE` 非本次问题路径）。

## Decisions

**D1：`DATA_UPLOAD_MAX_MEMORY_SIZE` 设为 16MB。**
5MB×4/3≈6.67MB base64 + JSON 冗余 < 16MB，留足余量且不过度放宽（超限仍由应用层 5MB 校验拦截）。

**D2：不另设前端/应用层改动。**
`_normalize_images` 已具备解码后尺寸校验与友好文案，天然承接。

## 模块防火墙自检

- 仅全局配置项，无写库/跨模块/通道变更。✅

## Risks / Trade-offs

- [请求体预算放大后，超大 base64 可能进入 JSON 解析] → 16MB 为上限，解析成本可控；语义层 5MB 校验仍兜底。
