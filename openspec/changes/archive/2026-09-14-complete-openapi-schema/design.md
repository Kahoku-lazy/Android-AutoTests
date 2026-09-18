## Context

- 告警分布实测见 proposal；`W001` 单类占 96 条，且多数是**同一个缺失扩展**在逐个视图上报——先做它能最快看到收敛曲线。
- `shared.auth.drf_auth.JWTAuthentication` 是全局默认认证类（`config/settings.py:249-251`），因此该扩展的影响面覆盖所有 DRF 端点。
- 视图侧问题形态已知：函数式 `@api_view`/`APIView` 缺 `serializer_class`（W002）；`ViewSet.get_queryset()` 依赖 `request.user`，schema 生成期无法求值（path 参数类型推断失败）。

## Goals / Non-Goals

**Goals:**

- `/api/schema` 能**准确**描述现有端点（认证方案 + 请求/响应体 + 路径参数类型），`check --deploy` 的 spectacular 告警清零。

**Non-Goals:**

- 不改任何端点行为、路径、字段、信封（纯元数据）；
- 不为「让告警消失」而简化/隐藏端点（禁止 `@extend_schema(exclude=True)` 之类掩盖手段，除非端点确实要退出文档——那需单独登记）；
- 不重写 Serializer 结构。

## Decisions

**D1 先做认证扩展，再按 App 补 serializer 标注。**
理由：`W001` 96 条共享一个根因，先修它可以把「真实剩余量」暴露出来（预期从 155 降到 ~60），避免按 App 盲改。

**D2 路径参数类型问题用 `@extend_schema_view` + 显式参数标注解决，而不是把 `get_queryset` 改成静态。**
理由：`get_queryset` 依赖 `request.user` 是**业务隔离要求**（用户项目隔离），为文档便利而弱化它属反向优化。

**D3 每个 App 补完后立刻跑一次告警统计，收敛曲线写进 tasks。**
理由：跨 9 个 App 的批量元数据改动容易「改着改着跑偏」；分 App 度量可及时发现某类告警需要换修法。

**D4 `SPECTACULAR_SETTINGS` 增加 bearer 安全方案声明（`SECURITY` / `APPEND_COMPONENTS`），与 `/api/swagger` 的 Authorize 按钮对齐。**
理由：公开的 Swagger UI 若不能输入 Bearer 令牌，文档只能读不能用；这属本次「让 schema 可用」的一部分。

## Risks / Trade-offs

- [为消 155 条告警给大量视图加标注 → diff 很大、触碰多个 App] → 严格限制在 schema 元数据（`serializer_class` / `@extend_schema` / 类型提示）；分 App 提交式推进并每批回归 `pytest -m "unit or integration"`。
- [动态 `get_queryset` 的 ViewSet 可能仍无法自动推断] → D2 的显式标注；若仍无解，tasks 要求登记保留项与理由，不静默放过。
- [schema 变更影响前端消费 `/api/schema`] → 前端未消费 schema（grep 证据为零），且本次只让描述更准确。
- [新增 `shared/auth/schema.py` 需被 DRF 自动发现] → drf-spectacular 通过「模块内定义`OpenApiAuthenticationExtension` 子类」的导入约定生效；tasks 里以「告警数下降」验证被发现（必要时在 `SPECTACULAR_SETTINGS` 的 `EXTENSIONS`/`APPEND_COMPONENTS` 显式登记）。
