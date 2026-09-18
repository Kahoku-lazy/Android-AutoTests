## Why

用户给智能体发图片时对话**异常终止**：后端日志 18:25:53 连续报 `django.core.exceptions.RequestDataTooBig: Request body exceeded settings.DATA_UPLOAD_MAX_MEMORY_SIZE`——Django 默认请求体上限 2.5MB，而平台允许的 5MB 图片经 base64 编码约 6.7MB，SSE 请求（`chat_stream`）在解析 JSON 之前就被拦截，流从未建立，前端表现为断流报错。应用层其实已有 5MB 图片校验（`chat_views._MAX_IMAGE_BYTES`），缺的只是请求体预算。

## What Changes

1. **P0** `config/settings.py`：新增 `DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024`——覆盖 5MB 图片 base64（≈6.7MB）+ JSON 开销；超限图片仍由应用层 `_normalize_images` 以"图片过大（最大 5MB）"友好拒绝。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.9（图片 ≤5MB、流式对话）
- 现场证据：`logs/backend.log` 18:25:53 `RequestDataTooBig`（`chat_views.py:90` 读 body 时抛出）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 配置修复（请求体预算与产品口径对齐），无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`config/settings.py`（+1 行）
- 测试范围：`manage.py check`；settings 值生效验证；5MB 图片 base64（≈6.7MB）< 16MB 算术确认；真实对话发图复测（用户）
