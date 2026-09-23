## REMOVED Requirements

### Requirement: 端点资产目录与路由表一致

**Reason**: 该能力的载体是元素定位模块的 `ApiGroup` / `ApiEndpoint` 两张表与工具 `tools/seed_api_endpoints.py`。本次 Web/API 域整体下线，两张表随迁移删除、工具一并删除，能力失去载体，其守护也随之不存在。

**Migration**: 平台自身的 API 描述不再以「接口资产」形式落库可供接口测试选用；接口契约改由 `tests/api/` 的 YAML 用例与后端路由表直接断言。守护侧由四面收敛为三面（前端 API 层 / tests 调用面 / YAML 用例），原「目录规模下限」一并移除。
