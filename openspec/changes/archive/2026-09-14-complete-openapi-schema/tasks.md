## 1. 认证扩展（治 W001 主体）

- [x] 1.1 新增 `shared/schema.py`：`JWTAuthenticationScheme(OpenApiAuthenticationExtension)`，`target_class = "shared.auth.drf_auth.JWTAuthentication"`、`name = "jwtAuth"`，安全方案 `http bearer`（`bearerFormat: JWT`）
- [x] 1.1b 扩展注册方式实测：drf-spectacular 用「类定义即注册」的元类收集扩展，但**不会**自动导入 `shared/schema.py`（在安装包源码中搜 `schema.py` 零命中）——只建文件时认证器告警仍有 69 条。改为新增 `shared/apps.py::SharedConfig.ready()` 中 `from . import schema`（在 `django.setup()` 期间、任何 schema 生成之前完成注册）→ 认证器告警 **69 → 0**
- [x] 1.2 无需额外改 `SPECTACULAR_SETTINGS`：扩展注册后生成的 schema 自动含 `components.securitySchemes.jwtAuth`（`temps/schema_final.yaml` 复核：`contains securitySchemes = True`、`jwtAuth = True`）
- [x] 1.3 验证：`could not resolve authenticator` 告警 **0**；告警总数 **155 → 80**（降幅 75）；`manage.py check` 零 issues；Django 自动识别 `shared.apps.SharedConfig`；`shared` 仍正常加载（`apps.get_app_config("shared")` = `shared.apps.SharedConfig`）

## 2. 按 App 补 schema 标注（80 → 5 → 0）

剩余 80 条的构成（`temps/schema_warn_stats2.py`）：`unable to guess serializer` 57 · `unable to resolve type hint` 14 · `could not derive type of path parameter` 7 · 其他 2。按**文件互不重叠**分 4 组并行处理：

- [x] 2.1 `apps/ai_assistant/`（views_drf · serializers · views_knowledge_drf · views_toolbox_drf · views_upload_drf）**29 → 0**：函数/类视图补 `responses=OpenApiTypes.OBJECT`（有真实入参 Serializer 的用 `ModelDetectInputSerializer`/`TaskSubmitInputSerializer`/`MessageInputSerializer`/`RenameInputSerializer`）；5 个 `SerializerMethodField` 加 `@extend_schema_field`；`ConversationViewSet` 6 个 action 全部显式标注 + `task_detail` 声明 `run_id` 路径参数
- [x] 2.2 `device_pool/views.py`（10）+ `dashboard/views.py`（4）+ `workflow/views_api.py`（2）**16 → 0**：`@api_view` 函数补 `@extend_schema`（置于 `@api_view` 之上）；dashboard 3 个返回 dict 的 APIView 用 `OBJECT`、返回 list 的用 `ANY`；`WorkflowPrototypeViewSet` 加 `serializer_class` + `queryset = ...objects.none()`（仅 schema 元数据）
- [x] 2.3 `case_manager/views_drf.py`（9）+ `device_inspector/views.py`（7）**16 → 0**：4 个 ViewSet 用 `@extend_schema_view` 逐 action 声明；`snapshot_detail` 等 7 个 `@api_view` 补 `@extend_schema`
- [x] 2.4 `accounts/views.py`（5）+ `evaluator/serializers.py`（5）+ `element_locator/{views_projects_drf,serializers}.py`（9）**19 → 0**：登录四件套按真实 Serializer 标注、`MeView` / 知识库视图用 `OBJECT`；`evaluator` 5 个 `SerializerMethodField` 加返回类型注解；`LocatorDirectoryViewSet` 的 `partial_update`/`destroy` 显式声明 `OpenApiParameter("id", int, PATH)`（drf-spectacular 的 `SCHEMA_COERCE_PATH_PK` 会把 `pk` 归一化成 `id`，故参数名写 `id`）
- [x] 2.5 **收尾（父 Agent 本人做）**：`--validate` 仍报 **5 条 operationId 碰撞**（`ai_agent_tasks_retrieve` · `ai_conversations_tasks_retrieve` · `cases_projects_retrieve` · `elements_projects_retrieve` · `inspector_snapshots_retrieve`，均为「列表端点与详情端点撞名」）→ 给 5 处补显式 `operation_id`（`ai_agent_task_detail` · `ai_conversation_task_detail` · `cases_projects_list` · `elements_projects_list`/`elements_project_detail` · `inspector_snapshot_detail`）。中途在 `element_locator` 上踩到一次回归：把类级 `@extend_schema` 换成 `@extend_schema_view` 后其余 action 失去覆盖 → 新增 15 条 Error；补回类级 `@extend_schema` 后复原

## 3. 验证

- [x] 3.1 `python manage.py spectacular --file temps/schema_final.yaml --validate` → **退出码 0 且 stderr/stdout 全空**（0 warnings / 0 errors；对照修复前 `Warnings: 5 / Errors: 0`、更早 `Warnings: 96+59`）。schema 151 KB，含 `securitySchemes.jwtAuth`
- [x] 3.2 `python manage.py check` → **0 issues**；生产档位 `DJANGO_DEBUG=False python manage.py check --deploy` 中 `drf_spectacular` 告警 **0 条**（修复前 155 条）
- [x] 3.3 `python -m pytest -m "unit or integration"` → **1 failed, 96 passed, 46 deselected**（唯一失败为既有 `test_case_manager_ids::test_next_case_id_increments_same_day`，与本变更无关）
- [x] 3.4 `python -m ruff check`（15 个涉及文件）→ **All checks passed**；`ruff format --check` → **15 files already formatted**；`python tools/gen_arch_stats.py --check-boundaries` → **零违规**
- [x] 3.5 `openspec validate complete-openapi-schema --strict` → **Change is valid**

## 4. 父 Agent 的独立抽查（不只依赖子 Agent 自述）

- 行为风险最高的两处：`case_manager` 4 个 ViewSet 与 `workflow` 的 `WorkflowPrototypeViewSet` 均新增 `queryset = Model.objects.none()` 以让 drf-spectacular 推导路径参数类型 —— 已核实它们都是**纯 `viewsets.ViewSet`**（非 `GenericViewSet`/`ModelViewSet`），`list`/`create`/`retrieve`/`partial_update`/`destroy` 全部自己实现，**没有 `get_queryset`/`get_object`** → 该属性运行时不参与任何逻辑，导入期不查库，无行为回归。
- 逐组 `git diff -U0` 核对删除行：只有被改写的方法签名、docstring（属 ① 单）与 ruff 折行，**无逻辑行被删**。
- `drf_spectacular.types.OpenApiTypes` 无 `ARRAY` 成员（实测）；已据此纠正 `dashboard/views.py` 的误用（改 `ANY`）。

## 5. 已知副作用与范围外事项

- **格式化副作用 2 处**（保留，否则 `ruff format --check` 失败）：`element_locator/views_projects_drf.py` 一条 103 字符既有调用被折行；`ai_assistant/views_toolbox_drf.py` 一条既有三行表达式折成一行。均无语义变化。
- **跨会话混杂（已确认不是我方改动）**：`apps/dashboard/views.py` 的 `git diff` 还包含另一个会话的 `dashboard-ai-agent-tasks` 变更（`ai_usage` 系列的 `ai_recent_tasks`/`ai_task_daily_execution`/`ai_task_execution_summary` 等增删），开始前即在工作区；本单在该文件只加了 1 行 import + 4 个类级 `@extend_schema`，未触碰其余内容。
- 新增 `shared/apps.py` 仅用于扩展注册（`ready()`），无行为影响；`shared` 仍在 `INSTALLED_APPS` 中按原样工作。
- 前端未消费 `/api/schema`（grep 零命中），本次只让描述更准确。
