## REMOVED Requirements

### Requirement: /api 请求的尾斜杠双向容错

**Reason**: 该能力由 `gateway/normalize_slash.NormalizeTrailingSlashMiddleware` 提供，本变更删除该中间件并关闭
`settings.APPEND_SLASH`，改为「`/api/` 路由唯一写成带尾斜杠 + 缺失即 404」的严格约定
（见新能力 `api-path-convention`）。容忍两种写法使约定长期无法收敛，且需要同时维护
「两条路径都活」与「路由定义混乱」两件事。

**Migration**: 全部调用方已改为带尾斜杠的路径 —— 前端 api 层（129 个调用点）、
`tests/api/case/*.yaml`（43 处）、`tools/seed_api_endpoints.py`（175 处端点资产路径）、
以及 `tests/graybox/unit/` 下硬编码 `/api/` 路径的用例。
