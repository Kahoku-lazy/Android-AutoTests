## Why

D0 复检发现：D0 配置的 OpenAPI 面（`REST_FRAMEWORK.DEFAULT_SCHEMA_CLASS` + `SPECTACULAR_SETTINGS` + `config/urls.py` 的 `/api/schema/` `/api/swagger/`）**产出质量不合格**——`python manage.py check --deploy` 报出 **155 条 drf-spectacular 告警**，即 `/api/schema` 对这些端点的描述是缺失/降级的。

实测分布（`temps/schema_warn_stats.py` → `temps/schema_warn_stats.txt`，2026-09-14）：

```
告警总数 = 155
按告警类: W001=96, W002=59
按 App: ai_assistant=53 · device_pool=20 · element_locator=19 · case_manager=14
        device_inspector=14 · dashboard=8 · evaluator=8 · accounts=7 · workflow=5 · (非 apps)=7
Top 文件: ai_assistant/views_drf.py=28 · device_pool/views.py=20 · case_manager/views_drf.py=14
         device_inspector/views.py=14 · ai_assistant/views_knowledge_drf.py=10
         element_locator/views_projects_drf.py=9 · dashboard/views.py=8 · accounts/views.py=7
```

两类根因：

- **W001（96 条，可一次性消除大部分）**：`drf_spectacular.W001 could not resolve authenticator <class 'shared.auth.drf_auth.JWTAuthentication'>. There was no OpenApiAuthenticationExtension registered for that class.` —— 每遇到一个视图重复一次，属**单点缺失**（缺一个认证扩展注册）；另有少量是 serializer 方法缺类型提示（`ai_assistant/serializers.py` 的 `get_api_key` / `get_available_models` / `get_base_url` / `get_last_checked_at` / `get_route_configs`，`evaluator/serializers.py`）。
- **W002（59 条）**：`unable to guess serializer`（对函数式 APIView / 裸 ViewSet）与 `could not derive type of path parameter "id" because it is untyped and obtaining queryset from the viewset failed`（ViewSet 的 `get_queryset` 依赖 request，schema 生成期拿不到）——需按视图补 `serializer_class` / `@extend_schema` / `@extend_schema_view`。

## What Changes

**只加 schema 元数据，不改任何请求/响应行为**：

1. **认证扩展（治 W001 主体）**：为 `shared.auth.drf_auth.JWTAuthentication` 注册 `OpenApiAuthenticationExtension`（新增 `shared/auth/schema.py`，并在 `SPECTACULAR_SETTINGS` 配 `APPEND_COMPONENTS`/`SECURITY` 或由扩展自行声明 bearer 方案）。
2. **按 App 补 serializer/schema 标注（治 W002 + 剩余 W001）**，分批：
   - `dashboard/views.py`（8）· `device_inspector/views.py`（14）· `device_pool/views.py`（20）；
   - `case_manager/views_drf.py`（14）· `element_locator/views_{projects_,}drf.py`（19）· `workflow/views_api.py`（5）· `evaluator/`（8）；
   - `ai_assistant/`（53，最大头：`views_drf.py` 28 + `views_knowledge_drf.py` 10 + `views_toolbox_drf.py` 6 + `serializers.py` 5 + `views_upload_drf.py` 4）；
   - `accounts/views.py`（7，多为认证扩展连带消除）。
3. **验证阈值**：告警数从 155 降到 **0**；若个别项确不可解（如动态 `get_queryset`），必须在 tasks 里登记「保留项 + 理由」，不允许静默残留。

## 关联文档

- 取证：`temps/schema_warn_stats.py` · `temps/schema_warn_stats.txt` · `python manage.py check --deploy`
- 契约真相源：各 App Serializer + `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`
- 相关单据：`fix-d0-config-drift`（`api_docs.py` 手写文档治理；其「改由 schema 渲染」依赖本单完成）
- 范围外：不重命名端点、不改路径、不动响应信封

## Capabilities

### New Capabilities

（无；`.openspec.yaml` 已声明 `skip_specs: true`）

### Modified Capabilities

（无——schema 元数据不构成需求级行为变化）

## Impact

- **修改**：`shared/auth/`（新增 schema 扩展）· 各 App `views*.py` / `serializers.py`（仅加 `serializer_class` / `@extend_schema` / 类型提示）· `config/settings.py`（`SPECTACULAR_SETTINGS` 安全方案声明）
- **不影响**：请求/响应结构、鉴权、路由、DB、前端（`/api/schema` 内容变准，形状不变）
- **测试范围**：`manage.py check` + `check --deploy`（告警 155 → 目标 0）· `manage.py spectacular --validate` 生成并校验 schema · `pytest -m "unit or integration"` · `ruff` · `--check-boundaries`
